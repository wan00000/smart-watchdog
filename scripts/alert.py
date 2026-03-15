#!/usr/bin/env python3
from __future__ import annotations

import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage


def build_html_body(subject: str, body: str) -> str:
    """Generate a modern, responsive HTML email template."""
    timestamp = datetime.now().strftime("%B %d, %Y at %H:%M:%S UTC")
    
    # Determine alert severity based on subject keywords
    is_critical = any(word in subject.upper() for word in ['ALERT', 'CRITICAL', 'FAIL', 'ERROR'])
    
    accent_color = '#ef4444' if is_critical else '#f59e0b'
    accent_bg = '#fef2f2' if is_critical else '#fffbeb'
    status_text = 'Critical Alert' if is_critical else 'Warning'
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>{subject}</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f4f4f5;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <!--[if mso]>
        <table role="presentation" align="center" border="0" cellpadding="0" cellspacing="0" width="600">
        <tr><td>
        <![endif]-->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:600px;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.05);">
          
          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);padding:32px 40px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td>
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                      <tr>
                        <td style="background-color:rgba(34,211,187,0.15);border-radius:10px;padding:10px;vertical-align:middle;">
                          <img src="https://img.icons8.com/fluency/48/shield.png" alt="" width="28" height="28" style="display:block;border:0;">
                        </td>
                        <td style="padding-left:14px;vertical-align:middle;">
                          <span style="color:#ffffff;font-size:20px;font-weight:600;letter-spacing:-0.025em;">Smart Infra Watchdog</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Alert Badge -->
          <tr>
            <td style="padding:28px 40px 0 40px;">
              <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                <tr>
                  <td style="background-color:{accent_bg};border-radius:20px;padding:6px 14px;">
                    <span style="color:{accent_color};font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">{status_text}</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Subject -->
          <tr>
            <td style="padding:16px 40px 0 40px;">
              <h1 style="margin:0;color:#0f172a;font-size:22px;font-weight:700;line-height:1.3;">{subject}</h1>
            </td>
          </tr>
          
          <!-- Timestamp -->
          <tr>
            <td style="padding:8px 40px 0 40px;">
              <p style="margin:0;color:#64748b;font-size:13px;">{timestamp}</p>
            </td>
          </tr>
          
          <!-- Divider -->
          <tr>
            <td style="padding:24px 40px;">
              <div style="height:1px;background-color:#e2e8f0;"></div>
            </td>
          </tr>
          
          <!-- Message Body -->
          <tr>
            <td style="padding:0 40px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f8fafc;border-radius:8px;border-left:4px solid {accent_color};">
                <tr>
                  <td style="padding:20px 24px;">
                    <p style="margin:0;color:#334155;font-size:15px;line-height:1.7;white-space:pre-wrap;">{body}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Action Hint -->
          <tr>
            <td style="padding:28px 40px 0 40px;">
              <p style="margin:0;color:#64748b;font-size:13px;line-height:1.6;">
                Please investigate this issue promptly. Check your monitoring dashboard for additional details and recent activity logs.
              </p>
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding:32px 40px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-top:1px solid #e2e8f0;padding-top:24px;">
                <tr>
                  <td>
                    <p style="margin:0 0 4px 0;color:#94a3b8;font-size:12px;">Smart Infra Watchdog</p>
                    <p style="margin:0;color:#cbd5e1;font-size:11px;">Infrastructure Monitoring &amp; Security</p>
                  </td>
                  <td align="right" style="vertical-align:top;">
                    <p style="margin:0;color:#cbd5e1;font-size:11px;">Automated Alert System</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
        </table>
        <!--[if mso]>
        </td></tr>
        </table>
        <![endif]-->
      </td>
    </tr>
  </table>
</body>
</html>'''


def send_email(subject: str, body: str) -> bool:
    host = os.getenv('SMTP_HOST', 'localhost').strip()
    port = int(os.getenv('SMTP_PORT', '25').strip())
    sender = os.getenv('ALERT_EMAIL_FROM', 'a9ufplup@gmail.com').strip()
    recipient = os.getenv('ALERT_EMAIL_TO', 'izwanhusainy02@gmail.com').strip()

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    
    # Set plain text as fallback
    msg.set_content(body)
    
    # Add HTML version as the preferred alternative
    html_body = build_html_body(subject, body)
    msg.add_alternative(html_body, subtype='html')

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
