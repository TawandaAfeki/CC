"""Logistics industry demo data definition."""
import random
from datetime import date

TABLE_NAME = "logistics_demo_data"

COLUMNS = {
    "id":                     "SERIAL PRIMARY KEY",
    "month":                  "DATE NOT NULL",
    "deliveries":             "INTEGER",
    "on_time_pct":            "NUMERIC(5,2)",
    "cost_per_km_zar":        "NUMERIC(6,2)",
    "fleet_utilisation_pct":  "NUMERIC(5,2)",
    "returns_pct":            "NUMERIC(5,2)",
    "revenue_zar":            "NUMERIC(14,2)",
    "fuel_cost_zar":          "NUMERIC(12,2)",
    "incidents":              "INTEGER",
    "km_travelled":           "INTEGER",
}

KPI_METRICS = [
    ("deliveries",            "Total Deliveries"),
    ("on_time_pct",           "On-Time Delivery (%)"),
    ("fleet_utilisation_pct", "Fleet Utilisation (%)"),
    ("cost_per_km_zar",       "Cost per km (ZAR)"),
]

CHART_METRICS = [
    ("revenue_zar",          "Monthly Revenue"),
    ("deliveries",           "Delivery Volume"),
    ("on_time_pct",          "On-Time Performance"),
    ("fuel_cost_zar",        "Fuel Cost Trend"),
]

REPORTING_SUBTITLE = "Monthly delivery performance, fleet utilisation, cost analysis, and logistics KPI tracking"

REPORT_CARDS = [
    {"color": "rc-t", "type_color": "rt-t", "type": "Operations Report",
     "title": "Monthly Operations Report \u2013 March 2025",
     "desc": "Delivery volumes, on-time rates, route efficiency, and fleet utilisation breakdown.",
     "period": "Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Cost Analysis",
     "title": "Cost per km Report \u2013 Q4 FY2024/25",
     "desc": "Fuel costs, maintenance, driver costs, cost-per-km by route, and variance analysis.",
     "period": "Jan\u2013Mar 2025", "status": "sr", "status_label": "Ready",
     "onclick": ""},
    {"color": "rc-c", "type_color": "rt-c", "type": "KPI Summary",
     "title": "Annual Logistics KPI Summary \u2013 FY2024/25",
     "desc": "Year-end scorecard: deliveries, on-time %, fleet utilisation, cost efficiency, and safety record.",
     "period": "Apr 2024 \u2013 Mar 2025", "status": "sd", "status_label": "Draft",
     "onclick": ""},
    {"color": "rc-a", "type_color": "rt-a", "type": "Client Report",
     "title": "Client SLA Performance \u2013 Template",
     "desc": "Customisable client-facing report showing deliveries, on-time rates, exceptions, and POD summary.",
     "period": "Customisable", "status": "sd", "status_label": "Template",
     "onclick": ""},
    {"color": "rc-t", "type_color": "rt-t", "type": "Fleet",
     "title": "Fleet Health Report \u2013 FY2024/25",
     "desc": "Vehicle maintenance status, age profile, downtime incidents, and replacement schedule.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
    {"color": "rc-o", "type_color": "rt-o", "type": "Returns",
     "title": "Returns & Exception Report \u2013 March 2025",
     "desc": "Return volumes, exception reasons, re-delivery costs, and client-level exception rates.",
     "period": "Mar 2025", "status": "ss", "status_label": "Coming Soon",
     "onclick": ""},
]

FAQ = [
    ("How often does dashboard data refresh?",
     "The dashboard connects live to Supabase and refreshes automatically within minutes of new delivery data being uploaded. You can also manually refresh at any time."),
    ("How do I request a client SLA performance report?",
     "Email info@choandco.co.za with the client name, date range, and required SLA metrics. Reports are delivered within 1 business day."),
    ("Can I track individual drivers or routes in the dashboard?",
     "Yes. We can configure driver-level or route-level views showing performance, utilisation, and cost per route. Contact us to set this up."),
    ("My delivery figures look incorrect, what should I do?",
     "Check your TMS or fleet management system export first. If the source data is correct, email info@choandco.co.za with a screenshot. We investigate within 4 business hours."),
    ("Who has access to my logistics data?",
     "Your data is stored in a dedicated Supabase database with row-level security. Only Cho&Co staff assigned to your account and users you authorise can access it."),
    ("How do I submit new delivery data for processing?",
     "Send your TMS export or Excel file to info@choandco.co.za. We process, clean, and upload to your dashboard within 1 business day."),
]


def generate() -> list[dict]:
    random.seed(55)
    rows = []
    base_deliveries = 3_200
    for i in range(18):
        year  = 2024 if i < 12 else 2025
        month = (i % 12) + 1
        dt    = date(year, month, 1)

        seasonal     = 1.0 + (0.18 if month in (11, 12) else -0.08 if month in (1, 2) else 0)
        deliveries   = int(base_deliveries * seasonal * random.uniform(0.93, 1.07))
        on_time      = round(random.uniform(88.0, 97.5), 2)
        cost_per_km  = round(random.uniform(5.20, 7.80), 2)
        utilisation  = round(random.uniform(74.0, 92.0), 2)
        returns      = round(random.uniform(1.5, 5.0), 2)
        km           = int(deliveries * random.uniform(18, 35))
        fuel         = round(km * random.uniform(1.80, 2.40), 2)
        revenue      = round(deliveries * random.uniform(220, 380), 2)
        incidents    = int(random.uniform(0, 4))

        rows.append({
            "month":                  dt.isoformat(),
            "deliveries":             deliveries,
            "on_time_pct":            on_time,
            "cost_per_km_zar":        cost_per_km,
            "fleet_utilisation_pct":  utilisation,
            "returns_pct":            returns,
            "revenue_zar":            revenue,
            "fuel_cost_zar":          fuel,
            "incidents":              incidents,
            "km_travelled":           km,
        })
        base_deliveries = int(base_deliveries * 1.004)
    return rows
