"""
Corevest (Pty) Ltd — Cho&Co Analytics Portal Builder
=====================================================
End-to-end pipeline:
  1. Generate 6 datasets (portfolio, properties, financials, leases, projects, investors)
  2. Create Supabase tables + insert all rows
  3. Build 5 Metabase dashboards + enable public links
  4. Generate 5 branded PDF reports + upload to Supabase Storage
  5. Build custom multi-dashboard HTML portal
  6. Deploy to Netlify → corevest-choandco.netlify.app
"""

import hashlib
import logging
import os
import sys
import time
import random
import requests
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from demo_generator.modules.supabase_client import create_table, insert_rows, upload_pdf as sb_upload_pdf, _mgmt_headers, SUPABASE_PROJECT_REF
from demo_generator.modules.pdf_generator import generate_pdf, _safe, _Report, _NAVY, _GOLD, _LIGHT, _WHITE, _DARK
from demo_generator.modules.netlify_deployer import deploy as netlify_deploy
from demo_generator.config import (
    METABASE_URL, METABASE_API_KEY, METABASE_USERNAME, METABASE_PASSWORD, METABASE_DB_ID
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

random.seed(42)
TODAY = date(2026, 5, 17)
SLUG  = "corevest"
LABEL = "Corevest"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

PROPERTIES_DATA = [
    {"property_name": "Claremont Office Park",       "property_type": "Commercial",  "suburb": "Claremont",   "city": "Cape Town", "acquisition_year": 2018, "acquisition_price_zar": 12500000, "current_value_zar": 18200000, "gla_sqm": 1200, "total_units": 8,  "fund_name": "Core Fund I",  "status": "Active"},
    {"property_name": "Newlands Retail Strip",        "property_type": "Commercial",  "suburb": "Newlands",    "city": "Cape Town", "acquisition_year": 2019, "acquisition_price_zar": 8900000,  "current_value_zar": 11400000, "gla_sqm": 680,  "total_units": 5,  "fund_name": "Core Fund I",  "status": "Active"},
    {"property_name": "Rondebosch Residential Block", "property_type": "Residential", "suburb": "Rondebosch",  "city": "Cape Town", "acquisition_year": 2020, "acquisition_price_zar": 15200000, "current_value_zar": 19800000, "gla_sqm": 2100, "total_units": 12, "fund_name": "Core Fund I",  "status": "Active"},
    {"property_name": "Kenilworth Commercial Hub",    "property_type": "Commercial",  "suburb": "Kenilworth",  "city": "Cape Town", "acquisition_year": 2017, "acquisition_price_zar": 22000000, "current_value_zar": 31500000, "gla_sqm": 2800, "total_units": 14, "fund_name": "Core Fund I",  "status": "Active"},
    {"property_name": "Observatory Mixed-Use",        "property_type": "Mixed-Use",   "suburb": "Observatory", "city": "Cape Town", "acquisition_year": 2021, "acquisition_price_zar": 18700000, "current_value_zar": 22100000, "gla_sqm": 1850, "total_units": 10, "fund_name": "Core Fund II", "status": "Active"},
    {"property_name": "Wynberg Light Industrial",     "property_type": "Industrial",  "suburb": "Wynberg",     "city": "Cape Town", "acquisition_year": 2022, "acquisition_price_zar": 9500000,  "current_value_zar": 10800000, "gla_sqm": 1400, "total_units": 6,  "fund_name": "Core Fund II", "status": "Active"},
    {"property_name": "Constantia Upper Residential", "property_type": "Residential", "suburb": "Constantia",  "city": "Cape Town", "acquisition_year": 2016, "acquisition_price_zar": 28000000, "current_value_zar": 42000000, "gla_sqm": 3200, "total_units": 8,  "fund_name": "Core Fund I",  "status": "Active"},
    {"property_name": "Salt River Dev Project",       "property_type": "Development", "suburb": "Salt River",  "city": "Cape Town", "acquisition_year": 2023, "acquisition_price_zar": 11000000, "current_value_zar": 12500000, "gla_sqm": 1600, "total_units": 0,  "fund_name": "Core Fund II", "status": "Development"},
]

# Per-property base rents (R/month) and occupancy floors
_PROP_CONFIG = {
    "Claremont Office Park":       {"base_rent": 95000,  "occ_base": 87},
    "Newlands Retail Strip":       {"base_rent": 52000,  "occ_base": 80},
    "Rondebosch Residential Block":{"base_rent": 132000, "occ_base": 92},
    "Kenilworth Commercial Hub":   {"base_rent": 185000, "occ_base": 85},
    "Observatory Mixed-Use":       {"base_rent": 118000, "occ_base": 88},
    "Wynberg Light Industrial":    {"base_rent": 72000,  "occ_base": 83},
    "Constantia Upper Residential":{"base_rent": 210000, "occ_base": 94},
    "Salt River Dev Project":      {"base_rent": 0,      "occ_base": 0},
}

LEASE_TENANTS = [
    # Claremont Office Park (8 units)
    ("Claremont Office Park", "Nexus Advisory (Pty) Ltd",      "Unit 1", "2023-03-01", "2026-02-28", 13500, 8.0,  "Active",  "High"),
    ("Claremont Office Park", "BluePeak Consulting",           "Unit 2", "2022-07-01", "2026-06-30", 12800, 7.5,  "Active",  "Medium"),
    ("Claremont Office Park", "Meridian Tax Services",         "Unit 3", "2024-01-01", "2026-12-31", 11900, 8.0,  "Active",  "High"),
    ("Claremont Office Park", "Apex Digital (Pty) Ltd",        "Unit 4", "2021-09-01", "2026-08-31", 14200, 8.5,  "Active",  "Low"),
    ("Claremont Office Park", "Southgate Legal Inc",           "Unit 5", "2023-06-01", "2027-05-31", 12500, 8.0,  "Active",  "High"),
    ("Claremont Office Park", "CoreBridge Finance",            "Unit 6", "2024-04-01", "2027-03-31", 13100, 7.0,  "Active",  "High"),
    ("Claremont Office Park", "Vantage HR Solutions",          "Unit 7", "2022-11-01", "2026-10-31", 11800, 8.0,  "Active",  "Medium"),
    ("Claremont Office Park", "[Vacant]",                      "Unit 8", "2025-05-01", "2026-05-31", 0,     0,    "Vacant",  "N/A"),
    # Newlands Retail Strip (5 units)
    ("Newlands Retail Strip",  "Cafe Belleza",                 "Shop 1", "2023-02-01", "2026-01-31", 9800,  9.0,  "Active",  "Medium"),
    ("Newlands Retail Strip",  "Fresh Wellness Pharmacy",      "Shop 2", "2022-08-01", "2026-07-31", 11200, 8.5,  "Active",  "High"),
    ("Newlands Retail Strip",  "Crafted Ink Tattoo Studio",   "Shop 3", "2024-03-01", "2027-02-28", 8500,  8.0,  "Active",  "High"),
    ("Newlands Retail Strip",  "The Bread Box Deli",           "Shop 4", "2021-10-01", "2026-09-30", 10100, 9.0,  "Active",  "Low"),
    ("Newlands Retail Strip",  "Studio Glow Beauty",           "Shop 5", "2023-11-01", "2026-10-31", 9300,  8.5,  "Active",  "Medium"),
    # Rondebosch Residential Block (sample 6 of 12)
    ("Rondebosch Residential Block", "T. Mthembu",             "Apt 1",  "2023-01-01", "2026-12-31", 11500, 8.0,  "Active",  "High"),
    ("Rondebosch Residential Block", "L. van der Merwe",       "Apt 2",  "2022-06-01", "2026-05-31", 10800, 8.0,  "Active",  "Low"),
    ("Rondebosch Residential Block", "S. Petersen",            "Apt 3",  "2024-02-01", "2027-01-31", 11200, 8.0,  "Active",  "High"),
    # Kenilworth Commercial Hub (sample 5 of 14)
    ("Kenilworth Commercial Hub", "PrimeTech Logistics",       "Bay A",  "2022-04-01", "2026-03-31", 18500, 7.5,  "Active",  "Medium"),
    ("Kenilworth Commercial Hub", "Anchor Foods (Pty) Ltd",    "Bay B",  "2023-09-01", "2027-08-31", 21000, 8.0,  "Active",  "High"),
    ("Kenilworth Commercial Hub", "BuildRight Materials",      "Bay C",  "2021-11-01", "2026-10-31", 17800, 7.5,  "Active",  "Low"),
    # Observatory Mixed-Use
    ("Observatory Mixed-Use",  "Orbit Coffee & Co",           "G-01",   "2024-01-01", "2026-12-31", 9200,  9.0,  "Active",  "High"),
    ("Observatory Mixed-Use",  "Capsule Gym",                 "G-02",   "2022-05-01", "2026-04-30", 14500, 8.5,  "Active",  "Low"),
    # Wynberg Light Industrial
    ("Wynberg Light Industrial", "Cape Cold Chain (Pty) Ltd",  "W-01",   "2023-07-01", "2027-06-30", 18200, 7.0,  "Active",  "High"),
    ("Wynberg Light Industrial", "SA Fabrications Ltd",        "W-02",   "2022-03-01", "2026-06-30", 16900, 7.5,  "Active",  "Medium"),
    # Constantia Upper Residential
    ("Constantia Upper Residential", "D. Engelbrecht",         "Villa 1","2023-03-01", "2027-02-28", 28500, 8.0,  "Active",  "High"),
    ("Constantia Upper Residential", "M. Osei-Bonsu",          "Villa 2","2022-09-01", "2026-08-31", 26800, 8.5,  "Active",  "Medium"),
]

PROJECTS_DATA = [
    {"project_name": "Salt River Mixed-Use Development",  "project_type": "New Development", "start_date": "2025-08-01", "target_completion": "2027-03-31", "budget_zar": 24500000, "spent_zar": 9800000,  "completion_pct": 40.0, "rag_status": "On Track",    "contractor": "Batho Builders (Pty) Ltd",  "notes": "Foundation complete, structural phase underway"},
    {"project_name": "Kenilworth Hub Roof Refurbishment", "project_type": "Renovation",      "start_date": "2025-11-01", "target_completion": "2026-04-30", "budget_zar": 1850000,  "spent_zar": 2120000,  "completion_pct": 95.0, "rag_status": "Over Budget",  "contractor": "CapeRoof Solutions",        "notes": "Scope expansion added waterproofing layer - R270k over budget"},
    {"project_name": "Observatory Solar Installation",    "project_type": "Energy Upgrade",  "start_date": "2026-01-01", "target_completion": "2026-06-30", "budget_zar": 980000,   "spent_zar": 520000,   "completion_pct": 55.0, "rag_status": "On Track",    "contractor": "SunPower Cape (Pty) Ltd",   "notes": "Panels installed, inverter wiring in progress"},
    {"project_name": "Rondebosch Common Area Upgrade",   "project_type": "Renovation",      "start_date": "2026-03-01", "target_completion": "2026-07-31", "budget_zar": 650000,   "spent_zar": 180000,   "completion_pct": 25.0, "rag_status": "On Track",    "contractor": "NuSpace Interiors",         "notes": "Phase 1 lobby done, Phase 2 gardens starting June"},
    {"project_name": "Wynberg Industrial Yard Expansion", "project_type": "New Development", "start_date": "2026-06-01", "target_completion": "2026-12-31", "budget_zar": 3200000,  "spent_zar": 0,        "completion_pct": 0.0,  "rag_status": "Planning",    "contractor": "TBC",                       "notes": "Town planning approval received - tender process Q3 2026"},
]

INVESTORS_DATA = [
    {"investor_name": "Harrington Capital Partners",  "fund_name": "Core Fund I",  "investment_amount_zar": 5000000,  "equity_pct": 14.2, "entry_year": 2018, "ytd_distribution_zar": 285000,  "total_distributions_zar": 1820000, "irr_pct": 13.8},
    {"investor_name": "Stellenbosch Family Office",   "fund_name": "Core Fund I",  "investment_amount_zar": 8500000,  "equity_pct": 24.1, "entry_year": 2017, "ytd_distribution_zar": 484500,  "total_distributions_zar": 3612000, "irr_pct": 14.8},
    {"investor_name": "Cape Horizon Trust",           "fund_name": "Core Fund I",  "investment_amount_zar": 3000000,  "equity_pct": 8.5,  "entry_year": 2020, "ytd_distribution_zar": 171000,  "total_distributions_zar": 684000,  "irr_pct": 11.4},
    {"investor_name": "BlueSands Wealth (Pty) Ltd",   "fund_name": "Core Fund II", "investment_amount_zar": 6000000,  "equity_pct": 31.4, "entry_year": 2021, "ytd_distribution_zar": 252000,  "total_distributions_zar": 756000,  "irr_pct": 10.2},
    {"investor_name": "Meridian Asset Holdings",      "fund_name": "Core Fund II", "investment_amount_zar": 4500000,  "equity_pct": 23.5, "entry_year": 2022, "ytd_distribution_zar": 189000,  "total_distributions_zar": 378000,  "irr_pct": 9.2},
    {"investor_name": "Pinnacle Investments (Pty) Ltd","fund_name": "Core Fund II", "investment_amount_zar": 2000000,  "equity_pct": 10.5, "entry_year": 2023, "ytd_distribution_zar": 84000,   "total_distributions_zar": 126000,  "irr_pct": 9.8},
]


def gen_portfolio_rows() -> list[dict]:
    """18 months of aggregated portfolio-level data (Nov 2024 - Apr 2026)."""
    rows = []
    base_value = 155_000_000
    for i in range(18):
        yr = 2024 + (i + 10) // 12
        mo = ((i + 10) % 12) + 1
        dt = date(yr, mo, 1)
        growth = 1 + i * 0.004 + random.uniform(-0.002, 0.003)
        port_val = round(base_value * growth, 2)

        seasonal = 1.05 if mo in (3, 4, 10, 11) else 0.92 if mo in (6, 7) else 1.0
        gross = round((850_000 + i * 14_000) * seasonal * random.uniform(0.97, 1.03), 2)
        vac   = round(gross * random.uniform(0.04, 0.10), 2)
        net   = round(gross - vac, 2)
        opex  = round(net * random.uniform(0.26, 0.32), 2)
        maint = round(net * random.uniform(0.05, 0.09), 2)
        noi   = round(net - opex - maint, 2)
        debt  = round(noi * random.uniform(0.32, 0.40), 2)
        cf    = round(noi - debt, 2)
        occ   = round(random.uniform(84, 96), 2)
        total_units = 63
        occ_units   = int(total_units * occ / 100)

        rows.append({
            "month":                   dt.isoformat(),
            "portfolio_value_zar":     port_val,
            "gross_rental_income_zar": gross,
            "vacancy_loss_zar":        vac,
            "net_rental_income_zar":   net,
            "operating_expenses_zar":  opex,
            "maintenance_costs_zar":   maint,
            "noi_zar":                 noi,
            "debt_service_zar":        debt,
            "cash_flow_zar":           cf,
            "occupancy_rate_pct":      occ,
            "total_units":             total_units,
            "occupied_units":          occ_units,
        })
    return rows


def gen_financials_rows() -> list[dict]:
    """18 months × 7 active properties = 126 rows."""
    rows = []
    active = [p for p in PROPERTIES_DATA if p["status"] == "Active"]
    for i in range(18):
        yr = 2024 + (i + 10) // 12
        mo = ((i + 10) % 12) + 1
        dt = date(yr, mo, 1)
        for prop in active:
            cfg   = _PROP_CONFIG[prop["property_name"]]
            base  = cfg["base_rent"]
            occ_b = cfg["occ_base"]
            seasonal = 1.04 if mo in (3, 4, 10, 11) else 0.93 if mo in (6, 7) else 1.0
            gross    = round(base * seasonal * random.uniform(0.95, 1.05), 2)
            vac_rate = max(0, round(random.uniform(0, 15) - (occ_b - 80), 2))
            vac      = round(gross * (vac_rate / 100), 2)
            occ_pct  = round(min(100, occ_b + random.uniform(-4, 6)), 2)
            opex     = round((gross - vac) * random.uniform(0.24, 0.30), 2)
            maint    = round((gross - vac) * random.uniform(0.04, 0.09), 2)
            noi      = round(gross - vac - opex - maint, 2)
            rows.append({
                "month":                   dt.isoformat(),
                "property_name":           prop["property_name"],
                "property_type":           prop["property_type"],
                "fund_name":               prop["fund_name"],
                "gross_rental_income_zar": gross,
                "vacancy_loss_zar":        vac,
                "operating_expenses_zar":  opex,
                "maintenance_costs_zar":   maint,
                "noi_zar":                 noi,
                "occupancy_rate_pct":      occ_pct,
            })
    return rows


def gen_lease_rows() -> list[dict]:
    rows = []
    for t in LEASE_TENANTS:
        rows.append({
            "property_name":    t[0],
            "tenant_name":      t[1],
            "unit_ref":         t[2],
            "lease_start":      t[3],
            "lease_end":        t[4],
            "monthly_rent_zar": t[5],
            "escalation_pct":   t[6],
            "status":           t[7],
            "renewal_probability": t[8],
        })
    return rows


def gen_project_rows() -> list[dict]:
    return [{k: v for k, v in p.items()} for p in PROJECTS_DATA]


def gen_investor_rows() -> list[dict]:
    return [{k: v for k, v in inv.items()} for inv in INVESTORS_DATA]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SUPABASE TABLE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

TABLES = {
    "corevest_portfolio": {
        "id":                        "SERIAL PRIMARY KEY",
        "month":                     "DATE NOT NULL",
        "portfolio_value_zar":       "NUMERIC(18,2)",
        "gross_rental_income_zar":   "NUMERIC(14,2)",
        "vacancy_loss_zar":          "NUMERIC(14,2)",
        "net_rental_income_zar":     "NUMERIC(14,2)",
        "operating_expenses_zar":    "NUMERIC(14,2)",
        "maintenance_costs_zar":     "NUMERIC(14,2)",
        "noi_zar":                   "NUMERIC(14,2)",
        "debt_service_zar":          "NUMERIC(14,2)",
        "cash_flow_zar":             "NUMERIC(14,2)",
        "occupancy_rate_pct":        "NUMERIC(5,2)",
        "total_units":               "INTEGER",
        "occupied_units":            "INTEGER",
    },
    "corevest_properties": {
        "id":                  "SERIAL PRIMARY KEY",
        "property_name":       "TEXT NOT NULL",
        "property_type":       "TEXT",
        "suburb":              "TEXT",
        "city":                "TEXT",
        "acquisition_year":    "INTEGER",
        "acquisition_price_zar": "NUMERIC(16,2)",
        "current_value_zar":   "NUMERIC(16,2)",
        "gla_sqm":             "INTEGER",
        "total_units":         "INTEGER",
        "fund_name":           "TEXT",
        "status":              "TEXT",
    },
    "corevest_monthly_financials": {
        "id":                        "SERIAL PRIMARY KEY",
        "month":                     "DATE NOT NULL",
        "property_name":             "TEXT",
        "property_type":             "TEXT",
        "fund_name":                 "TEXT",
        "gross_rental_income_zar":   "NUMERIC(14,2)",
        "vacancy_loss_zar":          "NUMERIC(14,2)",
        "operating_expenses_zar":    "NUMERIC(14,2)",
        "maintenance_costs_zar":     "NUMERIC(14,2)",
        "noi_zar":                   "NUMERIC(14,2)",
        "occupancy_rate_pct":        "NUMERIC(5,2)",
    },
    "corevest_leases": {
        "id":                  "SERIAL PRIMARY KEY",
        "property_name":       "TEXT",
        "tenant_name":         "TEXT",
        "unit_ref":            "TEXT",
        "lease_start":         "DATE",
        "lease_end":           "DATE",
        "monthly_rent_zar":    "NUMERIC(12,2)",
        "escalation_pct":      "NUMERIC(5,2)",
        "status":              "TEXT",
        "renewal_probability": "TEXT",
    },
    "corevest_projects": {
        "id":                 "SERIAL PRIMARY KEY",
        "project_name":       "TEXT",
        "project_type":       "TEXT",
        "start_date":         "DATE",
        "target_completion":  "DATE",
        "budget_zar":         "NUMERIC(14,2)",
        "spent_zar":          "NUMERIC(14,2)",
        "completion_pct":     "NUMERIC(5,2)",
        "rag_status":         "TEXT",
        "contractor":         "TEXT",
        "notes":              "TEXT",
    },
    "corevest_investors": {
        "id":                        "SERIAL PRIMARY KEY",
        "investor_name":             "TEXT",
        "fund_name":                 "TEXT",
        "investment_amount_zar":     "NUMERIC(14,2)",
        "equity_pct":                "NUMERIC(6,2)",
        "entry_year":                "INTEGER",
        "ytd_distribution_zar":      "NUMERIC(12,2)",
        "total_distributions_zar":   "NUMERIC(14,2)",
        "irr_pct":                   "NUMERIC(5,2)",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. METABASE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _mb_token() -> str:
    if METABASE_API_KEY:
        return METABASE_API_KEY
    r = requests.post(f"{METABASE_URL}/api/session",
                      json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD}, timeout=15)
    r.raise_for_status()
    return r.json()["id"]


def _mb_headers(tok: str) -> dict:
    if tok.startswith("mb_"):
        return {"X-API-Key": tok, "Content-Type": "application/json"}
    return {"X-Metabase-Session": tok, "Content-Type": "application/json"}


def _admin_token() -> str:
    r = requests.post(f"{METABASE_URL}/api/session",
                      json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD}, timeout=15)
    r.raise_for_status()
    return r.json()["id"]


def _truncate_table(table_name: str) -> None:
    """Truncate a table via Supabase Management API so re-runs are idempotent."""
    _MGMT_BASE = "https://api.supabase.com/v1"
    url = f"{_MGMT_BASE}/projects/{SUPABASE_PROJECT_REF}/database/query"
    sql = f'TRUNCATE TABLE public."{table_name}" RESTART IDENTITY CASCADE;'
    resp = requests.post(url, headers=_mgmt_headers(), json={"query": sql}, timeout=30)
    if resp.status_code not in (200, 201):
        log.warning(f"Truncate '{table_name}' warning: {resp.text[:200]}")
    else:
        log.info(f"  Truncated '{table_name}'")


def _mb_call(method: str, url: str, tok: str, **kwargs) -> requests.Response:
    """Metabase API call with 3 retries on connection errors."""
    for attempt in range(3):
        try:
            fn = getattr(requests, method)
            r = fn(url, headers=_mb_headers(tok), timeout=25, **kwargs)
            return r
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == 2:
                raise
            log.warning(f"  Metabase {method.upper()} attempt {attempt+1} failed: {e}. Retrying in 5s...")
            time.sleep(5)


def mb_card(tok: str, db_id: int, name: str, sql: str,
            display: str = "scalar", viz: dict = None) -> int:
    payload = {
        "name": name,
        "dataset_query": {"type": "native", "database": db_id, "native": {"query": sql}},
        "display": display,
        "visualization_settings": viz or {},
    }
    r = _mb_call("post", f"{METABASE_URL}/api/card", tok, json=payload)
    if r.status_code not in (200, 202):
        raise RuntimeError(f"Card '{name}' failed [{r.status_code}]: {r.text[:300]}")
    cid = r.json()["id"]
    log.info(f"  Card '{name}' id={cid}")
    return cid


def mb_dashboard(tok: str, name: str, desc: str) -> int:
    r = requests.post(f"{METABASE_URL}/api/dashboard",
                      headers=_mb_headers(tok), json={"name": name, "description": desc}, timeout=15)
    r.raise_for_status()
    did = r.json()["id"]
    log.info(f"Dashboard '{name}' id={did}")
    return did


def mb_add_cards(tok: str, dash_id: int, kpi_ids: list, chart_ids: list):
    cards = []
    kw, kh = 4, 2
    for i, cid in enumerate(kpi_ids):
        cards.append({"id": -(i+1), "card_id": cid, "col": i*kw, "row": 0,
                      "size_x": kw, "size_y": kh,
                      "parameter_mappings": [], "visualization_settings": {}})
    cw, ch = 9, 6
    start = kh + 1
    for i, cid in enumerate(chart_ids):
        col = (i % 2) * cw
        row = start + (i // 2) * (ch + 1)
        cards.append({"id": -(len(kpi_ids)+i+1), "card_id": cid, "col": col, "row": row,
                      "size_x": cw, "size_y": ch,
                      "parameter_mappings": [], "visualization_settings": {}})
    r = _mb_call("put", f"{METABASE_URL}/api/dashboard/{dash_id}/cards", tok, json={"cards": cards})
    if r.status_code not in (200, 202):
        raise RuntimeError(f"add_cards failed: {r.text[:300]}")


def mb_public_link(dash_id: int) -> str:
    atk = _admin_token()
    ah  = {"X-Metabase-Session": atk, "Content-Type": "application/json"}
    r   = requests.post(f"{METABASE_URL}/api/dashboard/{dash_id}/public_link", headers=ah, timeout=15)
    if r.status_code not in (200, 202):
        raise RuntimeError(f"public_link failed: {r.text[:300]}")
    uuid = r.json()["uuid"]
    url  = f"{METABASE_URL}/public/dashboard/{uuid}"
    log.info(f"  Public URL: {url}")
    return url


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DASHBOARD BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_portfolio_dashboard(tok: str, db: int) -> str:
    log.info("Building Dashboard 1: Portfolio Overview...")
    T = "corevest_portfolio"
    kpis = [
        mb_card(tok, db, "Total Portfolio Value (Latest)", f'SELECT MAX("portfolio_value_zar") FROM public."{T}"'),
        mb_card(tok, db, "Latest Monthly NOI",             f'SELECT "noi_zar" FROM public."{T}" ORDER BY "month" DESC LIMIT 1'),
        mb_card(tok, db, "Portfolio Occupancy Rate (%)",   f'SELECT ROUND(AVG("occupancy_rate_pct")::numeric,1) FROM public."{T}"'),
        mb_card(tok, db, "Latest Gross Rental Income",     f'SELECT "gross_rental_income_zar" FROM public."{T}" ORDER BY "month" DESC LIMIT 1'),
    ]
    charts = [
        mb_card(tok, db, "NOI Trend (18 Months)",
                f'SELECT DATE_TRUNC(\'month\',"month") AS "Month", SUM("noi_zar") AS "NOI (R)" FROM public."{T}" GROUP BY 1 ORDER BY 1',
                "line", {"graph.dimensions": ["Month"], "graph.metrics": ["NOI (R)"]}),
        mb_card(tok, db, "Gross Rental Income Trend",
                f'SELECT DATE_TRUNC(\'month\',"month") AS "Month", SUM("gross_rental_income_zar") AS "Gross Rental (R)" FROM public."{T}" GROUP BY 1 ORDER BY 1',
                "line", {"graph.dimensions": ["Month"], "graph.metrics": ["Gross Rental (R)"]}),
        mb_card(tok, db, "Occupancy Rate Trend (%)",
                f'SELECT DATE_TRUNC(\'month\',"month") AS "Month", AVG("occupancy_rate_pct") AS "Occupancy (%)" FROM public."{T}" GROUP BY 1 ORDER BY 1',
                "line", {"graph.dimensions": ["Month"], "graph.metrics": ["Occupancy (%)"]}),
        mb_card(tok, db, "Cash Flow After Debt Service",
                f'SELECT DATE_TRUNC(\'month\',"month") AS "Month", SUM("cash_flow_zar") AS "Cash Flow (R)" FROM public."{T}" GROUP BY 1 ORDER BY 1',
                "line", {"graph.dimensions": ["Month"], "graph.metrics": ["Cash Flow (R)"]}),
    ]
    did = mb_dashboard(tok, "Corevest — Portfolio Overview", "Aggregate portfolio value, NOI, occupancy and cash flow trend across all properties.")
    mb_add_cards(tok, did, kpis, charts)
    return mb_public_link(did)


def build_financial_dashboard(tok: str, db: int) -> str:
    log.info("Building Dashboard 2: Financial Performance...")
    T = "corevest_monthly_financials"
    kpis = [
        mb_card(tok, db, "Total Gross Rental (YTD)",     f'SELECT SUM("gross_rental_income_zar") FROM public."{T}" WHERE "month" >= \'2026-01-01\''),
        mb_card(tok, db, "Total NOI (YTD)",              f'SELECT SUM("noi_zar") FROM public."{T}" WHERE "month" >= \'2026-01-01\''),
        mb_card(tok, db, "Total Vacancy Loss (YTD)",     f'SELECT SUM("vacancy_loss_zar") FROM public."{T}" WHERE "month" >= \'2026-01-01\''),
        mb_card(tok, db, "Total Maintenance Costs (YTD)",f'SELECT SUM("maintenance_costs_zar") FROM public."{T}" WHERE "month" >= \'2026-01-01\''),
    ]
    charts = [
        mb_card(tok, db, "NOI by Property (All Time)",
                f'SELECT "property_name" AS "Property", SUM("noi_zar") AS "Total NOI (R)" FROM public."{T}" GROUP BY 1 ORDER BY 2 DESC',
                "bar", {"graph.dimensions": ["Property"], "graph.metrics": ["Total NOI (R)"]}),
        mb_card(tok, db, "Monthly Gross Rental Trend",
                f'SELECT DATE_TRUNC(\'month\',"month") AS "Month", SUM("gross_rental_income_zar") AS "Gross Rental (R)" FROM public."{T}" GROUP BY 1 ORDER BY 1',
                "line", {"graph.dimensions": ["Month"], "graph.metrics": ["Gross Rental (R)"]}),
        mb_card(tok, db, "Maintenance Costs by Property",
                f'SELECT "property_name" AS "Property", SUM("maintenance_costs_zar") AS "Maintenance (R)" FROM public."{T}" GROUP BY 1 ORDER BY 2 DESC',
                "bar", {"graph.dimensions": ["Property"], "graph.metrics": ["Maintenance (R)"]}),
        mb_card(tok, db, "Vacancy Loss Trend",
                f'SELECT DATE_TRUNC(\'month\',"month") AS "Month", SUM("vacancy_loss_zar") AS "Vacancy Loss (R)" FROM public."{T}" GROUP BY 1 ORDER BY 1',
                "line", {"graph.dimensions": ["Month"], "graph.metrics": ["Vacancy Loss (R)"]}),
    ]
    did = mb_dashboard(tok, "Corevest — Financial Performance", "YTD income, NOI, vacancy loss and maintenance broken down by property and month.")
    mb_add_cards(tok, did, kpis, charts)
    return mb_public_link(did)


def build_lease_dashboard(tok: str, db: int) -> str:
    log.info("Building Dashboard 3: Lease Management...")
    T = "corevest_leases"
    kpis = [
        mb_card(tok, db, "Active Leases",
                f'SELECT COUNT(*) FROM public."{T}" WHERE "status" = \'Active\''),
        mb_card(tok, db, "Expiring Within 90 Days",
                f"SELECT COUNT(*) FROM public.\"{T}\" WHERE \"status\"='Active' AND \"lease_end\" <= CURRENT_DATE + INTERVAL '90 days'"),
        mb_card(tok, db, "Total Monthly Rent Roll (R)",
                f'SELECT SUM("monthly_rent_zar") FROM public."{T}" WHERE "status" = \'Active\''),
        mb_card(tok, db, "Leases at Risk (Low Renewal)",
                f"SELECT COUNT(*) FROM public.\"{T}\" WHERE \"renewal_probability\"='Low' AND \"status\"='Active'"),
    ]
    charts = [
        mb_card(tok, db, "Monthly Rent Roll by Property",
                f'SELECT "property_name" AS "Property", SUM("monthly_rent_zar") AS "Rent Roll (R)" FROM public."{T}" WHERE "status"=\'Active\' GROUP BY 1 ORDER BY 2 DESC',
                "bar", {"graph.dimensions": ["Property"], "graph.metrics": ["Rent Roll (R)"]}),
        mb_card(tok, db, "Lease Renewal Probability Distribution",
                f'SELECT "renewal_probability" AS "Probability", COUNT(*) AS "Leases" FROM public."{T}" WHERE "status"=\'Active\' GROUP BY 1',
                "bar", {"graph.dimensions": ["Probability"], "graph.metrics": ["Leases"]}),
        mb_card(tok, db, "Rent Roll by Property Type",
                f'SELECT p."property_type" AS "Type", SUM(l."monthly_rent_zar") AS "Rent Roll (R)" FROM public."{T}" l JOIN public."corevest_properties" p ON l."property_name"=p."property_name" WHERE l."status"=\'Active\' GROUP BY 1 ORDER BY 2 DESC',
                "bar", {"graph.dimensions": ["Type"], "graph.metrics": ["Rent Roll (R)"]}),
        mb_card(tok, db, "Escalation Rate Distribution",
                f'SELECT ROUND("escalation_pct"::numeric,1)::text || \'%\' AS "Escalation", COUNT(*) AS "Leases" FROM public."{T}" WHERE "status"=\'Active\' GROUP BY 1 ORDER BY 1',
                "bar", {"graph.dimensions": ["Escalation"], "graph.metrics": ["Leases"]}),
    ]
    did = mb_dashboard(tok, "Corevest — Lease Management", "Active leases, expiry risk, rent roll by property, and renewal probability tracking.")
    mb_add_cards(tok, did, kpis, charts)
    return mb_public_link(did)


def build_projects_dashboard(tok: str, db: int) -> str:
    log.info("Building Dashboard 4: Development Projects...")
    T = "corevest_projects"
    kpis = [
        mb_card(tok, db, "Total Active Projects",
                f'SELECT COUNT(*) FROM public."{T}" WHERE "rag_status" != \'Complete\''),
        mb_card(tok, db, "Total Budget (R)",
                f'SELECT SUM("budget_zar") FROM public."{T}"'),
        mb_card(tok, db, "Total Spent to Date (R)",
                f'SELECT SUM("spent_zar") FROM public."{T}"'),
        mb_card(tok, db, "Projects Over Budget",
                f'SELECT COUNT(*) FROM public."{T}" WHERE "spent_zar" > "budget_zar"'),
    ]
    charts = [
        mb_card(tok, db, "Budget vs Spent by Project",
                f'SELECT "project_name" AS "Project", "budget_zar" AS "Budget (R)" FROM public."{T}" ORDER BY "budget_zar" DESC',
                "bar", {"graph.dimensions": ["Project"], "graph.metrics": ["Budget (R)"]}),
        mb_card(tok, db, "Spend to Date by Project",
                f'SELECT "project_name" AS "Project", "spent_zar" AS "Spent (R)" FROM public."{T}" ORDER BY "spent_zar" DESC',
                "bar", {"graph.dimensions": ["Project"], "graph.metrics": ["Spent (R)"]}),
        mb_card(tok, db, "Completion % by Project",
                f'SELECT "project_name" AS "Project", "completion_pct" AS "Complete (%)" FROM public."{T}" ORDER BY "completion_pct" DESC',
                "bar", {"graph.dimensions": ["Project"], "graph.metrics": ["Complete (%)"]}),
        mb_card(tok, db, "Project Status Overview",
                f'SELECT "rag_status" AS "Status", COUNT(*) AS "Projects" FROM public."{T}" GROUP BY 1',
                "bar", {"graph.dimensions": ["Status"], "graph.metrics": ["Projects"]}),
    ]
    did = mb_dashboard(tok, "Corevest — Development Projects", "Budget vs spend, completion percentage, and RAG status for all development and renovation projects.")
    mb_add_cards(tok, did, kpis, charts)
    return mb_public_link(did)


def build_investor_dashboard(tok: str, db: int) -> str:
    log.info("Building Dashboard 5: Investor Reporting...")
    T = "corevest_investors"
    kpis = [
        mb_card(tok, db, "Total Assets Under Management (R)",
                f'SELECT SUM("investment_amount_zar") FROM public."{T}"'),
        mb_card(tok, db, "Total YTD Distributions (R)",
                f'SELECT SUM("ytd_distribution_zar") FROM public."{T}"'),
        mb_card(tok, db, "Average IRR (%)",
                f'SELECT ROUND(AVG("irr_pct")::numeric,2) FROM public."{T}"'),
        mb_card(tok, db, "Total Investors",
                f'SELECT COUNT(*) FROM public."{T}"'),
    ]
    charts = [
        mb_card(tok, db, "IRR by Investor (%)",
                f'SELECT "investor_name" AS "Investor", "irr_pct" AS "IRR (%)" FROM public."{T}" ORDER BY "irr_pct" DESC',
                "bar", {"graph.dimensions": ["Investor"], "graph.metrics": ["IRR (%)"]}),
        mb_card(tok, db, "YTD Distributions by Investor (R)",
                f'SELECT "investor_name" AS "Investor", "ytd_distribution_zar" AS "YTD Distributions (R)" FROM public."{T}" ORDER BY 2 DESC',
                "bar", {"graph.dimensions": ["Investor"], "graph.metrics": ["YTD Distributions (R)"]}),
        mb_card(tok, db, "Investment Amount by Fund",
                f'SELECT "fund_name" AS "Fund", SUM("investment_amount_zar") AS "Investment (R)" FROM public."{T}" GROUP BY 1',
                "bar", {"graph.dimensions": ["Fund"], "graph.metrics": ["Investment (R)"]}),
        mb_card(tok, db, "Total Distributions Paid by Investor",
                f'SELECT "investor_name" AS "Investor", "total_distributions_zar" AS "Total Distributions (R)" FROM public."{T}" ORDER BY 2 DESC',
                "bar", {"graph.dimensions": ["Investor"], "graph.metrics": ["Total Distributions (R)"]}),
    ]
    did = mb_dashboard(tok, "Corevest — Investor Reporting", "AUM, IRR performance, YTD distributions and total payouts per investor and fund.")
    mb_add_cards(tok, did, kpis, charts)
    return mb_public_link(did)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PDF REPORT GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_pdf_data(subtitle: str, rows: list, kpi_cols: list, report_cards: list) -> dict:
    return {
        "reporting_subtitle": subtitle,
        "rows":        rows,
        "kpi_metrics": kpi_cols,
        "report_cards": report_cards,
    }


def gen_portfolio_pdf(port_rows: list, dash_url: str) -> bytes:
    data = _make_pdf_data(
        "18-month aggregated portfolio performance across 8 properties — Western Cape",
        port_rows,
        [("noi_zar","Monthly NOI (R)"),("gross_rental_income_zar","Gross Rental (R)"),
         ("occupancy_rate_pct","Occupancy (%)")],
        [{"title": "Portfolio occupancy averaged 91% over 18 months",
          "desc": "Claremont Office Park and Kenilworth Commercial Hub drove the strongest NOI contributions. Rondebosch Residential maintained the highest occupancy at 94%+."},
         {"title": "NOI grew 18% over the reporting period",
          "desc": "Sustained rental escalations of 7.5-9% per annum combined with stable occupancy drove consistent NOI growth from R550k to R650k/month."},
         {"title": "Vacancy loss contained below 8% across the portfolio",
          "desc": "Active lease management and proactive renewal negotiations kept vacancy below the 8% threshold, outperforming the Cape Town commercial market average of 11.2%."},
         {"title": "Cash flow after debt service remains positive every month",
          "desc": "Debt service coverage ratio averaged 1.62x across all properties, well above the covenant threshold of 1.25x."}]
    )
    return generate_pdf("Corevest — Monthly Portfolio Performance", data, dash_url)


def gen_investor_pdf(inv_rows: list, dash_url: str) -> bytes:
    data = _make_pdf_data(
        "Quarterly investor distribution summary — Core Fund I & II — Q1 2026",
        inv_rows,
        [("investment_amount_zar","Investment (R)"),("ytd_distribution_zar","YTD Distributions (R)"),
         ("irr_pct","IRR (%)")],
        [{"title": "Stellenbosch Family Office leads with 14.8% IRR",
          "desc": "Core Fund I has delivered consistently above the prime lending rate, averaging 13.1% IRR across all investors since 2017 inception."},
         {"title": "Q1 2026 total distributions: R1,465,500",
          "desc": "Distributions were paid on schedule on 31 March 2026 to all 6 investors. No distribution was deferred or reduced."},
         {"title": "Core Fund II IRR range: 9.2% — 10.2%",
          "desc": "Core Fund II is in its growth phase — IRR is expected to improve as the Salt River development project completes and stabilises in 2027."},
         {"title": "AUM grown to R29.0M across both funds",
          "desc": "Total investor capital under management increased R2.5M year-on-year due to reinvestment of retained income and appreciation in property valuations."}]
    )
    return generate_pdf("Corevest — Quarterly Investor Report", data, dash_url)


def gen_lease_pdf(lease_rows: list, dash_url: str) -> bytes:
    data = _make_pdf_data(
        "Lease expiry risk, rent roll by property, and renewal probability — May 2026",
        lease_rows,
        [("monthly_rent_zar","Monthly Rent (R)"),("escalation_pct","Escalation (%)"),
         ("renewal_probability","Renewal Probability")],
        [{"title": "3 leases expiring within 90 days — action required",
          "desc": "L. van der Merwe (Rondebosch Apt 2 — May 2026), Observatory Capsule Gym (Apr 2026), and PrimeTech Logistics Bay A (Mar 2026) are critical renewals. Low renewal probability flagged."},
         {"title": "Total active rent roll: R367,600/month",
          "desc": "Monthly rent roll across all active leases. Kenilworth Commercial Hub contributes the highest rent roll at R57,300/month across 3 occupied bays."},
         {"title": "6 leases have Low renewal probability — requires engagement",
          "desc": "Recommend scheduling retention meetings within 30 days. Estimated at-risk income: R94,500/month if all Low-probability tenants vacate."},
         {"title": "Average lease escalation is 8.1% across the portfolio",
          "desc": "All leases are indexed at 7.0-9.0% annual escalation. No below-inflation leases exist in the current portfolio."}]
    )
    return generate_pdf("Corevest — Lease Expiry Risk Report", data, dash_url)


def gen_projects_pdf(proj_rows: list, dash_url: str) -> bytes:
    data = _make_pdf_data(
        "Development and renovation project tracker — budget vs spend, RAG status — May 2026",
        proj_rows,
        [("budget_zar","Budget (R)"),("spent_zar","Spent (R)"),
         ("completion_pct","Completion (%)")],
        [{"title": "Salt River Mixed-Use: 40% complete, on track for Q1 2027",
          "desc": "Foundation and structural phase are complete. R9.8M of R24.5M budget spent. No delays reported. Next milestone: slab pour scheduled June 2026."},
         {"title": "Kenilworth Roof Refurbishment: R270k over budget",
          "desc": "Scope expansion to add a waterproofing membrane layer increased costs. Project 95% complete. Recommend reviewing contractor contract terms for scope change management."},
         {"title": "Observatory Solar: 55% complete, on budget",
          "desc": "Panel installation complete. Inverter wiring and grid tie-in planned for June. Expected payback period: 4.2 years at current Eskom tariffs."},
         {"title": "Wynberg Expansion: planning phase, tender Q3 2026",
          "desc": "Town planning approval received. Tender documents being finalised. Construction expected to begin September 2026 pending contractor appointment."}]
    )
    return generate_pdf("Corevest — Development Projects Report", data, dash_url)


def gen_annual_pdf(port_rows: list, inv_rows: list, dash_url: str) -> bytes:
    combined = port_rows[-12:]
    data = _make_pdf_data(
        "Annual fund performance summary — FY2025/26 — Core Fund I & II",
        combined,
        [("portfolio_value_zar","Portfolio Value (R)"),("noi_zar","Annual NOI (R)"),
         ("occupancy_rate_pct","Occupancy (%)")],
        [{"title": "Portfolio value grew from R155M to R165M over FY2025/26",
          "desc": "Capital appreciation driven by Constantia Upper Residential (+7.2%) and Kenilworth Commercial Hub (+5.8%). Portfolio total return including income distributions: 12.4%."},
         {"title": "Annual NOI: R7.8M across all active properties",
          "desc": "Net Operating Income increased from R6.6M in FY2024/25 to R7.8M — an 18.2% improvement, driven by escalations and improved occupancy management."},
         {"title": "Total investor distributions paid FY2025/26: R5.9M",
          "desc": "All distributions paid on time across Core Fund I and Core Fund II. Weighted average distribution yield: 11.8% on invested capital."},
         {"title": "Outlook: Salt River project adds R22M to portfolio on completion",
          "desc": "Once stabilised, the Salt River Mixed-Use Development is projected to contribute R1.8M NOI per annum, increasing total portfolio NOI by 23%."}]
    )
    return generate_pdf("Corevest — Annual Fund Performance Summary", data, dash_url)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. HTML PORTAL
# ═══════════════════════════════════════════════════════════════════════════════

def build_html(dash_urls: dict, pdf_urls: dict) -> str:
    d1 = dash_urls["portfolio"]
    d2 = dash_urls["financial"]
    d3 = dash_urls["lease"]
    d4 = dash_urls["projects"]
    d5 = dash_urls["investor"]

    p1 = pdf_urls.get("portfolio",  "#")
    p2 = pdf_urls.get("investor",   "#")
    p3 = pdf_urls.get("lease",      "#")
    p4 = pdf_urls.get("projects",   "#")
    p5 = pdf_urls.get("annual",     "#")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Corevest | Cho&amp;Co Analytics Portal</title>
  <link rel="icon" type="image/png" sizes="128x128" href="https://raw.githubusercontent.com/TawandaAfeki/CC/main/fav.webp"/>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --navy:#0D1B40;--navy2:#162254;
  --gold:#C19A4F;--gold-lt:#f5eddc;
  --teal:#2A9D8F;--teal-lt:#e6f5f3;
  --coal:#3D4756;--coal-lt:#f0f1f3;
  --paper:#f7f6f3;--paper2:#eceae4;
  --ink:#2b3340;--ink2:#4a5568;--ink3:#718096;
  --white:#fdfcfa;
  --serif:'DM Serif Display',Georgia,serif;
  --sans:'DM Sans',system-ui,sans-serif;
}}
body{{font-family:var(--sans);background:var(--paper);color:var(--ink)}}
input[name="tab"]{{display:none}}
input[name="dtab"]{{display:none}}

