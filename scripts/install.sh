#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root: sudo bash scripts/install.sh"
  exit 1
fi

read -rp "Domain, for example example.com: " DOMAIN
read -rp "Mail hostname [mail.${DOMAIN}]: " MAIL_HOSTNAME
MAIL_HOSTNAME="${MAIL_HOSTNAME:-mail.${DOMAIN}}"
read -rp "Telegram Bot Token: " BOT_TOKEN
read -rp "Telegram Chat ID: " CHAT_ID

if [[ -z "${DOMAIN}" || -z "${MAIL_HOSTNAME}" || -z "${BOT_TOKEN}" || -z "${CHAT_ID}" ]]; then
  echo "Domain, mail hostname, Bot Token, and Chat ID are required."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
printf 'postfix postfix/mailname string %s\npostfix postfix/main_mailer_type string Internet Site\n' "${MAIL_HOSTNAME}" | debconf-set-selections
apt-get install -y postfix python3 ca-certificates ufw swaks

install -m 0755 scripts/mail-to-tg.py /usr/local/bin/mail-to-tg.py
touch /var/log/mail-to-tg.log
chmod 666 /var/log/mail-to-tg.log

id tgmail >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin tgmail

cat > /etc/mail-tg.env <<EOF
BOT_TOKEN=${BOT_TOKEN}
CHAT_ID=${CHAT_ID}
EOF
chown root:tgmail /etc/mail-tg.env
chmod 640 /etc/mail-tg.env

hostnamectl set-hostname "${MAIL_HOSTNAME}" || true
printf '%s\n' "${MAIL_HOSTNAME}" > /etc/mailname

postconf -e "myhostname = ${MAIL_HOSTNAME}"
postconf -e "myorigin = /etc/mailname"
postconf -e 'mydestination = $myhostname, localhost'
postconf -e 'inet_interfaces = all'
postconf -e 'inet_protocols = ipv4'
postconf -e "virtual_alias_domains = ${DOMAIN}"
postconf -e 'virtual_alias_maps = hash:/etc/postfix/virtual'
postconf -e 'smtpd_recipient_restrictions = permit_mynetworks, reject_unauth_destination'
postconf -e 'disable_vrfy_command = yes'
postconf -e 'default_privs = tgmail'

cat > /etc/postfix/virtual <<EOF
@${DOMAIN} tgnotify
EOF
postmap /etc/postfix/virtual

cat > /etc/aliases <<'EOF'
postmaster: root
root: root
tgnotify: "|/usr/local/bin/mail-to-tg.py"
EOF
newaliases

ufw allow OpenSSH
ufw allow 25/tcp
ufw --force enable

systemctl restart postfix
postfix check

echo
echo "Installed."
echo
echo "Add these DNS records:"
echo "A     mail      YOUR_VPS_IP"
echo "MX    @         ${MAIL_HOSTNAME}    priority 10"
echo "TXT   @         \"v=spf1 mx -all\""
echo "TXT   _dmarc    \"v=DMARC1; p=none\""
echo
echo "Local test:"
echo "swaks --to test@${DOMAIN} --from localtest@example.net --server 127.0.0.1 --data 'Subject: local test"
echo
echo "Hello from Postfix.'"
