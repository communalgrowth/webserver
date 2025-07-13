#!/usr/bin/env bash
#
# IMPORTANT: Don't forget to generate a self-signed x509 certificate
# with openssl at /etc/postfix/{cert,key}-mailserver.pem, and also
# chown the files to postfix.

USER=gauss
FQDN=communalgrowth.org
MAILSERVER="mail.${FQDN}"

printf "postfix postfix/main_mailer_type string 'Internet Site'\n" \
    | debconf-set-selections
printf "opendmarc opendmarc/dbconfig-install boolean false\n" \
    | debconf-set-selections
DEBIAN_FRONTEND=noninteractive apt install -y \
  postfix opendkim opendkim-tools \
  opendmarc postfix-policyd-spf-python postfwd

if ! id "$USER" 2> /dev/null; then
    groupadd -g 1984 "$USER" && \
    useradd -m -g "$USER" -s /bin/bash -u 1984 "$USER"
fi

if ! id postfwd 2> /dev/null; then
    groupadd postfwd
    useradd -g postfwd -M -s /sbin/nologin -c "postfwd daemon user" postfwd
    passwd -l postfwd
fi

usermod -a -G "opendkim,opendmarc,postfwd,${USER}" postfix
mkdir -p -m755 /var/mail/vhosts
chown postfix:postfix /var/mail/vhosts
mkdir -p -m770 "/var/mail/vhosts/${FQDN}"
chown "${USER}:${USER}" "/var/mail/vhosts/${FQDN}"
for x in opendkim opendmarc postfwd; do
    mkdir -p -m750 "/var/spool/postfix/${x}"
    chown "${x}:${x}" "/var/spool/postfix/${x}"
done

# Set up virtual Maildirs.
mv /etc/postfix/vmailbox /etc/postfix/vmailbox.old
for u in admin forget subscribe support unsubscribe; do
  printf "%s@%s\t\t%s/%s/\n" "$u" "$FQDN" "$FQDN" "$u" >> /etc/postfix/vmailbox
done

user_id=$(id -u "$USER")
(sed -e '/^$/d' | xargs -d '\n' postconf) <<< "
mail_name = Postfix
smtpd_banner = \$myhostname ESMTP \$mail_name
myhostname = ${MAILSERVER}

enable_long_queue_ids = yes
smtpd_client_port_logging = yes

biff = no

policy-spf_time_limit = 3600s

milter_default_action = reject
milter_protocol = 6

smtpd_milters = unix:opendkim/opendkim.sock,local:opendmarc/opendmarc.sock
non_smtpd_milters = \$smtpd_milters

smtpd_helo_restrictions = reject_unauth_pipelining, reject_non_fqdn_hostname
mynetworks =
smtpd_tls_security_level = encrypt
smtpd_tls_cert_file = /etc/postfix/cert-mailserver.pem
smtpd_tls_key_file = /etc/postfix/key-mailserver.pem
smtpd_sender_restrictions = reject_non_fqdn_sender, reject_unknown_sender_domain, check_policy_service unix:private/policy-spf, check_policy_service unix:postfwd/postfwd.sock
smtpd_relay_restrictions = permit_mynetworks, reject_unauth_destination
smtpd_recipient_restrictions = permit_mynetworks, reject_unauth_destination
smtpd_helo_required = yes
smtpd_etrn_restrictions = reject
strict_rfc821_envelopes = yes
parent_domain_matches_subdomains =
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

cat > /etc/opendmarc.conf <<< "
AuthservID OpenDMARC
IgnoreAuthenticatedClients false
PidFile /run/opendmarc/opendmarc.pid
PublicSuffixList /usr/share/publicsuffix/public_suffix_list.dat
RejectFailures true
RequiredHeaders true
SPFSelfValidate true
Socket local:/var/spool/postfix/opendmarc/opendmarc.sock
Syslog true
TrustedAuthservIDs ${MAILSERVER}
UMask 0002
UserID opendmarc
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
systemctl restart opendkim
systemctl restart opendmarc
postalias /etc/aliases
postmap /etc/postfix/vmailbox
postfix start >&/dev/null || postfix reload