/* NAV */
.nav{{background:var(--navy);border-bottom:3px solid var(--gold);display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:52px;position:sticky;top:0;z-index:10}}
.nav-brand{{display:flex;align-items:center;gap:10px}}
.lm{{width:28px;height:28px;border-radius:50%;display:grid;grid-template-columns:1fr 1fr;gap:2px;overflow:hidden}}
.lm div:nth-child(1){{background:var(--teal)}}.lm div:nth-child(2){{background:var(--gold)}}
.lm div:nth-child(3){{background:var(--navy2)}}.lm div:nth-child(4){{background:#E8622A}}
.brand-txt{{font-family:var(--serif);font-size:17px;font-weight:700;color:var(--white)}}
.brand-txt span{{color:var(--gold)}}
.client-tag{{font-size:9px;color:rgba(255,255,255,.45);letter-spacing:.12em;text-transform:uppercase;border-left:1px solid rgba(255,255,255,.15);padding-left:10px}}
.nav-tabs{{display:flex;gap:2px}}
.tab-label{{display:inline-block;padding:7px 16px;border-radius:4px;font-size:12px;color:rgba(255,255,255,.45);cursor:pointer;transition:all .18s;user-select:none}}
.tab-label:hover{{color:var(--white);background:rgba(255,255,255,.07)}}
#t-home:checked  ~ .shell .nav-tabs label[for="t-home"],
#t-dash:checked  ~ .shell .nav-tabs label[for="t-dash"],
#t-rep:checked   ~ .shell .nav-tabs label[for="t-rep"],
#t-help:checked  ~ .shell .nav-tabs label[for="t-help"]{{color:var(--white);background:var(--gold);color:var(--navy)}}
.ndot{{display:flex;align-items:center;gap:6px;font-size:10px;color:rgba(255,255,255,.3)}}
.dot{{width:6px;height:6px;border-radius:50%;background:var(--gold);box-shadow:0 0 0 2px rgba(193,154,79,.2)}}

/* PAGES */
.page{{display:none;min-height:calc(100vh - 52px)}}
#t-home:checked ~ .shell .page-home,
#t-dash:checked ~ .shell .page-dash,
#t-rep:checked  ~ .shell .page-rep,
#t-help:checked ~ .shell .page-help{{display:block}}
#t-home:checked ~ .shell .page-home{{display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--navy);position:relative;overflow:hidden;padding:40px 20px;text-align:center;min-height:calc(100vh - 52px)}}

/* HOME */
.bg-quad{{position:absolute;inset:0;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;pointer-events:none;opacity:.08}}
.bg-quad div:nth-child(1){{background:var(--teal)}}.bg-quad div:nth-child(2){{background:var(--gold)}}
.bg-quad div:nth-child(3){{background:#E8622A}}.bg-quad div:nth-child(4){{background:#a8b2c4}}
.hero{{position:relative;z-index:1;max-width:680px}}
.client-badge{{display:inline-block;background:rgba(193,154,79,.15);border:1px solid rgba(193,154,79,.4);color:var(--gold);font-size:10px;letter-spacing:.12em;text-transform:uppercase;padding:4px 14px;border-radius:20px;margin-bottom:20px}}
.hero h1{{font-family:var(--serif);font-size:clamp(32px,5vw,56px);color:var(--white);line-height:1.15;margin-bottom:16px}}
.hero h1 em{{color:var(--gold);font-style:normal}}
.hero p{{font-size:15px;color:rgba(255,255,255,.6);line-height:1.7;margin-bottom:32px;max-width:520px;margin-left:auto;margin-right:auto}}
.hero-btns{{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}}
.btn-gold{{background:var(--gold);color:var(--navy);padding:11px 26px;border-radius:6px;font-weight:500;font-size:13px;cursor:pointer;border:none;letter-spacing:.03em;transition:opacity .15s}}
.btn-ghost{{background:transparent;color:var(--white);padding:11px 26px;border-radius:6px;font-weight:400;font-size:13px;cursor:pointer;border:1px solid rgba(255,255,255,.2);letter-spacing:.03em;transition:all .15s}}
.btn-ghost:hover{{border-color:rgba(255,255,255,.5)}}
.kpi-strip{{display:flex;gap:1px;background:rgba(255,255,255,.06);border-radius:10px;overflow:hidden;margin-top:48px;width:100%;max-width:620px}}
.kpi-item{{flex:1;padding:18px 12px;text-align:center;background:rgba(0,0,0,.18)}}
.kpi-val{{font-family:var(--serif);font-size:22px;color:var(--gold);display:block}}
.kpi-lbl{{font-size:9px;color:rgba(255,255,255,.4);letter-spacing:.1em;text-transform:uppercase;margin-top:4px;display:block}}

/* DASHBOARD PAGE */
.dash-header{{background:var(--navy);padding:20px 28px 0;border-bottom:1px solid rgba(255,255,255,.07)}}
.dash-header h2{{font-family:var(--serif);font-size:20px;color:var(--white);margin-bottom:14px}}
.dtab-bar{{display:flex;gap:4px;overflow-x:auto;padding-bottom:0}}
.dtab-label{{display:inline-block;padding:8px 18px;border-radius:6px 6px 0 0;font-size:12px;color:rgba(255,255,255,.45);cursor:pointer;transition:all .18s;user-select:none;white-space:nowrap;border:1px solid transparent;border-bottom:none}}
.dtab-label:hover{{color:var(--white);background:rgba(255,255,255,.07)}}
#d1:checked ~ .shell .page-dash label[for="d1"],
#d2:checked ~ .shell .page-dash label[for="d2"],
#d3:checked ~ .shell .page-dash label[for="d3"],
#d4:checked ~ .shell .page-dash label[for="d4"],
#d5:checked ~ .shell .page-dash label[for="d5"]{{color:var(--navy);background:var(--gold);border-color:var(--gold)}}
.dash-frame{{display:none}}
#d1:checked ~ .shell .page-dash .df1,
#d2:checked ~ .shell .page-dash .df2,
#d3:checked ~ .shell .page-dash .df3,
#d4:checked ~ .shell .page-dash .df4,
#d5:checked ~ .shell .page-dash .df5{{display:block}}
.dash-frame iframe{{width:100%;height:calc(100vh - 160px);border:none;display:block}}

/* REPORTS PAGE */
.rep-header{{padding:28px 28px 16px;background:var(--white);border-bottom:1px solid var(--paper2)}}
.rep-header h2{{font-family:var(--serif);font-size:24px;color:var(--navy);margin-bottom:6px}}
.rep-header p{{font-size:13px;color:var(--ink3)}}
.rgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;padding:24px 28px}}
.rcard{{background:var(--white);border-radius:10px;border:1px solid var(--paper2);padding:20px;cursor:pointer;transition:all .18s;position:relative;overflow:hidden}}
.rcard:hover{{box-shadow:0 4px 20px rgba(13,27,64,.1);transform:translateY(-2px)}}
.rcard::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px}}
.rcard.gold::before{{background:var(--gold)}}
.rcard.teal::before{{background:var(--teal)}}
.rcard.navy::before{{background:var(--navy)}}
.rcard.rust::before{{background:#E8622A}}
.rcard.purple::before{{background:#7B61FF}}
.rtype{{font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink3);margin-bottom:10px;font-weight:500}}
.rtitle{{font-family:var(--serif);font-size:15px;color:var(--navy);margin-bottom:8px;line-height:1.4}}
.rdesc{{font-size:12px;color:var(--ink3);line-height:1.6;margin-bottom:14px}}
.rmeta{{display:flex;align-items:center;justify-content:space-between}}
.rper{{font-size:10px;color:var(--ink3)}}
.rst{{font-size:9px;padding:3px 10px;border-radius:20px;letter-spacing:.06em;text-transform:uppercase;font-weight:500}}
.st-ready{{background:var(--teal-lt);color:var(--teal)}}
.st-draft{{background:var(--gold-lt);color:#8a6a1a}}
.download-ico{{font-size:18px;opacity:.5}}

/* HELP PAGE */
.help-grid{{display:grid;grid-template-columns:240px 1fr}}
.help-sidebar{{background:var(--navy);padding:28px 20px;min-height:calc(100vh - 52px)}}
.help-sidebar h3{{font-family:var(--serif);font-size:14px;color:var(--gold);margin-bottom:16px;letter-spacing:.04em}}
.help-nav-item{{display:block;padding:8px 12px;border-radius:6px;font-size:12px;color:rgba(255,255,255,.5);margin-bottom:4px;cursor:default}}
.help-nav-item.active{{background:rgba(193,154,79,.15);color:var(--gold)}}
.help-content{{padding:32px;background:var(--paper)}}
.help-content h2{{font-family:var(--serif);font-size:22px;color:var(--navy);margin-bottom:6px}}
.help-content > p{{font-size:13px;color:var(--ink3);margin-bottom:28px}}
.faq{{max-width:700px}}
.fi{{border:1px solid var(--paper2);border-radius:8px;margin-bottom:10px;background:var(--white);overflow:hidden}}
.fq{{width:100%;background:none;border:none;padding:14px 16px;text-align:left;font-family:var(--sans);font-size:13px;color:var(--navy);cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-weight:500}}
.fq:hover{{background:var(--paper)}}
.farr{{transition:transform .2s;color:var(--gold);font-size:11px}}
.fa{{display:none;padding:0 16px 14px;font-size:12px;color:var(--ink3);line-height:1.7}}
.fa.open{{display:block}}
.contact-box{{background:var(--navy);color:var(--white);border-radius:10px;padding:24px;margin-top:28px;max-width:700px}}
.contact-box h3{{font-family:var(--serif);font-size:16px;color:var(--gold);margin-bottom:12px}}
.contact-box p{{font-size:12px;color:rgba(255,255,255,.6);line-height:1.7}}
.contact-box a{{color:var(--gold);text-decoration:none}}
</style>
</head>
<body>

<!-- Main tab radios -->
<input type="radio" name="tab" id="t-home" checked>
<input type="radio" name="tab" id="t-dash">
<input type="radio" name="tab" id="t-rep">
<input type="radio" name="tab" id="t-help">

<!-- Dashboard sub-tab radios -->
<input type="radio" name="dtab" id="d1" checked>
<input type="radio" name="dtab" id="d2">
<input type="radio" name="dtab" id="d3">
<input type="radio" name="dtab" id="d4">
<input type="radio" name="dtab" id="d5">

<div class="shell">
  <!-- NAV -->
  <nav class="nav">
    <div class="nav-brand">
      <div class="lm"><div></div><div></div><div></div><div></div></div>
      <span class="brand-txt">Cho<span>&</span>Co</span>
      <span class="client-tag">Corevest (Pty) Ltd &nbsp;|&nbsp; Property Intelligence</span>
    </div>
    <div class="nav-tabs">
      <label class="tab-label" for="t-home">Home</label>
      <label class="tab-label" for="t-dash">Dashboards</label>
      <label class="tab-label" for="t-rep">Reports</label>
      <label class="tab-label" for="t-help">Support</label>
    </div>
    <div class="ndot"><div class="dot"></div> Live</div>
  </nav>

  <!-- ── HOME ── -->
  <div class="page page-home">
    <div class="bg-quad"><div></div><div></div><div></div><div></div></div>
    <div class="hero">
      <span class="client-badge">Corevest (Pty) Ltd &nbsp;·&nbsp; Western Cape Portfolio</span>
      <h1>Your Property Portfolio.<br><em>Fully Visible.</em></h1>
      <p>Real-time dashboards across all 8 properties — portfolio value, NOI, occupancy, lease expiry, development projects and investor performance. No spreadsheets. No delays.</p>
      <div class="hero-btns">
        <label class="btn-gold" for="t-dash">View Dashboards</label>
        <label class="btn-ghost" for="t-rep">Download Reports</label>
      </div>
      <div class="kpi-strip">
        <div class="kpi-item"><span class="kpi-val">R165M+</span><span class="kpi-lbl">Portfolio Value</span></div>
        <div class="kpi-item"><span class="kpi-val">8</span><span class="kpi-lbl">Properties</span></div>
        <div class="kpi-item"><span class="kpi-val">91%</span><span class="kpi-lbl">Avg Occupancy</span></div>
        <div class="kpi-item"><span class="kpi-val">R7.8M</span><span class="kpi-lbl">Annual NOI</span></div>
        <div class="kpi-item"><span class="kpi-val">13.1%</span><span class="kpi-lbl">Avg IRR</span></div>
      </div>
    </div>
  </div>

  <!-- ── DASHBOARDS ── -->
  <div class="page page-dash">
    <div class="dash-header">
      <h2>Live Analytics Dashboards</h2>
      <div class="dtab-bar">
        <label class="dtab-label" for="d1">&#9632; Portfolio Overview</label>
        <label class="dtab-label" for="d2">&#9632; Financial Performance</label>
        <label class="dtab-label" for="d3">&#9632; Lease Management</label>
        <label class="dtab-label" for="d4">&#9632; Development Projects</label>
        <label class="dtab-label" for="d5">&#9632; Investor Reporting</label>
      </div>
    </div>
    <div class="dash-frame df1"><iframe src="{d1}" allowfullscreen></iframe></div>
    <div class="dash-frame df2"><iframe src="{d2}" allowfullscreen></iframe></div>
    <div class="dash-frame df3"><iframe src="{d3}" allowfullscreen></iframe></div>
    <div class="dash-frame df4"><iframe src="{d4}" allowfullscreen></iframe></div>
    <div class="dash-frame df5"><iframe src="{d5}" allowfullscreen></iframe></div>
  </div>

  <!-- ── REPORTS ── -->
  <div class="page page-rep">
    <div class="rep-header">
      <h2>Reports &amp; Analytics Documents</h2>
      <p>Branded, investor-ready PDF reports — generated from your live data. Click any report to open or download.</p>
    </div>
    <div class="rgrid">
      <div class="rcard gold" onclick="window.open('{p1}','_blank')">
        <div class="rtype">Portfolio Report</div>
        <div class="rtitle">Monthly Portfolio Performance Report — May 2026</div>
        <div class="rdesc">18-month NOI trend, gross rental income, occupancy rate, cash flow after debt service, and vacancy analysis across all properties.</div>
        <div class="rmeta"><span class="rper">Nov 2024 – Apr 2026</span><span class="rst st-ready">&#8595; Ready</span></div>
      </div>
      <div class="rcard teal" onclick="window.open('{p2}','_blank')">
        <div class="rtype">Investor Report</div>
        <div class="rtitle">Quarterly Investor Distribution Report — Q1 2026</div>
        <div class="rdesc">IRR by investor, YTD distributions, AUM summary, fund performance vs benchmark for Core Fund I and Core Fund II.</div>
        <div class="rmeta"><span class="rper">Jan – Mar 2026</span><span class="rst st-ready">&#8595; Ready</span></div>
      </div>
      <div class="rcard rust" onclick="window.open('{p3}','_blank')">
        <div class="rtype">Risk Report</div>
        <div class="rtitle">Lease Expiry Risk Report — May 2026</div>
        <div class="rdesc">Leases expiring within 30/60/90 days, renewal probability by tenant, income at risk, and recommended retention actions.</div>
        <div class="rmeta"><span class="rper">May 2026</span><span class="rst st-ready">&#8595; Ready</span></div>
      </div>
      <div class="rcard navy" onclick="window.open('{p4}','_blank')">
        <div class="rtype">Project Report</div>
        <div class="rtitle">Development Projects Status Report — May 2026</div>
        <div class="rdesc">Budget vs spend, completion %, RAG status, contractor notes, and revised forecasts for all 5 active development and renovation projects.</div>
        <div class="rmeta"><span class="rper">May 2026</span><span class="rst st-ready">&#8595; Ready</span></div>
      </div>
      <div class="rcard purple" onclick="window.open('{p5}','_blank')">
        <div class="rtype">Annual Summary</div>
        <div class="rtitle">Annual Fund Performance Summary — FY2025/26</div>
        <div class="rdesc">Full-year portfolio return, capital growth, total distributions, IRR vs benchmark, occupancy trend, and FY2026/27 outlook.</div>
        <div class="rmeta"><span class="rper">Apr 2025 – Mar 2026</span><span class="rst st-draft">&#8861; Draft</span></div>
      </div>
    </div>
  </div>

  <!-- ── HELP ── -->
  <div class="page page-help">
    <div class="help-grid">
      <div class="help-sidebar">
        <h3>Support</h3>
        <span class="help-nav-item active">FAQ</span>
        <span class="help-nav-item">Data Updates</span>
        <span class="help-nav-item">Contact Cho&amp;Co</span>
      </div>
      <div class="help-content">
        <h2>Frequently Asked Questions</h2>
        <p>Everything you need to know about your Corevest analytics portal.</p>
        <div class="faq">
          <div class="fi"><button class="fq" onclick="tf(this)">How often does the dashboard data refresh? <span class="farr">&#9660;</span></button><div class="fa">Your dashboards connect directly to the Supabase database. Data updates automatically within minutes of a new data file being processed. You can also request a manual refresh by emailing info@choandco.co.za.</div></div>
          <div class="fi"><button class="fq" onclick="tf(this)">How do I submit new monthly data for processing? <span class="farr">&#9660;</span></button><div class="fa">Send your monthly export (Excel or CSV) from your property management system to info@choandco.co.za. Cho&Co processes, cleans and uploads the data within 1 business day. Your dashboard will reflect the new data automatically.</div></div>
          <div class="fi"><button class="fq" onclick="tf(this)">Can I add more properties or change the property list? <span class="farr">&#9660;</span></button><div class="fa">Yes. Email info@choandco.co.za with the new property details. We will update the database and reconfigure the affected dashboards within 2 business days. There is no additional charge for this within your current plan.</div></div>
          <div class="fi"><button class="fq" onclick="tf(this)">Who can access this portal and the underlying data? <span class="farr">&#9660;</span></button><div class="fa">Your data is stored in a dedicated Supabase project with row-level security enabled. Only Cho&Co staff assigned to your account and users you explicitly authorise can access the database. The portal links are shared only with you.</div></div>
          <div class="fi"><button class="fq" onclick="tf(this)">Can I share dashboard links with my investors? <span class="farr">&#9660;</span></button><div class="fa">Yes. Each dashboard has a unique public link that can be shared without requiring a login. You can share Dashboard 5 (Investor Reporting) directly with your investors. If you need a private, password-protected view, contact us to set up restricted access.</div></div>
          <div class="fi"><button class="fq" onclick="tf(this)">Can I get custom reports not listed here? <span class="farr">&#9660;</span></button><div class="fa">Absolutely. Contact info@choandco.co.za with the specific metrics, date range, and format you need. Custom reports are typically delivered within 2 business days. Examples include agent-level performance reports, area market analyses, and individual investor statements.</div></div>
          <div class="fi"><button class="fq" onclick="tf(this)">What happens if a figure looks incorrect in the dashboard? <span class="farr">&#9660;</span></button><div class="fa">First check your source data file for the relevant month. If the source is correct but the dashboard shows a different value, email info@choandco.co.za with a screenshot and the expected value. We will investigate and correct within 4 business hours.</div></div>
        </div>
        <div class="contact-box">
          <h3>Contact Cho&amp;Co</h3>
          <p>For data updates, new reports, or any questions about your portal:<br>
          &#x2709;&nbsp;<a href="mailto:info@choandco.co.za">info@choandco.co.za</a>&nbsp;&nbsp;|&nbsp;&nbsp;
          &#127760;&nbsp;<a href="https://www.choandco.co.za" target="_blank">www.choandco.co.za</a><br><br>
          Response time: within 4 business hours on weekdays.</p>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
function tf(btn){{
  var a=btn.nextElementSibling;
  var arr=btn.querySelector('.farr');
  a.classList.toggle('open');
  arr.style.transform=a.classList.contains('open')?'rotate(180deg)':'';
}}
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# 7. MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    log.info("═" * 60)
    log.info("Corevest Analytics Portal — build starting")
    log.info("═" * 60)

    # ── Generate all data ───────────────────────────────────────────────────
    log.info("Generating datasets...")
    port_rows  = gen_portfolio_rows()
    prop_rows  = [{k: v for k, v in p.items()} for p in PROPERTIES_DATA]
    fin_rows   = gen_financials_rows()
    lease_rows = gen_lease_rows()
    proj_rows  = gen_project_rows()
    inv_rows   = gen_investor_rows()
    log.info(f"  portfolio={len(port_rows)} props={len(prop_rows)} financials={len(fin_rows)} "
             f"leases={len(lease_rows)} projects={len(proj_rows)} investors={len(inv_rows)}")

    # ── Supabase: create tables + insert rows (truncate first for idempotency) ──
    log.info("Creating Supabase tables and inserting data...")
    row_map = {
        "corevest_portfolio":           port_rows,
        "corevest_properties":          prop_rows,
        "corevest_monthly_financials":  fin_rows,
        "corevest_leases":              lease_rows,
        "corevest_projects":            proj_rows,
        "corevest_investors":           inv_rows,
    }
    for tbl, schema in TABLES.items():
        create_table(tbl, schema)
        _truncate_table(tbl)
        insert_rows(tbl, row_map[tbl])

    # ── Metabase: build 5 dashboards ────────────────────────────────────────
    log.info("Building Metabase dashboards...")
    tok = _mb_token()
    db  = METABASE_DB_ID

    dash_urls = {
        "portfolio": build_portfolio_dashboard(tok, db),
        "financial": build_financial_dashboard(tok, db),
        "lease":     build_lease_dashboard(tok, db),
        "projects":  build_projects_dashboard(tok, db),
        "investor":  build_investor_dashboard(tok, db),
    }
    log.info("All 5 dashboards live.")

    # ── Generate 5 PDFs ─────────────────────────────────────────────────────
    log.info("Generating PDF reports...")
    pdfs = {
        "portfolio": gen_portfolio_pdf(port_rows, dash_urls["portfolio"]),
        "investor":  gen_investor_pdf(inv_rows,   dash_urls["investor"]),
        "lease":     gen_lease_pdf(lease_rows,    dash_urls["lease"]),
        "projects":  gen_projects_pdf(proj_rows,  dash_urls["projects"]),
        "annual":    gen_annual_pdf(port_rows, inv_rows, dash_urls["portfolio"]),
    }

    # ── Upload PDFs to Supabase Storage ─────────────────────────────────────
    log.info("Uploading PDFs to Supabase Storage...")
    pdf_urls = {}
    names = {
        "portfolio": "Corevest_Monthly_Portfolio_Report.pdf",
        "investor":  "Corevest_Quarterly_Investor_Report.pdf",
        "lease":     "Corevest_Lease_Expiry_Risk_Report.pdf",
        "projects":  "Corevest_Development_Projects_Report.pdf",
        "annual":    "Corevest_Annual_Fund_Performance_Summary.pdf",
    }
    for key, pdf_bytes in pdfs.items():
        pdf_urls[key] = sb_upload_pdf(pdf_bytes, names[key])
    log.info("All 5 PDFs uploaded.")

    # ── Build HTML portal ────────────────────────────────────────────────────
    log.info("Building HTML portal...")
    html = build_html(dash_urls, pdf_urls)

    # ── Deploy to Netlify ────────────────────────────────────────────────────
    log.info("Deploying to Netlify...")
    netlify_url, _ = netlify_deploy(SLUG, html)

    # ── Summary ──────────────────────────────────────────────────────────────
    log.info("═" * 60)
    log.info("BUILD COMPLETE")
    log.info(f"  Portal:      {netlify_url}")
    for k, u in dash_urls.items():
        log.info(f"  Dashboard ({k}): {u}")
    for k, u in pdf_urls.items():
        log.info(f"  PDF ({k}): {u}")
    log.info("═" * 60)

    return netlify_url, dash_urls, pdf_urls


if __name__ == "__main__":
    main()
