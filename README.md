# Domain Mail to Telegram

Lightweight catch-all domain email receiver for a low-spec VPS.

It receives mail for any address at your domain, then sends a Telegram
notification with the sender, recipient, subject, date, body preview, and
attachment names.

Example:

```text
github@example.com
shop-2026@example.com
anything@example.com
```

All addresses are accepted and sent to the same Telegram chat.

## What This Is

- Postfix SMTP receiver
- Catch-all domain alias
- Python Telegram notification pipe
- No webmail
- No IMAP
- No database
- Suitable for very small VPS machines

## Requirements

- Debian or Ubuntu VPS
- Public IPv4 address
- Inbound TCP port 25 open
- Domain DNS access
- Telegram Bot Token
- Telegram Chat ID
- Root or sudo access on the VPS

## DNS Records

Replace `example.com` and `203.0.113.10` with your domain and VPS IP.

```dns
A     mail      203.0.113.10
MX    @         mail.example.com    priority 10
TXT   @         "v=spf1 mx -all"
TXT   _dmarc    "v=DMARC1; p=none"
```

If you use Cloudflare, the `mail` A record must be **DNS only**, not proxied.

## Install

SSH into your VPS and run:

```bash
curl -fsSL https://raw.githubusercontent.com/Arui08/domain-mail-to-telegram/main/scripts/install.sh -o install.sh
sudo bash install.sh
```

Or clone the repository:

```bash
git clone https://github.com/Arui08/domain-mail-to-telegram.git
cd domain-mail-to-telegram
sudo bash scripts/install.sh
```

The installer asks for:

```text
Domain: example.com
Mail hostname: mail.example.com
Telegram Bot Token: 123456:ABC...
Telegram Chat ID: 123456789
```

## Test

After DNS has propagated, send an email to any address at your domain:

```text
test@example.com
github@example.com
random-anything@example.com
```

You should receive a Telegram message.

For local VPS testing:

```bash
swaks --to test@example.com --from localtest@example.net --server 127.0.0.1 \
  --data 'Subject: local test

Hello from Postfix.'
```

## Useful Commands

Check Postfix:

```bash
systemctl status postfix --no-pager -l
ss -ltnp | grep ':25'
```

Check logs:

```bash
tail -f /var/log/mail.log
tail -f /var/log/mail-to-tg.log
```

Check queue:

```bash
mailq
```

Reconfigure catch-all manually:

```bash
sudo nano /etc/postfix/virtual
sudo postmap /etc/postfix/virtual
sudo systemctl restart postfix
```

## Security Notes

- Do not commit VPS passwords, Telegram tokens, or private keys.
- Rotate your Telegram Bot Token if it was exposed.
- Change your VPS root password after setup if it was shared in chat.
- This project is for receiving mail. Reliable outbound sending needs DKIM,
  PTR/rDNS, IP reputation, and more careful policy work.

## License

MIT
