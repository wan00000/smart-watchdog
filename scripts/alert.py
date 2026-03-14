#!/usr/bin/env python3
from __future__ import annotations

import os
import smtplib
import sys
from email.message import EmailMessage


def send_email(subject: str, body: str) -> bool:
    host = os.getenv('SMTP_HOST', 'localhost').strip()
    port = int(os.getenv('SMTP_PORT', '25').strip())
    sender = os.getenv('ALERT_EMAIL_FROM', 'a9ufplup@gmail.com').strip()
    recipient = os.getenv('ALERT_EMAIL_TO', 'izwanhusainy02@gmail.com').strip()

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.send_message(msg)
    return True


def main() -> int:
    if len(sys.argv) < 3:
        print('Usage: alert.py <subject> <message>', file=sys.stderr)
        return 2

    subject = sys.argv[1]
    body = sys.argv[2]

    if os.getenv('EMAIL_ALERTS_ENABLED', '0') != '1':
        print(f'[ALERT DISABLED] {subject}\n{body}')
        return 0

    try:
        send_email(subject, body)
        print(f'[ALERT SENT] {subject}')
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f'[ALERT FALLBACK] {subject}\n{body}\nSMTP error: {exc}')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
