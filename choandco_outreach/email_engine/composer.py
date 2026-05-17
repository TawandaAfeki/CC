import logging

from leads.models import Lead
from email_engine.templates import SECTOR_TEMPLATES, FOLLOWUP_TEMPLATES, sanitize_emdashes

logger = logging.getLogger(__name__)

# Maps substrings of scraped industry strings to SECTOR_TEMPLATES keys.
# Evaluated in order -- more specific matches first.
SECTOR_MAP = [
    (["accounting", "bookkeeping", "chartered accountant", "auditing", "tax", "cpa"], "accounting"),
    (["recruitment", "staffing", "headhunting", "talent", "hr services", "placement"], "recruitment"),
    (["retail", "e-commerce", "ecommerce", "shop", "store", "fashion", "wholesale"], "retail"),
    (["property", "real estate", "estate agent", "letting", "realty", "proptech"], "property"),
    (["financial services", "fintech", "finance", "investment", "asset management",
      "insurance", "banking", "wealth", "portfolio"], "financial_services"),
]


def _resolve_sector(industry: str) -> str:
    """Map a raw industry string to a SECTOR_TEMPLATES key."""
    if not industry:
        return "generic"
    lowered = industry.lower().strip()
    for keywords, sector_key in SECTOR_MAP:
        if any(kw in lowered for kw in keywords):
            return sector_key
    return "generic"


def _extract_first_name(decision_maker_name: str) -> str:
    """
    Extract first name from decision_maker_name.
    Falls back to 'there' so the greeting becomes 'Hi there,' if unknown.
    """
    name = decision_maker_name.strip() if decision_maker_name else ""
    if not name:
        return "there"
    return name.split()[0].capitalize()


def compose_email(lead: Lead) -> tuple:
    """
    Compose an initial outreach email for a lead.
    Returns (subject, body).
    """
    sector = _resolve_sector(lead.industry)
    template = SECTOR_TEMPLATES[sector]
    first_name = _extract_first_name(lead.decision_maker_name)

    replacements = {
        "{first_name}":   first_name,
        "{company_name}": lead.company_name,
        "{industry}":     lead.industry if lead.industry else "your industry",
    }

    subject = template["subject"]
    body = template["body"]
    for placeholder, value in replacements.items():
        subject = subject.replace(placeholder, value)
        body = body.replace(placeholder, value)

    subject = sanitize_emdashes(subject)
    body = sanitize_emdashes(body)
    return subject, body


def compose_followup_email(
    stage: str,
    first_name: str,
    company_name: str,
    industry: str,
    original_subject: str,
) -> tuple:
    """
    Compose a follow-up email for the given stage.
    stage: 'followup1' | 'followup2' | 'followup3'
    Returns (subject, body).
    """
    template = FOLLOWUP_TEMPLATES[stage]

    replacements = {
        "{first_name}":       first_name if first_name else "there",
        "{company_name}":     company_name,
        "{industry}":         industry if industry else "your industry",
        "{original_subject}": original_subject if original_subject else "my previous note",
    }

    subject = template["subject"]
    body = template["body"]
    for placeholder, value in replacements.items():
        subject = subject.replace(placeholder, value)
        body = body.replace(placeholder, value)

    subject = sanitize_emdashes(subject)
    body = sanitize_emdashes(body)
    return subject, body
