# Troubleshooting

## External Mail Does Not Arrive

Check DNS:

```bash
dig MX example.com
dig A mail.example.com
```

The `mail.example.com` A record must point to your VPS IP.

Check that Postfix is listening:

```bash
ss -ltnp | grep ':25'
```

Check firewall:

```bash
ufw status numbered
```

## Local Test Works, External Test Does Not

Most likely causes:

- DNS has not propagated yet.
- The `mail` DNS record is proxied by Cloudflare.
- Your VPS provider blocks inbound port 25.
- The sender refuses to send to new or unusual domains.

## Telegram Notification Does Not Arrive

Check logs:

```bash
tail -n 100 /var/log/mail.log
tail -n 100 /var/log/mail-to-tg.log
```

Check the token file permissions:

```bash
ls -l /etc/mail-tg.env
```

Expected:

```text
-rw-r----- root tgmail /etc/mail-tg.env
```

## Queue Is Not Empty

Show queue:

```bash
mailq
```

Flush queue:

```bash
postqueue -f
```

Delete all queued mail only if you understand the impact:

```bash
postsuper -d ALL
```
