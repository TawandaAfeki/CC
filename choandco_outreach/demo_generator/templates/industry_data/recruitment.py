"""Recruitment industry demo data definition."""
import random
from datetime import date

TABLE_NAME = "recruitment_demo_data"

COLUMNS = {
    "id":                    "SERIAL PRIMARY KEY",
    "month":                 "DATE NOT NULL",
    "placements":            "INTEGER",
    "revenue_zar":           "NUMERIC(14,2)",
    "avg_fee_zar":           "NUMERIC(10,2)",
    "candidate_pipeline":    "INTEGER",
    "avg_time_to_fill_days": "NUMERIC(5,1)",
    "success_rate_pct":      "NUMERIC(5,2)",
    "permanent_placements":  "INTEGER",
    "contract_placements":   "INTEGER",
    "new_client_accounts":   "INTEGER",
}

KPI_METRICS = [
    ("placements",            "Total Placements"),
    ("revenue_zar",           "Revenue (ZAR)"),
    ("avg_time_to_fill_days", "Avg Time to Fill (Days)"),
    ("success_rate_pct",      "Success Rate (%)"),
]

CHART_METRICS = [
    ("revenue_zar",          "Monthly Revenue"),
    ("placements",           "Monthly Placements"),
    ("candidate_pipeline",   "Candidate Pipeline"),
    ("success_rate_pct",     "Success Rate Trend"),
]

REPORTING_SUBTITLE = "Monthly placement performance, revenue analysis, pipeline metrics, and recruitment KPI tracking"

REPORT_CARDS = [
    {"color": "rc-t", "type_color": "rt-t", "type": "Placements Report",
     "title": "Monthly Placements Report \u2013 March 2025",
     "desc": "Permanent vs contract placements, revenue per placement, top sectors filled, and consultant performance breakdown.",
     "period": "Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Pipeline",
     "title": "Candidate Pipeline Report \u2013 Q4 FY2024/25",
     "desc": "Active candidates by stage, time-in-stage analysis, drop-off rates, and pipeline health score.",
     "period": "Jan\u2013Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-c", "type_color": "rt-c", "type": "KPI Summary",
     "title": "Annual Recruitment KPI Summary \u2013 FY2024/25",
     "desc": "Year-end scorecard: placements, revenue, fill rate, time-to-fill, and client retention.",
     "period": "Apr 2024 \u2013 Mar 2025", "status": "sd", "status_label": "Draft",
     "onclick": ""},
    {"color": "rc-a", "type_color": "rt-a", "type": "Client Report",
     "title": "Client Account Performance \u2013 Template",
     "desc": "Customisable client-facing report showing vacancies filled, time-to-fill, and candidate quality scores.",
     "period": "Customisable", "status": "sd", "status_label": "Template",
     "onclick": ""},
    {"color": "rc-t", "type_color": "rt-t", "type": "Sector Analysis",
     "title": "Sector Demand Analysis \u2013 FY2024/25",
     "desc": "Hiring demand by industry sector, salary benchmarking, and skills gap analysis.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Consultant",
     "title": "Consultant Performance Report \u2013 March 2025",
     "desc": "Individual consultant billings, activity metrics, conversion rates, and targets vs actuals.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
]

FAQ = [
    ("How often does dashboard data refresh?",
     "The dashboard connects live to Supabase and refreshes automatically within minutes of new placement data being uploaded. You can also manually refresh at any time."),
    ("How do I request a consultant performance report?",
     "Email info@choandco.co.za with the consultant names, date range, and metrics needed. Reports are delivered within 1 business day."),
    ("Can I track vacancies by client separately?",
     "Yes. We can create a client-filtered view showing all vacancies, stages, and placements for a specific account. Contact us to configure this."),
    ("My placement count looks incorrect, what should I do?",
     "Check your ATS export first. If the source data is correct but the dashboard shows a discrepancy, email info@choandco.co.za with a screenshot."),
    ("Who has access to my recruitment data?",
     "Your data is stored in a dedicated Supabase database with row-level security. Only Cho&Co staff assigned to your account and users you authorise can access it."),
    ("How do I submit new placement data for processing?",
     "Send your ATS export or Excel file to info@choandco.co.za. We process, clean, and upload to your dashboard within 1 business day."),
]


def generate() -> list[dict]:
    random.seed(7)
    rows = []
    base_rev = 480_000
    for i in range(18):
        year  = 2024 if i < 12 else 2025
        month = (i % 12) + 1
        dt    = date(year, month, 1)

        seasonal     = 1.0 + (0.15 if month in (3, 4, 9, 10) else -0.1 if month in (12, 1) else 0)
        placements   = int(random.uniform(12, 26) * seasonal)
        perm         = int(placements * random.uniform(0.55, 0.75))
        contract     = placements - perm
        avg_fee      = round(random.uniform(28_000, 52_000), 2)
        revenue      = round(placements * avg_fee * random.uniform(0.92, 1.05), 2)
        pipeline     = int(placements * random.uniform(8, 15))
        fill_time    = round(random.uniform(18, 38), 1)
        success_rate = round(random.uniform(62, 84), 2)
        new_clients  = int(random.uniform(1, 4))

        rows.append({
            "month":                 dt.isoformat(),
            "placements":            placements,
            "revenue_zar":           revenue,
            "avg_fee_zar":           avg_fee,
            "candidate_pipeline":    pipeline,
            "avg_time_to_fill_days": fill_time,
            "success_rate_pct":      success_rate,
            "permanent_placements":  perm,
            "contract_placements":   contract,
            "new_client_accounts":   new_clients,
        })
        base_rev *= 1.006
    return rows
