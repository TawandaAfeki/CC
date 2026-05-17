import re
import logging

from leads.models import Lead
from leads.suppression import is_suppressed

logger = logging.getLogger(__name__)

# Generic and impersonal email prefixes to reject
# info@, contact@, admin@ etc. do not reach decision-makers
GENERIC_PREFIXES = {
    # Automated / system addresses
    "noreply", "no-reply", "donotreply", "mailer-daemon",
    "postmaster", "abuse", "webmaster",
    # Generic business inboxes (not decision-makers)
    "info", "contact", "contactus", "enquiries", "hello",
    "admin", "support",
}

# Competitor keywords (data analytics companies are not prospects)
COMPETITOR_KEYWORDS = [
    "data analytics", "business intelligence", "bi consulting",
    "data science", "data engineering", "analytics consulting",
    "dashboard development", "data visualization",
]

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def qualify(leads: list) -> list:
    """Filter leads through qualification rules."""
    qualified = []
    for lead in leads:
        if not _has_valid_email(lead):
            logger.debug("Skipped %s: invalid email", lead.company_name)
            continue
        if is_suppressed(lead.email):
            logger.info("Skipped %s: suppressed address (%s)", lead.company_name, lead.email)
            continue
        if _is_generic_email(lead):
            logger.debug("Skipped %s: generic email (%s)", lead.company_name, lead.email)
            continue
        if _is_competitor(lead):
            logger.debug("Skipped %s: appears to be a competitor", lead.company_name)
            continue
        if _is_own_company(lead):
            logger.debug("Skipped %s: own company", lead.company_name)
            continue
        qualified.append(lead)

    logger.info("Qualified %d out of %d leads", len(qualified), len(leads))
    return qualified


def _has_valid_email(lead: Lead) -> bool:
    """Check that the email address is syntactically valid."""
    return bool(lead.email and EMAIL_PATTERN.match(lead.email.strip()))


def _is_generic_email(lead: Lead) -> bool:
    """Reject generic inboxes that don't reach decision-makers."""
    prefix = lead.email.split("@")[0].lower().strip()
    return prefix in GENERIC_PREFIXES


def _is_competitor(lead: Lead) -> bool:
    """Check if the lead appears to be a data analytics competitor."""
    text = f"{lead.company_name} {lead.industry} {lead.raw_snippet}".lower()
    return any(kw in text for kw in COMPETITOR_KEYWORDS)


def _is_own_company(lead: Lead) -> bool:
    """Do not email ourselves."""
    return "choandco" in lead.company_name.lower().replace(" ", "").replace("&", "")
