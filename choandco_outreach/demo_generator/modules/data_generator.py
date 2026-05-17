"""Generates industry-specific KPI data and returns rows + metadata."""
import importlib
import logging
import io
import csv

log = logging.getLogger(__name__)

# Map slugs to their data modules
_MODULE_MAP = {
    "retail":                "demo_generator.templates.industry_data.retail",
    "recruitment":           "demo_generator.templates.industry_data.recruitment",
    "property":              "demo_generator.templates.industry_data.property",
    "financial_services":    "demo_generator.templates.industry_data.financial_services",
    "logistics":             "demo_generator.templates.industry_data.logistics",
    "agribusiness":          "demo_generator.templates.industry_data.agribusiness",
    "professional_services": "demo_generator.templates.industry_data.professional_services",
}
_GENERIC = "demo_generator.templates.industry_data.generic"


def get_industry_module(industry_slug: str):
    mod_path = _MODULE_MAP.get(industry_slug, _GENERIC)
    mod = importlib.import_module(mod_path)
    return mod


def generate_data(industry_slug: str) -> dict:
    """
    Generate demo data for an industry.

    Returns:
        {
          "table_name": str,
          "columns":    dict[str, str],  # col_name → SQL type
          "rows":       list[dict],
          "kpi_metrics":   list[(col, label)],
          "chart_metrics": list[(col, label)],
          "report_cards":  list[dict],
          "reporting_subtitle": str,
          "faq":           list[(question, answer)],
          "csv_bytes":  bytes,
        }
    """
    mod   = get_industry_module(industry_slug)
    rows  = mod.generate()

    # Override TABLE_NAME to include the slug (for generic fallback)
    table_name = f"{industry_slug}_demo_data"

    # Build CSV bytes
    csv_bytes = _to_csv(rows)

    return {
        "table_name":          table_name,
        "columns":             mod.COLUMNS,
        "rows":                rows,
        "kpi_metrics":         mod.KPI_METRICS,
        "chart_metrics":       mod.CHART_METRICS,
        "report_cards":        mod.REPORT_CARDS,
        "reporting_subtitle":  mod.REPORTING_SUBTITLE,
        "faq":                 mod.FAQ,
        "csv_bytes":           csv_bytes,
    }


def _to_csv(rows: list[dict]) -> bytes:
    if not rows:
        return b""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


# ── CLI test helper ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    industry = sys.argv[1] if len(sys.argv) > 1 else "retail"
    data = generate_data(industry)
    print(f"Industry  : {industry}")
    print(f"Table     : {data['table_name']}")
    print(f"Rows      : {len(data['rows'])}")
    print(f"Columns   : {list(data['columns'].keys())}")
    print(f"CSV bytes : {len(data['csv_bytes'])}")
    print("First row :", data["rows"][0])
