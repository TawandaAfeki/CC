import logging
from datetime import datetime

from config import EXCEL_PATH, SUMMARY_RECIPIENT
from email_engine.sender import send_email_with_attachment

logger = logging.getLogger(__name__)


def send_daily_summary() -> bool:
    """Send the outreach log Excel file to the summary recipient."""
    if not EXCEL_PATH.exists():
        logger.warning("No outreach log found, skipping daily summary")
        return False

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"Cho&Co Outreach Log - {today}"

    body = (
        f"Hi Tawanda,\n\n"
        f"Please find attached the updated outreach log for {today}.\n\n"
        f"This file contains all leads contacted to date, including company name, "
        f"email address, phone number, industry, and the date and time each email was sent.\n\n"
    )

    success = send_email_with_attachment(
        to_address=SUMMARY_RECIPIENT,
        subject=subject,
        body=body,
        attachment_path=EXCEL_PATH,
    )

    if success:
        logger.info("Daily summary sent to %s", SUMMARY_RECIPIENT)
    else:
        logger.error("Failed to send daily summary")

    return success
