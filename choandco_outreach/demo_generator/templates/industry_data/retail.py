"""Retail industry demo data definition."""
import random
from datetime import date

TABLE_NAME = "retail_demo_data"

COLUMNS = {
    "id":                  "SERIAL PRIMARY KEY",
    "month":               "DATE NOT NULL",
    "total_sales_zar":     "NUMERIC(14,2)",
    "units_sold":          "INTEGER",
    "avg_basket_size_zar": "NUMERIC(10,2)",
    "foot_traffic":        "INTEGER",
    "gross_margin_pct":    "NUMERIC(5,2)",
    "inventory_turnover":  "NUMERIC(5,2)",
    "online_sales_zar":    "NUMERIC(14,2)",
    "returns_pct":         "NUMERIC(5,2)",
}

KPI_METRICS = [
    ("total_sales_zar",     "Total Sales (ZAR)"),
    ("units_sold",          "Units Sold"),
    ("avg_basket_size_zar", "Avg Basket Size (ZAR)"),
    ("gross_margin_pct",    "Gross Margin (%)"),
]

CHART_METRICS = [
    ("total_sales_zar",  "Monthly Sales Revenue"),
    ("foot_traffic",     "Monthly Foot Traffic"),
    ("online_sales_zar", "Online vs In-Store Sales"),
    ("gross_margin_pct", "Gross Margin Trend"),
]

REPORTING_SUBTITLE = "Monthly sales performance, margin analysis, inventory insights, and retail KPI tracking"

REPORT_CARDS = [
    {"color": "rc-t", "type_color": "rt-t", "type": "Sales Report",
     "title": "Monthly Sales Report \u2013 March 2025",
     "desc": "Full revenue breakdown, basket size analysis, online vs in-store split, and top-performing product categories.",
     "period": "Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Inventory",
     "title": "Inventory Turnover Report \u2013 Q4 FY2024/25",
     "desc": "Stock turnover rates, slow-moving SKUs, overstock flags, and recommended reorder levels.",
     "period": "Jan\u2013Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-c", "type_color": "rt-c", "type": "KPI Summary",
     "title": "Annual Retail KPI Summary \u2013 FY2024/25",
     "desc": "Year-end scorecard: revenue, margin, traffic, basket size, returns rate, and category performance.",
     "period": "Apr 2024 \u2013 Mar 2025", "status": "sd", "status_label": "Draft",
     "onclick": ""},
    {"color": "rc-a", "type_color": "rt-a", "type": "Customer Report",
     "title": "Customer Behaviour Report \u2013 Template",
     "desc": "Customisable report showing purchase frequency, loyalty programme stats, and segment breakdown.",
     "period": "Customisable", "status": "sd", "status_label": "Template",
     "onclick": ""},
    {"color": "rc-t", "type_color": "rt-t", "type": "Promotions",
     "title": "Promotional Effectiveness \u2013 FY2024/25",
     "desc": "ROI on promotional campaigns, discount impact on margin, and redemption rates.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "E-commerce",
     "title": "Online Sales Summary \u2013 March 2025",
     "desc": "Digital channel revenue, conversion rates, cart abandonment, and delivery performance.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
]

FAQ = [
    ("How often does dashboard data refresh?",
     "The dashboard connects live to Supabase and refreshes automatically within minutes of new sales data being uploaded. You can also manually refresh your browser at any time."),
    ("How do I request a category breakdown report?",
     "Email info@choandco.co.za with the product categories, date range, and metrics needed. Standard reports delivered within 1 business day."),
    ("Can I track promotions separately in the dashboard?",
     "Yes. We can create a dedicated promotions view filtered by campaign tag. Contact us to set this up for your next promotion."),
    ("My sales figures look incorrect, what should I do?",
     "Verify your POS or e-commerce export first. If the source data is correct but the dashboard shows an error, email info@choandco.co.za with a screenshot. We investigate within 4 business hours."),
    ("Who has access to my retail data?",
     "Your data is stored in a dedicated Supabase database with row-level security. Only Cho&Co staff assigned to your account and users you authorise can access it."),
    ("How do I submit new sales data for processing?",
     "Send your POS export, CSV, or Excel file to info@choandco.co.za. We process, clean, and upload to your dashboard within 1 business day."),
]


def generate() -> list[dict]:
    """Return 18 months of realistic retail demo data."""
    random.seed(42)
    rows = []
    base_sales = 850_000
    for i in range(18):
        year  = 2024 if i < 12 else 2025
        month = (i % 12) + 1
        dt    = date(year, month, 1)

        seasonal = 1.0 + 0.25 * (1 if month in (11, 12) else -0.05 if month in (1, 2) else 0)
        sales    = round(base_sales * seasonal * random.uniform(0.93, 1.08), 2)
        units    = int(sales / random.uniform(120, 160))
        basket   = round(sales / max(units, 1), 2)
        traffic  = int(units * random.uniform(3.5, 5.5))
        margin   = round(random.uniform(28.0, 38.0), 2)
        turnover = round(random.uniform(6.0, 10.0), 2)
        online   = round(sales * random.uniform(0.18, 0.32), 2)
        returns  = round(random.uniform(2.0, 6.5), 2)

        rows.append({
            "month":               dt.isoformat(),
            "total_sales_zar":     sales,
            "units_sold":          units,
            "avg_basket_size_zar": basket,
            "foot_traffic":        traffic,
            "gross_margin_pct":    margin,
            "inventory_turnover":  turnover,
            "online_sales_zar":    online,
            "returns_pct":         returns,
        })
        base_sales *= 1.005   # gentle monthly growth
    return rows
