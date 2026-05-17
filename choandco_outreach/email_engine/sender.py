import logging
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, formataddr, make_msgid
from pathlib import Path

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SENDER_EMAIL
from email_engine.signature import SIGNATURE_HTML

logger = logging.getLogger(__name__)


def _get_ssl_context():
    """Create SSL context for GoDaddy secureserver.net."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _smtp_connect(context):
    """Connect via STARTTLS on port 587."""
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(SMTP_USER, SMTP_PASSWORD)
    return server


def _body_to_html(body: str) -> str:
    """Convert plain-text email body to HTML with signature appended."""
    # Convert line breaks to HTML and wrap in styled container
    body_html = body.replace("\n", "<br/>\n")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#1a1814;line-height:1.6;">
<div style="max-width:600px;padding:20px;">
{body_html}
<br/>
<p style="margin:0 0 2px;font-size:14px;color:#1a1814;">Warm regards,</p>
<p style="margin:0 0 16px;font-size:14px;font-weight:600;color:#1a1814;">Tawanda Afeki</p>
{SIGNATURE_HTML}
</div>
</body>
</html>"""


def _build_message(to_address: str, subject: str, body: str) -> MIMEMultipart:
    """Build an email with both plain-text and HTML versions."""
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("Tawanda Afeki", SENDER_EMAIL))
    msg["To"] = to_address
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="choandco.co.za")
    msg["Reply-To"] = SENDER_EMAIL
    msg["X-Mailer"] = "Microsoft Outlook 16.0"

    # Plain text fallback (for email clients that don't render HTML)
    plain_body = body + "\n\nWarm regards,\nTawanda Afeki\n\nCho&Co. | Data & Business Intelligence\nE info@choandco.co.za\nT +27 71 060 2976\nW www.choandco.co.za"
    msg.attach(MIMEText(plain_body, "plain", "utf-8"))

    # HTML version with full branded signature
    html_body = _body_to_html(body)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg


def send_email(to_address: str, subject: str, body: str) -> bool:
    """Send an HTML email with branded signature via SMTP STARTTLS."""
    try:
        msg = _build_message(to_address, subject, body)
        context = _get_ssl_context()

        with _smtp_connect(context) as server:
            server.sendmail(SENDER_EMAIL, to_address, msg.as_string())

        logger.info("Email sent to %s: %s", to_address, subject)
        return True

    except smtplib.SMTPAuthenticationError:
        logger.critical("SMTP authentication failed. Check your .env credentials.")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.warning("Recipient refused: %s - %s", to_address, e)
        return False
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_address, e)
        return False


def send_with_retry(to_address: str, subject: str, body: str, retries: int = 3) -> bool:
    """Retry sending with exponential backoff on transient errors."""
    for attempt in range(retries):
        if send_email(to_address, subject, body):
            return True
        if attempt < retries - 1:
            wait = (2 ** attempt) * 5
            logger.info("Retrying in %ds (attempt %d/%d)", wait, attempt + 2, retries)
            time.sleep(wait)
    return False


def send_email_with_attachment(to_address: str, subject: str, body: str, attachment_path: Path) -> bool:
    """Send an email with a file attachment."""
    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = formataddr(("Tawanda Afeki", SENDER_EMAIL))
        msg["To"] = to_address
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="choandco.co.za")
        msg["Reply-To"] = SENDER_EMAIL
        msg["X-Mailer"] = "Microsoft Outlook 16.0"

        # Email body (plain text for attachment emails)
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={attachment_path.name}",
        )
        msg.attach(part)

        context = _get_ssl_context()
        with _smtp_connect(context) as server:
            server.sendmail(SENDER_EMAIL, to_address, msg.as_string())

        logger.info("Email with attachment sent to %s", to_address)
        return True

    except Exception as e:
        logger.error("Failed to send email with attachment to %s: %s", to_address, e)
        return False
