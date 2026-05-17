import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "data"
TEMPLATES_DIR   = BASE_DIR / "templates"
COMPLETED_DEMOS = DATA_DIR / "completed_demos.json"
OUTREACH_EXCEL  = Path(__file__).parent.parent / "data" / "outreach_log.xlsx"

# ── Supabase ───────────────────────────────────────────────────────────────
SUPABASE_URL            = os.getenv("SUPABASE_URL", "https://ahdctxgdszwncyuvwbtp.supabase.co")
SUPABASE_SERVICE_KEY    = os.getenv("SUPABASE_SERVICE_KEY", "")
SUPABASE_PROJECT_REF    = SUPABASE_URL.split("//")[1].split(".")[0]   # ahdctxgdszwncyuvwbtp
SUPABASE_DB_HOST        = f"db.{SUPABASE_PROJECT_REF}.supabase.co"
SUPABASE_DB_PASSWORD    = os.getenv("SUPABASE_DB_PASSWORD", "")
SUPABASE_DB_USER        = "postgres"
SUPABASE_DB_NAME        = "postgres"
SUPABASE_DB_PORT        = 5432
REPORTS_BUCKET          = "Reports"

# ── Metabase ───────────────────────────────────────────────────────────────
METABASE_URL            = os.getenv("METABASE_URL", "https://metabase-production-2504.up.railway.app")
METABASE_API_KEY        = os.getenv("METABASE_API_KEY", "")
METABASE_USERNAME       = os.getenv("METABASE_USERNAME", "")
METABASE_PASSWORD       = os.getenv("METABASE_PASSWORD", "")
METABASE_DB_ID          = int(os.getenv("METABASE_DB_ID", "0"))

# ── GitHub ─────────────────────────────────────────────────────────────────
GITHUB_TOKEN            = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME         = os.getenv("GITHUB_USERNAME", "")
GITHUB_REPO             = "CC"
GITHUB_BRANCH           = "main"

# ── Netlify ────────────────────────────────────────────────────────────────
NETLIFY_TOKEN           = os.getenv("NETLIFY_TOKEN", "")
NETLIFY_DOMAIN_SUFFIX   = "choandco.co.za"

# ── SMTP (reuses outreach agent credentials) ───────────────────────────────
SMTP_HOST               = "smtpout.secureserver.net"
SMTP_PORT               = 587
SMTP_USER               = os.getenv("TITAN_SMTP_USER", "")
SMTP_PASSWORD           = os.getenv("TITAN_SMTP_PASSWORD", "")
NOTIFY_EMAIL            = "afekitawanda@gmail.com"
FROM_EMAIL              = SMTP_USER

# ── Industry name normalisation map ───────────────────────────────────────
# Maps raw Excel values → canonical slug used for table names, folders, domains
INDUSTRY_SLUG_MAP = {
    "accounting":            "accounting",
    "recruitment":           "recruitment",
    "retail":                "retail",
    "financial services":    "financial_services",
    "financial_services":    "financial_services",
    "property":              "property",
    "professional services": "professional_services",
    "professional_services": "professional_services",
    "logistics":             "logistics",
    "agribusiness":          "agribusiness",
}

def slug(industry: str) -> str:
    """Return canonical slug for an industry string."""
    key = industry.strip().lower()
    return INDUSTRY_SLUG_MAP.get(key, key.replace(" ", "_"))
