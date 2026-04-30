#!/usr/bin/env python3
import html
import re
import sys
import urllib.parse
import urllib.request
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser

ENV_PATH = "/etc/mail-tg.env"
LOG_PATH = "/var/log/mail-to-tg.log"


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "head", "title", "meta"}:
            self.skip_depth += 1
        if tag in {"br", "p", "div", "tr", "table", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "head", "title", "meta"} and self.skip_depth:
            self.skip_depth -= 1
        if tag in {"p", "div", "tr", "table", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data)

    def text(self):
        text = html.unescape(" ".join(self.parts))
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def log(message):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(message + "\n")
    except Exception:
        pass


def load_env(path):
    data = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def first_header(msg, name):
    value = msg.get(name, "")
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def body_text(msg):
    if msg.is_multipart():
        html_part = ""
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            try:
                content = part.get_content()
            except Exception:
                continue
            if ctype == "text/plain" and str(content).strip():
                return str(content).strip()
            if ctype == "text/html" and str(content).strip() and not html_part:
                html_part = str(content)
        if html_part:
            return html_to_text(html_part)
        return ""
    try:
        content = msg.get_content()
    except Exception:
        return ""
    if msg.get_content_type() == "text/html":
        return html_to_text(str(content))
    return str(content).strip()


def html_to_text(value):
    parser = VisibleTextParser()
    parser.feed(value)
    parser.close()
    text = parser.text()
    return text or re.sub(r"<[^>]+>", " ", html.unescape(value)).strip()


def code_hint(text):
    patterns = [
        r"(?:验证码|verification code|code)[^\dA-Z]{0,40}([A-Z0-9]{4,10})",
        r"\b([0-9]{6,8})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def attachment_names(msg):
    names = []
    for part in msg.walk() if msg.is_multipart() else []:
        if part.get_content_disposition() == "attachment":
            names.append(part.get_filename() or "unnamed")
    return names


def tg_send(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text[:3900],
        "disable_web_page_preview": "true",
    }).encode()
    with urllib.request.urlopen(url, payload, timeout=15) as resp:
        resp.read()


def main():
    raw = sys.stdin.buffer.read()
    msg = BytesParser(policy=policy.default).parsebytes(raw)
    env = load_env(ENV_PATH)
    token = env.get("BOT_TOKEN", "")
    chat_id = env.get("CHAT_ID", "")
    if not token or not chat_id:
        log("missing BOT_TOKEN or CHAT_ID")
        return 75

    sender = first_header(msg, "From")
    to = first_header(msg, "To")
    subject = first_header(msg, "Subject")
    date = first_header(msg, "Date")
    body = body_text(msg)
    code = code_hint(body)
    if code:
        body = f"Code: {code}\n\n{body}"
    if len(body) > 2600:
        body = body[:2600] + "\n\n...[truncated]"
    attachments = attachment_names(msg)
    attach_line = ""
    if attachments:
        attach_line = "\nAttachments: " + ", ".join(attachments[:8])

    text = (
        "New mail\n\n"
        f"From: {sender}\n"
        f"To: {to}\n"
        f"Subject: {subject}\n"
        f"Date: {date}"
        f"{attach_line}\n\n"
        f"{body}"
    )
    try:
        tg_send(token, chat_id, text)
    except Exception as exc:
        log(f"send failed: {exc}")
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
