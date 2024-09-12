#!/usr/bin/env bash

USER=tiger
FQDN=communalgrowth.org

printf "postfix postfix/main_mailer_type string 'Internet Site'\n" \
    | debconf-set-selections
DEBIAN_FRONTEND=noninteractive apt install -y \
  postfix opendkim opendkim-tools postfix-policyd-spf-python postfwd
adduser postfix opendkim

if ! id "$USER" 2> /dev/null; then
    groupadd -g 1984 "$USER" && \
    useradd -m -g "$USER" -s /bin/bash -u 1984 "$USER"
fi

if ! id postfwd 2> /dev/null; then
    groupadd postfwd
    useradd -g postfwd -M -s /sbin/nologin -c "postfwd daemon user" postfwd
    passwd -l postfwd
fi

user_id=$(id -u "$USER")
mkdir -p "/var/mail/vhosts/${FQDN}"
mkdir /var/spool/postfix/opendkim
chown postfix:postfix /var/mail/vhosts
chown "${USER}:${USER}" "/var/mail/vhosts/${FQDN}"
chown opendkim:opendkim /var/spool/postfix/opendkim
chown postfwd:postfwd /var/spool/postfix/postfwd

# Set up virtual Maildirs.
mv /etc/postfix/vmailbox /etc/postfix/vmailbox.old
for u in admin forget subscribe support unsubscribe; do
  printf "%s@%s\t\t%s/%s/\n" "$u" "$FQDN" "$FQDN" "$u" >> /etc/postfix/vmailbox
done

(sed -e '/^$/d' | xargs -d '\n' postconf) <<< "
mail_name = Postfix
smtpd_banner = \$myhostname ESMTP \$mail_name
myhostname = mail.${FQDN}

policy-spf_time_limit = 3600s

milter_default_action = reject
milter_protocol = 6

smtpd_milters = unix:opendkim/opendkim.sock
non_smtpd_milters = unix:opendkim/opendkim.sock

smtpd_tls_security_level=encrypt
smtpd_sender_restrictions = reject_non_fqdn_sender, reject_unknown_sender_domain, check_policy_service unix:postfwd/postfwd.sock
smtpd_relay_restrictions = permit_mynetworks, reject_unauth_destination
smtpd_recipient_restrictions = permit_mynetworks, reject_unauth_destination, check_policy_service unix:private/policy-spf
disable_vrfy_command = yes
message_size_limit = 512000

virtual_mailbox_domains=${FQDN}
virtual_mailbox_base=/var/mail/vhosts
virtual_mailbox_maps=hash:/etc/postfix/vmailbox
virtual_minimum_uid=100
virtual_uid_maps=static:${user_id}
virtual_gid_maps=static:${user_id}
"

cat > /etc/opendkim.conf <<< "
Syslog                  yes
SyslogSuccess           yes
Canonicalization        relaxed/relaxed
Mode                    v
UserID                  opendkim
UMask                   007
Socket                  local:/var/spool/postfix/opendkim/opendkim.sock
TrustAnchorFile         /usr/share/dns/root.key
On-BadSignature         reject
On-NoSignature          reject
On-SignatureError       reject
On-KeyNotFound          reject
"

cat >> /etc/postfix/master.cf <<< "
policy-spf  unix  -       n       n       -       -       spawn
     user=nobody argv=/usr/bin/policyd-spf
"

cat > /etc/postfwd.cf <<< "
# Postfwd rules to prevent people from flooding with messages. We
# rate-limit to 100 e-mails a day for gmail et al users, and 100
# e-mail a day totally for a domain that is not a popular mail server
# like gmail.

# Every time a 'user@domain' sends an e-mail, a counter for 'user' is
# increased. When it reaches 100, it triggers the rejection
# action. The counter is reset every day.
id=RULE-popularmailservers
    sender_domain=~(gmail\.com|proton\.me|yahoo\.com|icloud\.com)
    action=rate(sender/100/86400/421 4.7.1 - Server overload, more than 100 messages in a day from your account, try again tomorrow.)

# Every time an e-mail is received from a domain, a counter for the
# domain is increased. When it reaches 100, it triggers rejection.
id=RULE-customdomains
    sender_domain!~(gmail\.com|proton\.me|yahoo\.com|icloud\.com)
    action=rate(sender_domain/100/86400/421 4.7.1 - Server overload, more than 100 messages in a day from your domain, try again tomorrow.)
"

printf "postmaster:\tadmin@%s\n" "$FQDN" > /etc/aliases

postfwd --file /etc/postfwd.cf \
        --daemon \
        --user postfwd \
        --group postfwd \
        --proto unix \
        --port /var/spool/postfix/postfwd/postfwd.sock
service opendkim restart
postalias /etc/aliases
postmap /etc/postfix/vmailbox
postfix start >&/dev/null || postfix reload
