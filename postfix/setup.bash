#!/usr/bin/env bash

USER=tiger
FQDN=communalgrowth.org

DEBIAN_FRONTEND=noninteractive apt install -y \
  postfix opendkim opendkim-tools postfix-policyd-spf-python

if ! id "$USER" 2> /dev/null; then
    groupadd -g 1984 "$USER" && \
    useradd -m -g "$USER" -s /bin/bash -u 1984 "$USER"
fi

user_id=$(id -u "$USER")

mkdir -p "/var/mail/vhosts/${FQDN}"
mkdir /var/spool/postfix/opendkim
chown postfix:postfix /var/mail/vhosts
chown "${USER}:${USER}" "/var/mail/vhosts/${FQDN}"
chown opendkim:opendkim /var/spool/postfix/opendkim

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

smtpd_sender_restrictions = reject_non_fqdn_sender, reject_unknown_sender_domain
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
Canonicalization        relaxed/simple
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

printf "postmaster:\tadmin@%s\n" "$FQDN" > /etc/aliases

service opendkim restart
postalias /etc/aliases
postmap /etc/postfix/vmailbox
postfix start >&/dev/null || postfix reload
