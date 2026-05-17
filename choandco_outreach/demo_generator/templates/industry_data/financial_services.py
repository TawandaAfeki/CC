"""Financial services industry demo data definition."""
import random
from datetime import date

TABLE_NAME = "financial_services_demo_data"

COLUMNS = {
    "id":                  "SERIAL PRIMARY KEY",
    "month":               "DATE NOT NULL",
    "aum_zar":             "NUMERIC(18,2)",
    "client_count":        "INTEGER",
    "revenue_zar":         "NUMERIC(14,2)",
    "new_accounts":        "INTEGER",
    "closed_accounts":     "INTEGER",
    "net_inflows_zar":     "NUMERIC(14,2)",
    "compliance_rate_pct": "NUMERIC(5,2)",
    "avg_return_pct":      "NUMERIC(5,2)",
    "advisory_hours":      "INTEGER",
}

KPI_METRICS = [
    ("aum_zar",             "Assets Under Management (ZAR)"),
    ("client_count",        "Total Clients"),
    ("revenue_zar",         "Revenue (ZAR)"),
    ("compliance_rate_pct", "Compliance Rate (%)"),
]

CHART_METRICS = [
    ("aum_zar",          "AUM Growth"),
    ("net_inflows_zar",  "Net Inflows / Outflows"),
    ("new_accounts",     "New Accounts per Month"),
    ("avg_return_pct",   "Average Portfolio Return"),
]

REPORTING_SUBTITLE = "Monthly AUM analysis, client growth, compliance tracking, and financial services KPI reporting"

REPORT_CARDS = [
    {"color": "rc-t", "type_color": "rt-t", "type": "AUM Report",
     "title": "Monthly AUM Report \u2013 March 2025",
     "desc": "Assets under management breakdown, net inflows, portfolio performance, and asset class allocation.",
     "period": "Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Compliance",
     "title": "Compliance Status Report \u2013 Q4 FY2024/25",
     "desc": "FAIS compliance score, outstanding FICA documents, audit findings, and regulatory deadline tracker.",
     "period": "Jan\u2013Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-c", "type_color": "rt-c", "type": "KPI Summary",
     "title": "Annual KPI Summary \u2013 FY2024/25",
     "desc": "Year-end scorecard: AUM, revenue, client count, compliance rate, and portfolio performance.",
     "period": "Apr 2024 \u2013 Mar 2025", "status": "sd", "status_label": "Draft",
     "onclick": ""},
    {"color": "rc-a", "type_color": "rt-a", "type": "Client Report",
     "title": "Client Portfolio Statement \u2013 Template",
     "desc": "Customisable client-facing statement with portfolio value, returns, transactions, and fees.",
     "period": "Customisable", "status": "sd", "status_label": "Template",
     "onclick": ""},
    {"color": "rc-t", "type_color": "rt-t", "type": "Risk",
     "title": "Risk Exposure Report \u2013 FY2024/25",
     "desc": "Portfolio risk metrics, concentration risk, market exposure, and stress test results.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Revenue",
     "title": "Revenue & Fee Analysis \u2013 March 2025",
     "desc": "Advisory fee income, performance fees, product revenue, and fee-to-AUM ratio.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
]

FAQ = [
    ("How often does dashboard data refresh?",
     "The dashboard connects live to Supabase and refreshes automatically within minutes of new financial data being uploaded. You can also manually refresh at any time."),
    ("How do I request a client portfolio statement?",
     "Email info@choandco.co.za with the client name, date range, and preferred format. Statements are delivered within 1 business day."),
    ("Can I track compliance deadlines in the dashboard?",
     "Yes. We can add a compliance calendar view showing upcoming FAIS, FICA, and regulatory deadlines. Contact us to configure this."),
    ("My AUM figures look incorrect, what should I do?",
     "Check your portfolio management system export first. If the source data is correct but the dashboard shows a discrepancy, email info@choandco.co.za with a screenshot."),
    ("Who has access to my financial data?",
     "Your data is stored in a dedicated Supabase database with row-level security and encryption at rest. Only Cho&Co staff assigned to your account and users you authorise can access it."),
    ("How do I submit updated portfolio data?",
     "Send your portfolio management export or Excel file to info@choandco.co.za. We process, clean, and upload to your dashboard within 1 business day."),
]


def generate() -> list[dict]:
    random.seed(99)
    rows = []
    aum = 85_000_000
    clients = 142
    for i in range(18):
        year  = 2024 if i < 12 else 2025
        month = (i % 12) + 1
        dt    = date(year, month, 1)

        new_acc    = int(random.uniform(3, 10))
        closed_acc = int(random.uniform(0, 3))
        clients   += new_acc - closed_acc
        inflows    = round(random.uniform(800_000, 3_500_000), 2)
        aum        = round(aum * random.uniform(0.98, 1.04) + inflows, 2)
        revenue    = round(aum * random.uniform(0.0008, 0.0015), 2)
        compliance = round(random.uniform(92.0, 99.5), 2)
        avg_return = round(random.uniform(6.5, 14.0), 2)
        adv_hours  = int(random.uniform(120, 280))

        rows.append({
            "month":               dt.isoformat(),
            "aum_zar":             aum,
            "client_count":        clients,
            "revenue_zar":         revenue,
            "new_accounts":        new_acc,
            "closed_accounts":     closed_acc,
            "net_inflows_zar":     inflows,
            "compliance_rate_pct": compliance,
            "avg_return_pct":      avg_return,
            "advisory_hours":      adv_hours,
        })
    return rows
