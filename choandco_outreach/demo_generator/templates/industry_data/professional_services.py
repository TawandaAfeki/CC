"""Professional services industry demo data definition."""
import random
from datetime import date

TABLE_NAME = "professional_services_demo_data"

COLUMNS = {
    "id":                    "SERIAL PRIMARY KEY",
    "month":                 "DATE NOT NULL",
    "billable_hours":        "INTEGER",
    "revenue_zar":           "NUMERIC(14,2)",
    "utilisation_rate_pct":  "NUMERIC(5,2)",
    "client_count":          "INTEGER",
    "project_count":         "INTEGER",
    "avg_hourly_rate_zar":   "NUMERIC(8,2)",
    "new_projects":          "INTEGER",
    "completed_projects":    "INTEGER",
    "nps_score":             "NUMERIC(5,1)",
}

KPI_METRICS = [
    ("revenue_zar",          "Revenue (ZAR)"),
    ("billable_hours",       "Billable Hours"),
    ("utilisation_rate_pct", "Utilisation Rate (%)"),
    ("nps_score",            "NPS Score"),
]

CHART_METRICS = [
    ("revenue_zar",          "Monthly Revenue"),
    ("billable_hours",       "Billable Hours Trend"),
    ("utilisation_rate_pct", "Utilisation Rate"),
    ("project_count",        "Active Projects"),
]

REPORTING_SUBTITLE = "Monthly revenue, billable hours, utilisation analysis, and professional services KPI tracking"

REPORT_CARDS = [
    {"color": "rc-t", "type_color": "rt-t", "type": "Revenue Report",
     "title": "Monthly Revenue Report \u2013 March 2025",
     "desc": "Revenue by service line, consultant billing, retainer vs project income, and invoicing summary.",
     "period": "Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Utilisation",
     "title": "Team Utilisation Report \u2013 Q4 FY2024/25",
     "desc": "Billable vs non-billable hours per consultant, bench time, and capacity planning recommendations.",
     "period": "Jan\u2013Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-c", "type_color": "rt-c", "type": "KPI Summary",
     "title": "Annual KPI Summary \u2013 FY2024/25",
     "desc": "Year-end scorecard: revenue, billable hours, utilisation rate, client retention, and NPS.",
     "period": "Apr 2024 \u2013 Mar 2025", "status": "sd", "status_label": "Draft",
     "onclick": ""},
    {"color": "rc-a", "type_color": "rt-a", "type": "Client Report",
     "title": "Client Engagement Report \u2013 Template",
     "desc": "Customisable client-facing summary showing hours delivered, milestones, and value delivered.",
     "period": "Customisable", "status": "sd", "status_label": "Template",
     "onclick": ""},
    {"color": "rc-t", "type_color": "rt-t", "type": "Pipeline",
     "title": "Business Development Pipeline \u2013 FY2024/25",
     "desc": "New opportunity pipeline, conversion rates, proposal win/loss analysis, and revenue forecast.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Profitability",
     "title": "Project Profitability Report \u2013 March 2025",
     "desc": "Project-level margin analysis, budget vs actuals, write-offs, and scope creep tracking.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
]

FAQ = [
    ("How often does dashboard data refresh?",
     "The dashboard connects live to Supabase and refreshes automatically within minutes of new time and billing data being uploaded. You can also manually refresh at any time."),
    ("How do I request a project profitability analysis?",
     "Email info@choandco.co.za with the project names or IDs, date range, and cost details. Reports are delivered within 1 business day."),
    ("Can I track individual consultants or service lines separately?",
     "Yes. We can configure consultant-level or service-line views showing revenue, hours, and utilisation. Contact us to set this up."),
    ("My billable hours look incorrect, what should I do?",
     "Check your time-tracking or practice management system export first. If the source data is correct, email info@choandco.co.za with a screenshot."),
    ("Who has access to my firm data?",
     "Your data is stored in a dedicated Supabase database with row-level security. Only Cho&Co staff assigned to your account and users you authorise can access it."),
    ("How do I submit new time and billing data?",
     "Send your practice management export or Excel file to info@choandco.co.za. We process, clean, and upload to your dashboard within 1 business day."),
]


def generate() -> list[dict]:
    random.seed(33)
    rows = []
    base_rev = 620_000
    clients = 28
    projects = 14
    for i in range(18):
        year  = 2024 if i < 12 else 2025
        month = (i % 12) + 1
        dt    = date(year, month, 1)

        seasonal      = 1.0 + (0.12 if month in (3, 9, 10) else -0.15 if month in (12, 1) else 0)
        billable_hrs  = int(random.uniform(1_800, 3_200) * seasonal)
        avg_rate      = round(random.uniform(850, 1_600), 2)
        revenue       = round(billable_hrs * avg_rate * random.uniform(0.95, 1.05), 2)
        utilisation   = round(random.uniform(68, 88), 2)
        new_proj      = int(random.uniform(2, 7))
        comp_proj     = int(random.uniform(1, 5))
        projects     += new_proj - comp_proj
        projects      = max(projects, 6)
        new_clients   = int(random.uniform(0, 3))
        clients      += new_clients
        nps           = round(random.uniform(42, 78), 1)

        rows.append({
            "month":                 dt.isoformat(),
            "billable_hours":        billable_hrs,
            "revenue_zar":           revenue,
            "utilisation_rate_pct":  utilisation,
            "client_count":          clients,
            "project_count":         projects,
            "avg_hourly_rate_zar":   avg_rate,
            "new_projects":          new_proj,
            "completed_projects":    comp_proj,
            "nps_score":             nps,
        })
        base_rev *= 1.005
    return rows
