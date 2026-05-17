import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Company info
COMPANY_NAME = "Cho&Co"
WEBSITE = "www.choandco.co.za"
FOUNDER = "Tawanda Afeki"
SENDER_EMAIL = "info@choandco.co.za"
PHONE = "+27 71 060 2976"
PRICING = "R5,000 - R10,000"
DELIVERY = "5 to 10 business days"
STATS_DECISIONS = "28% faster decision-making"
STATS_ACCURACY = "over 31% improvement in data accuracy"

SERVICES = [
    "Data cleaning and validation",
    "Analytics dashboards (Tableau and Power BI)",
    "Customized reporting tailored to your business",
]

# SMTP (GoDaddy / secureserver.net) - Port 587 STARTTLS for deliverability
SMTP_HOST = "smtpout.secureserver.net"
SMTP_PORT = 587
SMTP_USER = os.getenv("TITAN_SMTP_USER", "")
SMTP_PASSWORD = os.getenv("TITAN_SMTP_PASSWORD", "")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = DATA_DIR / "outreach_log.xlsx"
DEDUP_PATH = DATA_DIR / "sent_hashes.json"
LOG_PATH = BASE_DIR / "outreach.log"

# Recipient for daily summary
SUMMARY_RECIPIENT = "afekitawanda@gmail.com"

# Rate limiting
SCRAPE_DELAY_RANGE = (3, 7)
EMAIL_DELAY_RANGE = (30, 90)
MAX_EMAILS_PER_RUN = 20
REQUEST_TIMEOUT = 15

# Priority sectors for outreach (Phase 2 — 8 high-value sectors)
INDUSTRIES = [
    "accounting",
    "recruitment",
    "retail",
    "financial services",
    "property",
    "professional services",
    "logistics",
    "agribusiness",
]
