#!/usr/bin/env bash

USER=tiger
FQDN=communalgrowth.org

user_id=$(id -u ${USER})

mkdir -p /var/mail/vhosts
chown postfix:postfix /var/mail/vhosts

mkdir -p "/var/mail/vhosts/${FQDN}"
chown "${USER}:${USER}" "/var/mail/vhosts/${FQDN}"

# Set up virtual Maildirs.
for u in admin forget subscribe support unsubscribe; do
  printf "%s@%s\t\t%s/%s/\n" "$u" "$FQDN" "$FQDN" "$u" >> /etc/postfix/vmailbox
done

xargs -a - postconf <<< "
smtpd_relay_restrictions=permit_mynetworks,reject_unauth_destination
alias_maps=
message_size_limit=512000
virtual_mailbox_domains=${FQDN}
virtual_mailbox_base=/var/mail/vhosts
virtual_mailbox_maps=hash:/etc/postfix/vmailbox
virtual_minimum_uid=100
virtual_uid_maps=static:${user_id}
virtual_gid_maps=static:${user_id}
"

postmap /etc/postfix/vmailbox
postfix start >&/dev/null || postfix reload


