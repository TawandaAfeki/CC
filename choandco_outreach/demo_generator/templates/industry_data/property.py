"""Property industry demo data definition."""
import random
from datetime import date

TABLE_NAME = "property_demo_data"

COLUMNS = {
    "id":                  "SERIAL PRIMARY KEY",
    "month":               "DATE NOT NULL",
    "listings_active":     "INTEGER",
    "sales_value_zar":     "NUMERIC(16,2)",
    "units_sold":          "INTEGER",
    "avg_sale_price_zar":  "NUMERIC(14,2)",
    "rental_yield_pct":    "NUMERIC(5,2)",
    "occupancy_rate_pct":  "NUMERIC(5,2)",
    "days_on_market":      "NUMERIC(5,1)",
    "new_mandates":        "INTEGER",
    "commission_zar":      "NUMERIC(12,2)",
}

KPI_METRICS = [
    ("sales_value_zar",    "Total Sales Value (ZAR)"),
    ("units_sold",         "Units Sold"),
    ("occupancy_rate_pct", "Occupancy Rate (%)"),
    ("days_on_market",     "Avg Days on Market"),
]

CHART_METRICS = [
    ("sales_value_zar",   "Monthly Sales Value"),
    ("listings_active",   "Active Listings"),
    ("rental_yield_pct",  "Rental Yield Trend"),
    ("commission_zar",    "Commission Earned"),
]

REPORTING_SUBTITLE = "Monthly property sales, rental performance, mandate tracking, and market KPI analysis"

REPORT_CARDS = [
    {"color": "rc-t", "type_color": "rt-t", "type": "Sales Report",
     "title": "Monthly Property Sales Report \u2013 March 2025",
     "desc": "Sales value, units sold, commission breakdown, average sale price, and area performance analysis.",
     "period": "Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Rental",
     "title": "Rental Portfolio Report \u2013 Q4 FY2024/25",
     "desc": "Occupancy rates, rental yields, overdue rentals, lease renewals, and maintenance cost summary.",
     "period": "Jan\u2013Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-c", "type_color": "rt-c", "type": "KPI Summary",
     "title": "Annual Property KPI Summary \u2013 FY2024/25",
     "desc": "Year-end scorecard: sales value, commission, mandates, occupancy, and market share.",
     "period": "Apr 2024 \u2013 Mar 2025", "status": "sd", "status_label": "Draft",
     "onclick": ""},
    {"color": "rc-a", "type_color": "rt-a", "type": "Market Report",
     "title": "Area Market Analysis \u2013 Template",
     "desc": "Customisable market overview: average prices, days on market, demand trends, and comparable sales.",
     "period": "Customisable", "status": "sd", "status_label": "Template",
     "onclick": ""},
    {"color": "rc-t", "type_color": "rt-t", "type": "Mandate",
     "title": "Mandate Conversion Report \u2013 FY2024/25",
     "desc": "New mandates acquired, conversion rate to sale, expired mandates, and agent performance.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Compliance",
     "title": "FICA Compliance Summary \u2013 March 2025",
     "desc": "Client FICA status, outstanding documents, and regulatory compliance progress.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
]

FAQ = [
    ("How often does dashboard data refresh?",
     "The dashboard connects live to Supabase and refreshes automatically within minutes of new property data being uploaded. You can also manually refresh at any time."),
    ("How do I request an area market analysis?",
     "Email info@choandco.co.za with the suburb or area, property type, and date range. Custom market reports are delivered within 2 business days."),
    ("Can I track individual agents separately in the dashboard?",
     "Yes. We can configure an agent-level filtered view showing listings, sales, and commission per agent. Contact us to set this up."),
    ("My sales figures look incorrect, what should I do?",
     "Check your property management system export first. If the source data is correct but the dashboard shows a discrepancy, email info@choandco.co.za with a screenshot."),
    ("Who has access to my property data?",
     "Your data is stored in a dedicated Supabase database with row-level security. Only Cho&Co staff assigned to your account and users you authorise can access it."),
    ("How do I submit new property data for processing?",
     "Send your property management export or Excel file to info@choandco.co.za. We process, clean, and upload to your dashboard within 1 business day."),
]


def generate() -> list[dict]:
    random.seed(13)
    rows = []
    for i in range(18):
        year  = 2024 if i < 12 else 2025
        month = (i % 12) + 1
        dt    = date(year, month, 1)

        seasonal      = 1.0 + (0.2 if month in (3, 4, 10, 11) else -0.12 if month in (6, 7) else 0)
        units         = int(random.uniform(8, 22) * seasonal)
        avg_price     = round(random.uniform(1_200_000, 2_800_000), 2)
        sales_value   = round(units * avg_price * random.uniform(0.95, 1.04), 2)
        commission    = round(sales_value * random.uniform(0.045, 0.065), 2)
        listings      = int(units * random.uniform(4, 7))
        rental_yield  = round(random.uniform(6.5, 9.5), 2)
        occupancy     = round(random.uniform(84, 97), 2)
        days_on_mkt   = round(random.uniform(28, 72), 1)
        new_mandates  = int(random.uniform(10, 30))

        rows.append({
            "month":               dt.isoformat(),
            "listings_active":     listings,
            "sales_value_zar":     sales_value,
            "units_sold":          units,
            "avg_sale_price_zar":  avg_price,
            "rental_yield_pct":    rental_yield,
            "occupancy_rate_pct":  occupancy,
            "days_on_market":      days_on_mkt,
            "new_mandates":        new_mandates,
            "commission_zar":      commission,
        })
    return rows
