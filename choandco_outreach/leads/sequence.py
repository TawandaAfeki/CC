"""
leads/sequence.py

Manages follow-up email scheduling for the Cho&Co outreach sequence.
Reads the dedup store to find leads due for follow-up emails and sends them.
"""
import logging
import time
import random
from datetime import datetime

from leads.dedup import get_leads_due_for_followup, mark_followup_sent
from leads.verifier import verify_email
from leads.suppression import is_suppressed, add_suppressed
from email_engine.composer import compose_followup_email
from email_engine.sender import send_with_retry

logger = logging.getLogger(__name__)

# Follow-up windows in days (inclusive range)
FOLLOWUP_WINDOWS = {
    "followup1": (3, 4),
    "followup2": (7, 8),
    "followup3": (14, 16),
}


def _extract_first_name(full_name: str) -> str:
    """Extract first name from a full name. Falls back to 'there'."""
    if not full_name or not full_name.strip():
        return "there"
    return full_name.strip().split()[0].capitalize()


def get_pending_followups(stage: str) -> list:
    """Return store entries due for a given follow-up stage."""
    if stage not in FOLLOWUP_WINDOWS:
        raise ValueError(f"Unknown stage: {stage}")
    min_days, max_days = FOLLOWUP_WINDOWS[stage]
    return get_leads_due_for_followup(stage, min_days, max_days)


def run_followup_stage(stage: str, max_emails: int = 20) -> int:
    """
    Find all leads due for `stage`, compose and send follow-up emails.
    Returns number of follow-up emails successfully sent.
    """
    from config import EMAIL_DELAY_RANGE

    pending = get_pending_followups(stage)
    logger.info("Stage %s: %d leads due for follow-up", stage, len(pending))

    if not pending:
        return 0

    sent_count = 0
    for i, entry in enumerate(pending[:max_emails], 1):
        email = entry.get("email", "")
        company = entry.get("company", "")
        dm_name = entry.get("decision_maker_name", "")
        industry = entry.get("industry", "")
        original_subject = entry.get("original_subject", "")

        if not email:
            continue

        # Guard 1: check suppression list
        if is_suppressed(email):
            logger.info("Skipping suppressed follow-up: %s (%s)", email, company)
            continue

        # Guard 2: re-verify the email domain is still reachable
        if not verify_email(email):
            logger.warning("Follow-up email failed re-verification, auto-suppressing: %s", email)
            add_suppressed(email)
            continue

        first_name = _extract_first_name(dm_name)

        subject, body = compose_followup_email(
            stage=stage,
            first_name=first_name,
            company_name=company,
            industry=industry,
            original_subject=original_subject,
        )

        logger.info("[%s %d/%d] Sending follow-up to %s (%s)...", stage, i, len(pending[:max_emails]), company, email)
        success = send_with_retry(email, subject, body)

        if success:
            mark_followup_sent(company, email, stage)
            # Log to Excel
            try:
                from tracking.logger import log_followup
                log_followup(email, company, dm_name, industry, stage, datetime.now())
            except Exception as e:
                logger.warning("Could not log follow-up to Excel: %s", e)
            sent_count += 1
            logger.info("Follow-up %s sent to %s (%s)", stage, email, company)
        else:
            logger.warning("Failed follow-up %s to %s", stage, email)

        # Delay between follow-up emails
        if i < len(pending[:max_emails]):
            delay = random.uniform(*EMAIL_DELAY_RANGE)
            logger.info("Waiting %.0f seconds before next follow-up...", delay)
            time.sleep(delay)

    return sent_count
