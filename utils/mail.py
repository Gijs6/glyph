import logging
import os
from email.mime.text import MIMEText
from smtplib import SMTP_SSL as SMTP

logger = logging.getLogger("mail")


def _send(recipient_email, subject, content):
    server = os.getenv("SMTP_SERVER")
    sender = os.getenv("SMTP_SENDER")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")

    if not server or not sender:
        logger.warning("SMTP not configured, skipping email to %s", recipient_email)
        return False

    try:
        msg = MIMEText(content, "plain")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient_email

        conn = SMTP(server)
        conn.set_debuglevel(False)
        conn.login(username, password)
        try:
            conn.sendmail(sender, [recipient_email], msg.as_string())
        finally:
            conn.quit()

        logger.info("Email sent to %s: %s", recipient_email, subject)
        return True

    except Exception:
        logger.exception("Failed to send email to %s", recipient_email)
        return False


def send_reset_mail(reset_url, email):
    content = f"""\
Hey!

You can set (or reset) your password via the following link: {reset_url}
This link is valid for 1 hour.

If you weren't expecting this, you can safely ignore this email.

Cheers,
Glyph
"""
    return _send(email, "Set your password - Glyph", content)
