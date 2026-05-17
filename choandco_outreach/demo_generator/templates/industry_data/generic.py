"""Generic fallback industry demo data definition (used for unknown industries)."""
import random
from datetime import date

TABLE_NAME = "generic_demo_data"   # overridden dynamically by data_generator.py

COLUMNS = {
    "id":              "SERIAL PRIMARY KEY",
    "month":           "DATE NOT NULL",
    "revenue_zar":     "NUMERIC(14,2)",
    "client_count":    "INTEGER",
    "transactions":    "INTEGER",
    "avg_value_zar":   "NUMERIC(10,2)",
    "growth_pct":      "NUMERIC(5,2)",
    "cost_zar":        "NUMERIC(14,2)",
    "gross_profit_zar":"NUMERIC(14,2)",
    "new_clients":     "INTEGER",
}

KPI_METRICS = [
    ("revenue_zar",      "Revenue (ZAR)"),
    ("client_count",     "Total Clients"),
    ("transactions",     "Transactions"),
    ("growth_pct",       "Growth (%)"),
]

CHART_METRICS = [
    ("revenue_zar",       "Monthly Revenue"),
    ("gross_profit_zar",  "Gross Profit"),
    ("transactions",      "Transaction Volume"),
    ("client_count",      "Client Growth"),
]

REPORTING_SUBTITLE = "Monthly performance metrics, revenue analysis, client tracking, and business KPI reporting"

REPORT_CARDS = [
    {"color": "rc-t", "type_color": "rt-t", "type": "Performance Report",
     "title": "Monthly Performance Report \u2013 March 2025",
     "desc": "Revenue, transaction volumes, client count, and gross profit breakdown.",
     "period": "Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Client Report",
     "title": "Client Activity Report \u2013 Q4 FY2024/25",
     "desc": "Client acquisition, retention, transaction frequency, and average transaction value.",
     "period": "Jan\u2013Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-c", "type_color": "rt-c", "type": "KPI Summary",
     "title": "Annual KPI Summary \u2013 FY2024/25",
     "desc": "Year-end scorecard: revenue, growth, client count, profitability, and key performance indicators.",
     "period": "Apr 2024 \u2013 Mar 2025", "status": "sd", "status_label": "Draft",
     "onclick": ""},
    {"color": "rc-a", "type_color": "rt-a", "type": "Custom Report",
     "title": "Custom Performance Report \u2013 Template",
     "desc": "Customisable report template tailored to your specific business metrics and reporting needs.",
     "period": "Customisable", "status": "sd", "status_label": "Template",
     "onclick": ""},
    {"color": "rc-t", "type_color": "rt-t", "type": "Trend Analysis",
     "title": "Business Trend Analysis \u2013 FY2024/25",
     "desc": "Year-on-year trends, seasonality analysis, and growth trajectory forecast.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Profitability",
     "title": "Profitability Report \u2013 March 2025",
     "desc": "Cost structure analysis, margin trends, and profitability improvement opportunities.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
]

FAQ = [
    ("How often does dashboard data refresh?",
     "The dashboard connects live to Supabase and refreshes automatically within minutes of new data being uploaded. You can also manually refresh at any time."),
    ("How do I request a custom report?",
     "Email info@choandco.co.za with the report type, date range, and metrics needed. Standard reports delivered within 1 business day. Custom reports may take 2\u20133 business days."),
    ("Can I customise the dashboard for my specific metrics?",
     "Yes. We can add custom metrics, calculated fields, and industry-specific visualisations. Contact us to discuss your requirements."),
    ("My data looks incorrect, what should I do?",
     "Check your source data first. If the data is correct but the dashboard shows an error, email info@choandco.co.za with a screenshot. We investigate within 4 business hours."),
    ("Who has access to my data?",
     "Your data is stored in a dedicated Supabase database with row-level security. Only Cho&Co staff assigned to your account and users you authorise can access it."),
    ("How do I submit new data for processing?",
     "Send your data files (Excel, CSV, or system export) to info@choandco.co.za. We process, clean, and upload to your dashboard within 1 business day."),
]


def generate() -> list[dict]:
    random.seed(77)
    rows = []
    clients = 45
    for i in range(18):
        year  = 2024 if i < 12 else 2025
        month = (i % 12) + 1
        dt    = date(year, month, 1)

        new_clients  = int(random.uniform(2, 8))
        clients     += new_clients
        transactions = int(random.uniform(120, 350))
        avg_val      = round(random.uniform(3_500, 12_000), 2)
        revenue      = round(transactions * avg_val * random.uniform(0.95, 1.05), 2)
        cost         = round(revenue * random.uniform(0.45, 0.65), 2)
        gross_profit = round(revenue - cost, 2)
        growth       = round(random.uniform(-2.0, 12.0), 2)

        rows.append({
            "month":            dt.isoformat(),
            "revenue_zar":      revenue,
            "client_count":     clients,
            "transactions":     transactions,
            "avg_value_zar":    avg_val,
            "growth_pct":       growth,
            "cost_zar":         cost,
            "gross_profit_zar": gross_profit,
            "new_clients":      new_clients,
        })
    return rows
