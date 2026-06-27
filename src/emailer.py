"""Gmail SMTP sender with safe test mode. Never logs credentials."""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

log = logging.getLogger("emailer")
PREVIEW_DIR = Path(__file__).resolve().parent.parent / "output" / "previews"


def _enabled() -> bool:
    return os.getenv("EMAIL_SEND_ENABLED", "false").strip().lower() == "true"


def send(subject: str, html_body: str, report_id: str = "report") -> dict:
    """Send via Gmail SMTP if EMAIL_SEND_ENABLED=true, else write preview file."""
    recipient = os.getenv("EMAIL_RECIPIENT", "hmehta4851@gmail.com")
    result = {"report_id": report_id, "recipient": recipient, "sent": False,
              "preview": "", "ts": datetime.now(timezone.utc).isoformat()}

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    preview_path = PREVIEW_DIR / f"{report_id}.html"
    preview_path.write_text(html_body, encoding="utf-8")
    result["preview"] = str(preview_path)

    if not _enabled():
        log.info("EMAIL_SEND_ENABLED=false -> preview only: %s", preview_path)
        return result

    user = os.environ["SMTP_USERNAME"]
    pwd = os.environ["SMTP_APP_PASSWORD"]
    sender = os.getenv("SMTP_FROM", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as srv:
        srv.login(user, pwd)
        srv.sendmail(sender, [recipient], msg.as_string())
    result["sent"] = True
    log.info("email sent: id=%s to=%s", report_id, recipient)  # no credentials logged
    return result
