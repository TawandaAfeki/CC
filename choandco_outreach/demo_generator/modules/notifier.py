"""Sends a completion email after a demo portal is successfully generated."""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

from demo_generator.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    FROM_EMAIL, NOTIFY_EMAIL,
)

log = logging.getLogger(__name__)


def _build_email(
    industry_label: str,
    custom_url: str,
    netlify_url: str,
    dashboard_url: str,
    pdf_url: str,
    github_url: str,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Cho&Co Demo Ready] {industry_label} Portal Live"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = NOTIFY_EMAIL

    today = date.today().strftime("%d %B %Y").lstrip("0")

    plain = f"""
Cho&Co Demo Generator — {today}

A new industry demo portal has been successfully created!

Industry     : {industry_label}
Live Portal  : {custom_url}
Netlify URL  : {netlify_url}
Dashboard    : {dashboard_url}
Report PDF   : {pdf_url}
GitHub File  : {github_url}

The portal is now live and ready to share with prospects.
— Cho&Co Automation
""".strip()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="font-family:'DM Sans',Arial,sans-serif;background:#f7f6f3;margin:0;padding:32px">
<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #eceae4">
  <div style="background:#3D4756;padding:20px 28px;border-bottom:3px solid #2A9D8F">
    <h2 style="margin:0;color:#fff;font-size:18px;font-weight:400">Cho<span style="color:#2A9D8F">&amp;</span>Co Demo Generator</h2>
    <p style="margin:4px 0 0;font-size:11px;color:rgba(255,255,255,.4);letter-spacing:.1em;text-transform:uppercase">{today}</p>
  </div>
  <div style="padding:28px">
    <div style="background:#e6f5f3;border-left:3px solid #2A9D8F;border-radius:4px;padding:14px 18px;margin-bottom:22px">
      <p style="margin:0;font-size:13px;color:#1e7268;font-weight:500">&#10003; New industry demo portal is live!</p>
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:12px">
      <tr><td style="padding:8px 0;color:#718096;border-bottom:1px solid #eceae4;width:130px">Industry</td>
          <td style="padding:8px 0;color:#2b3340;border-bottom:1px solid #eceae4;font-weight:500">{industry_label}</td></tr>
      <tr><td style="padding:8px 0;color:#718096;border-bottom:1px solid #eceae4">Live Portal</td>
          <td style="padding:8px 0;border-bottom:1px solid #eceae4"><a href="{custom_url}" style="color:#2A9D8F;text-decoration:none">{custom_url}</a></td></tr>
      <tr><td style="padding:8px 0;color:#718096;border-bottom:1px solid #eceae4">Netlify URL</td>
          <td style="padding:8px 0;border-bottom:1px solid #eceae4"><a href="{netlify_url}" style="color:#2A9D8F;text-decoration:none">{netlify_url}</a></td></tr>
      <tr><td style="padding:8px 0;color:#718096;border-bottom:1px solid #eceae4">Dashboard</td>
          <td style="padding:8px 0;border-bottom:1px solid #eceae4"><a href="{dashboard_url}" style="color:#2A9D8F;text-decoration:none">Open Dashboard</a></td></tr>
      <tr><td style="padding:8px 0;color:#718096;border-bottom:1px solid #eceae4">Report PDF</td>
          <td style="padding:8px 0;border-bottom:1px solid #eceae4"><a href="{pdf_url}" style="color:#2A9D8F;text-decoration:none">View Report</a></td></tr>
      <tr><td style="padding:8px 0;color:#718096">GitHub</td>
          <td style="padding:8px 0"><a href="{github_url}" style="color:#2A9D8F;text-decoration:none">View File</a></td></tr>
    </table>
    <p style="margin:22px 0 0;font-size:11px;color:#718096">
      The portal is ready to share with {industry_label} prospects.<br>
      Share <strong>{custom_url}</strong> in your next follow-up email.
    </p>
  </div>
  <div style="background:#f0f1f3;padding:14px 28px;font-size:10px;color:#718096;letter-spacing:.05em;text-transform:uppercase">
    Cho&amp;Co Automation &nbsp;&middot;&nbsp; choandco.co.za
  </div>
</div>
</body></html>"""

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
    return msg


def send_notification(
    industry_label: str,
    custom_url: str,
    netlify_url: str,
    dashboard_url: str,
    pdf_url: str,
    github_url: str,
):
    """Send the completion notification email via existing Cho&Co SMTP."""
    msg = _build_email(industry_label, custom_url, netlify_url, dashboard_url, pdf_url, github_url)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE   # matches existing outreach agent pattern for GoDaddy

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, NOTIFY_EMAIL, msg.as_string())
        log.info(f"Completion notification sent to {NOTIFY_EMAIL} for '{industry_label}'.")
    except Exception as e:
        log.error(f"Failed to send notification email: {e}")
        # Non-fatal: portal is live even if notification fails
