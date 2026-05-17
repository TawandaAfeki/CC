"""
Email templates for Cho&Co outreach.
All templates are emdash-free, under 120 words, warm and conversational.
"""
import re

# ---------------------------------------------------------------------------
# SECTOR TEMPLATES — initial outreach, one per priority sector
# Placeholders: {first_name}, {company_name}, {industry}
# ---------------------------------------------------------------------------

SECTOR_TEMPLATES = {
    "accounting": {
        "subject": "Quick question about {company_name} reporting",
        "body": (
            "Hi {first_name},\n\n"
            "Accounting firms helping SMEs scale usually hit the same wall -- your team "
            "spends hours compiling client reports from spreadsheets, and the output still "
            "leaves questions.\n\n"
            "I built a live dashboard demo for accounting firms that shows what real-time, "
            "client-facing reporting could look like. Takes 2 minutes to look at.\n\n"
            "Worth a glance?\n\n"
            "Tawanda\n"
        ),
    },
    "recruitment": {
        "subject": "{company_name}'s candidate data",
        "body": (
            "Hi {first_name},\n\n"
            "Recruitment firms generate massive amounts of data -- candidate pipelines, "
            "placement rates, time-to-fill -- but most of it lives in spreadsheets that "
            "nobody has time to analyse.\n\n"
            "I built a dashboard that turns recruitment data into live metrics your team "
            "can actually use for forecasting and client reporting. Happy to send a "
            "2-minute demo link.\n\n"
            "Interested?\n\n"
            "Tawanda\n"
        ),
    },
    "retail": {
        "subject": "Idea for {company_name}'s sales data",
        "body": (
            "Hi {first_name},\n\n"
            "Most mid-size retailers I've researched have all the sales data they need -- "
            "it's just scattered across POS systems, spreadsheets, and platforms that "
            "don't talk to each other.\n\n"
            "I help businesses like {company_name} turn that into one clean dashboard "
            "where you can see what's selling, what's not, and where the margin is -- "
            "in real time. Starts from R5,000.\n\n"
            "Open to a quick look?\n\n"
            "Tawanda\n"
        ),
    },
    "property": {
        "subject": "Data idea for {company_name}",
        "body": (
            "Hi {first_name},\n\n"
            "I recently built a dashboard for a property investment firm that analyses "
            "pricing trends, location performance, and optimal buying windows. It cut "
            "their property evaluation time by 30%.\n\n"
            "I think something similar could work for {company_name}. Happy to send a "
            "demo link -- takes 2 minutes.\n\n"
            "Worth a look?\n\n"
            "Tawanda\n"
        ),
    },
    "financial_services": {
        "subject": "Quick thought on {company_name}'s reporting",
        "body": (
            "Hi {first_name},\n\n"
            "Financial services firms generate some of the richest data in SA -- but "
            "turning regulatory reports and client portfolios into clear, actionable "
            "dashboards is usually a pain.\n\n"
            "I build real-time analytics dashboards that make compliance reporting and "
            "client visibility faster. Currently offering a free data health check for "
            "financial services firms.\n\n"
            "Interested?\n\n"
            "Tawanda\n"
        ),
    },
    "generic": {
        "subject": "{company_name}'s data",
        "body": (
            "Hi {first_name},\n\n"
            "I came across {company_name} and noticed you're growing fast. In my "
            "experience, that's usually when data starts becoming a bottleneck -- "
            "reports take longer, spreadsheets multiply, and decisions slow down.\n\n"
            "I help SA businesses turn scattered data into clean dashboards and reports. "
            "Starts from R5,000, delivered in 5-10 days.\n\n"
            "Would it be useful to see a quick demo?\n\n"
            "Tawanda\n"
        ),
    },
}

# ---------------------------------------------------------------------------
# FOLLOW-UP TEMPLATES
# Placeholders: {first_name}, {company_name}, {industry}, {original_subject}
# ---------------------------------------------------------------------------

FOLLOWUP_TEMPLATES = {
    "followup1": {
        "subject": "Re: {original_subject}",
        "body": (
            "Hi {first_name}, just floating this back up. I put together a short example "
            "of what {industry} reporting could look like with live dashboards -- happy to "
            "share the link if useful. No pressure either way.\n\n"
            "Tawanda\n"
        ),
    },
    "followup2": {
        "subject": "Different angle on this",
        "body": (
            "Hi {first_name}, one more thought -- many {industry} businesses I've spoken "
            "to waste 5-10 hours a week on manual reporting. If that sounds familiar, I "
            "think a 10-minute call could be worth it. If not, no worries at all.\n\n"
            "Tawanda\n"
        ),
    },
    "followup3": {
        "subject": "Closing the loop",
        "body": (
            "Hi {first_name}, I'll assume the timing isn't right -- totally fine. If data "
            "or reporting ever becomes a priority, I'm at tawanda@choandco.co.za. Wishing "
            "{company_name} all the best.\n\n"
            "Tawanda\n"
        ),
    },
}


def sanitize_emdashes(text: str) -> str:
    """Remove all em-dash and en-dash characters from text."""
    # Replace em-dash (U+2014)
    text = text.replace("\u2014", " -- ")
    # Replace en-dash (U+2013) between numbers with "to"
    text = re.sub(r"(\d)\u2013(\d)", r"\1 to \2", text)
    # Replace remaining en-dashes
    text = text.replace("\u2013", " -- ")
    return text
