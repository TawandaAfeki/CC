"""
Demo Generator — orchestrator.

Called automatically at the end of each Cho&Co outreach batch.
For each new industry found in the outreach Excel log:
  1. Generate industry-specific KPI data
  2. Upload data to Supabase (new table + PDF report to Storage)
  3. Build Metabase dashboard, export PDF
  4. Generate branded HTML portal
  5. Push HTML to GitHub CC repo
  6. Create Netlify site + custom subdomain
  7. Send completion email
  8. Mark industry as done
"""
import logging
import sys
from pathlib import Path

# Allow running from repo root: python -m demo_generator.main
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from demo_generator.config import SUPABASE_DB_HOST, slug as make_slug
from demo_generator.modules.industry_checker  import IndustryChecker
from demo_generator.modules.data_generator    import generate_data
from demo_generator.modules.supabase_client   import create_table, insert_rows, upload_pdf
from demo_generator.modules.metabase_builder  import build_dashboard
from demo_generator.modules.pdf_generator     import generate_pdf
from demo_generator.modules.html_generator    import generate_html
from demo_generator.modules.github_deployer   import deploy as github_deploy
from demo_generator.modules.netlify_deployer  import deploy as netlify_deploy
from demo_generator.modules.notifier          import send_notification

log = logging.getLogger(__name__)

# ── Human-readable labels ──────────────────────────────────────────────────
_LABELS = {
    "retail":                "Retail",
    "recruitment":           "Recruitment",
    "property":              "Property",
    "financial_services":    "Financial Services",
    "logistics":             "Logistics",
    "agribusiness":          "Agribusiness",
    "professional_services": "Professional Services",
}


def _label(slug: str) -> str:
    return _LABELS.get(slug, slug.replace("_", " ").title())


# ── Main entry point ───────────────────────────────────────────────────────

def run(industries_to_process: list[str] | None = None):
    """
    Main entry point for the demo generator.

    Args:
        industries_to_process: Optional override list (slugs). If None,
                               reads the outreach Excel to find new industries.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [DEMO] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    checker = IndustryChecker()

    new_industries = industries_to_process or checker.get_new_industries()

    if not new_industries:
        log.info("Demo generator: nothing to do — all industries already have portals.")
        return

    log.info(f"Demo generator: processing {len(new_industries)} new industries: {new_industries}")

    for industry_slug in new_industries:
        industry_label = _label(industry_slug)
        log.info(f"─── Starting demo pipeline for: {industry_label} ───")

        try:
            # 1. Generate data
            log.info(f"[{industry_label}] Step 1/7 — Generating KPI data...")
            data = generate_data(industry_slug)

            # 2. Upload table + rows to Supabase first (table must exist before Metabase syncs)
            log.info(f"[{industry_label}] Step 2/7 — Uploading data to Supabase...")
            create_table(data["table_name"], data["columns"])
            insert_rows(data["table_name"], data["rows"])

            # 3. Build Metabase dashboard (syncs the now-existing table) + export PDF
            log.info(f"[{industry_label}] Step 3/7 — Building Metabase dashboard...")
            dashboard_url, pdf_bytes = build_dashboard(
                industry_slug  = industry_slug,
                industry_label = industry_label,
                table_name     = data["table_name"],
                kpi_metrics    = data["kpi_metrics"],
                chart_metrics  = data["chart_metrics"],
                supabase_host  = SUPABASE_DB_HOST,
            )

            # Generate real PDF from industry data (Metabase CE has no PDF export)
            log.info(f"[{industry_label}] Step 3b/7 — Generating PDF report...")
            pdf_bytes = generate_pdf(industry_label, data, dashboard_url)

            # Upload PDF to Supabase Storage
            log.info(f"[{industry_label}] Step 3c/7 — Uploading PDF report to Supabase Storage...")
            filename = f"{industry_label.replace(' ', '_').title()}_Demo_Report.pdf"
            pdf_url = upload_pdf(pdf_bytes, filename)

            # 4. Generate HTML
            log.info(f"[{industry_label}] Step 4/7 — Generating HTML portal...")
            html = generate_html(
                industry_slug      = industry_slug,
                industry_label     = industry_label,
                dashboard_url      = dashboard_url,
                pdf_url            = pdf_url,
                reporting_subtitle = data["reporting_subtitle"],
                report_cards       = data["report_cards"],
                faq                = data["faq"],
            )

            # 5. GitHub
            log.info(f"[{industry_label}] Step 5/7 — Deploying to GitHub...")
            github_url = github_deploy(industry_slug, html)

            # 6. Netlify
            log.info(f"[{industry_label}] Step 6/7 — Creating Netlify site...")
            netlify_url, custom_url = netlify_deploy(industry_slug, html)

            # 7. Notify
            log.info(f"[{industry_label}] Step 7/7 — Sending notification...")
            send_notification(
                industry_label = industry_label,
                custom_url     = custom_url,
                netlify_url    = netlify_url,
                dashboard_url  = dashboard_url,
                pdf_url        = pdf_url,
                github_url     = github_url,
            )

            # Mark as done (only on full success)
            checker.mark_done(industry_slug)
            log.info(f"[{industry_label}] ✓ Portal live at {custom_url}")

        except Exception as exc:
            log.error(
                f"[{industry_label}] Pipeline failed — will retry on next run. "
                f"Error: {exc}",
                exc_info=True,
            )
            # Do NOT mark as done; next run will retry


# ── CLI entry ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Usage: python -m demo_generator.main [industry_slug ...]
    overrides = [make_slug(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else None
    run(overrides)
