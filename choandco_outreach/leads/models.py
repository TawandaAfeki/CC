from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Lead:
    company_name: str
    email: str
    phone: str = ""
    industry: str = ""
    website: str = ""
    source: str = ""
    location: str = ""
    raw_snippet: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)
    # Decision-maker fields
    decision_maker_name: str = ""   # e.g. "Amin Mohammed"
    decision_maker_title: str = ""  # e.g. "Manager"
    linkedin_url: str = ""          # placeholder for future enrichment
