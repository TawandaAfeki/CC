"""Agribusiness industry demo data definition."""
import random
from datetime import date

TABLE_NAME = "agribusiness_demo_data"

COLUMNS = {
    "id":                    "SERIAL PRIMARY KEY",
    "month":                 "DATE NOT NULL",
    "yield_tonnes":          "NUMERIC(10,2)",
    "revenue_zar":           "NUMERIC(14,2)",
    "input_costs_zar":       "NUMERIC(12,2)",
    "gross_profit_zar":      "NUMERIC(14,2)",
    "export_volume_tonnes":  "NUMERIC(10,2)",
    "commodity_price_zar":   "NUMERIC(10,2)",
    "water_usage_kl":        "NUMERIC(12,2)",
    "hectares_planted":      "NUMERIC(8,2)",
    "labour_cost_zar":       "NUMERIC(12,2)",
}

KPI_METRICS = [
    ("yield_tonnes",       "Total Yield (Tonnes)"),
    ("revenue_zar",        "Revenue (ZAR)"),
    ("gross_profit_zar",   "Gross Profit (ZAR)"),
    ("export_volume_tonnes","Export Volume (Tonnes)"),
]

CHART_METRICS = [
    ("revenue_zar",         "Monthly Revenue"),
    ("yield_tonnes",        "Yield vs Input Costs"),
    ("commodity_price_zar", "Commodity Price Trend"),
    ("export_volume_tonnes","Export Volume"),
]

REPORTING_SUBTITLE = "Monthly yield analysis, commodity pricing, cost management, and agribusiness KPI tracking"

REPORT_CARDS = [
    {"color": "rc-t", "type_color": "rt-t", "type": "Harvest Report",
     "title": "Monthly Harvest & Revenue Report \u2013 March 2025",
     "desc": "Yield by crop, revenue per tonne, commodity pricing, and gross profit breakdown.",
     "period": "Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Input Costs",
     "title": "Input Cost Analysis \u2013 Q4 FY2024/25",
     "desc": "Fertiliser, seed, fuel, labour, and water costs per hectare with budget vs actuals.",
     "period": "Jan\u2013Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-c", "type_color": "rt-c", "type": "KPI Summary",
     "title": "Annual Agribusiness KPI Summary \u2013 FY2024/25",
     "desc": "Year-end scorecard: total yield, revenue, export volume, cost efficiency, and profitability.",
     "period": "Apr 2024 \u2013 Mar 2025", "status": "sd", "status_label": "Draft",
     "onclick": ""},
    {"color": "rc-a", "type_color": "rt-a", "type": "Export Report",
     "title": "Export Performance Report \u2013 Template",
     "desc": "Customisable export report showing volumes by market, pricing, logistics costs, and compliance status.",
     "period": "Customisable", "status": "sd", "status_label": "Template",
     "onclick": ""},
    {"color": "rc-t", "type_color": "rt-t", "type": "Sustainability",
     "title": "Water & Resource Usage \u2013 FY2024/25",
     "desc": "Water consumption per hectare, irrigation efficiency, and resource sustainability metrics.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Labour",
     "title": "Labour Cost Report \u2013 March 2025",
     "desc": "Seasonal and permanent labour costs, productivity per worker, and cost per tonne analysis.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
]

FAQ = [
    ("How often does dashboard data refresh?",
     "The dashboard connects live to Supabase and refreshes automatically within minutes of new production data being uploaded. You can also manually refresh at any time."),
    ("How do I request a commodity price analysis?",
     "Email info@choandco.co.za with the commodities, date range, and market context needed. Reports delivered within 2 business days."),
    ("Can I track multiple crops or farms separately?",
     "Yes. We can configure crop-level or farm-level views showing yield, cost, and profitability per unit. Contact us to set this up."),
    ("My yield figures look incorrect, what should I do?",
     "Check your farm management system or manual records first. If the source data is correct, email info@choandco.co.za with a screenshot. We investigate within 4 business hours."),
    ("Who has access to my agribusiness data?",
     "Your data is stored in a dedicated Supabase database with row-level security. Only Cho&Co staff assigned to your account and users you authorise can access it."),
    ("How do I submit new harvest or cost data for processing?",
     "Send your farm management export or Excel file to info@choandco.co.za. We process, clean, and upload to your dashboard within 1 business day."),
]


def generate() -> list[dict]:
    random.seed(22)
    rows = []
    for i in range(18):
        year  = 2024 if i < 12 else 2025
        month = (i % 12) + 1
        dt    = date(year, month, 1)

        # SA harvest seasons: main crop Mar-May, secondary Sep-Nov
        harvest_boost = 1.8 if month in (3, 4, 5) else 1.3 if month in (9, 10, 11) else 0.6
        hectares      = round(random.uniform(180, 320), 2)
        yield_t       = round(hectares * random.uniform(2.5, 5.0) * harvest_boost, 2)
        commodity_p   = round(random.uniform(3_200, 5_800), 2)
        revenue       = round(yield_t * commodity_p * random.uniform(0.95, 1.05), 2)
        input_c       = round(hectares * random.uniform(8_000, 14_000), 2)
        labour_c      = round(hectares * random.uniform(1_200, 2_500), 2)
        gross_profit  = round(revenue - input_c - labour_c, 2)
        export_vol    = round(yield_t * random.uniform(0.25, 0.55), 2)
        water_kl      = round(hectares * random.uniform(350, 700), 2)

        rows.append({
            "month":                 dt.isoformat(),
            "yield_tonnes":          yield_t,
            "revenue_zar":           revenue,
            "input_costs_zar":       input_c,
            "gross_profit_zar":      gross_profit,
            "export_volume_tonnes":  export_vol,
            "commodity_price_zar":   commodity_p,
            "water_usage_kl":        water_kl,
            "hectares_planted":      hectares,
            "labour_cost_zar":       labour_c,
        })
    return rows
