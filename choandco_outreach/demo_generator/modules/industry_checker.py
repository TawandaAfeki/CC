"""Reads the outreach Excel log and finds industries that don't yet have a demo."""
import json
import logging
import openpyxl
from demo_generator.config import COMPLETED_DEMOS, OUTREACH_EXCEL, slug

log = logging.getLogger(__name__)


class IndustryChecker:
    def __init__(self):
        self._ensure_data_dir()

    # ── Public API ────────────────────────────────────────────────────────

    def get_new_industries(self) -> list[str]:
        """Return slugified industry names that exist in the Excel log but have no demo."""
        emailed = self._get_emailed_industries()
        done    = self._get_completed_demos()
        new     = [i for i in emailed if i not in done and i != "accounting"]
        if new:
            log.info(f"New industries to demo: {new}")
        else:
            log.info("No new industries to process.")
        return new

    def mark_done(self, industry_slug: str):
        """Append industry_slug to completed_demos.json after a successful pipeline run."""
        done = self._get_completed_demos()
        if industry_slug not in done:
            done.append(industry_slug)
            COMPLETED_DEMOS.write_text(json.dumps(done, indent=2))
            log.info(f"Marked '{industry_slug}' as completed.")

    # ── Private helpers ───────────────────────────────────────────────────

    def _ensure_data_dir(self):
        COMPLETED_DEMOS.parent.mkdir(parents=True, exist_ok=True)
        if not COMPLETED_DEMOS.exists():
            COMPLETED_DEMOS.write_text('["accounting"]\n')

    def _get_completed_demos(self) -> list[str]:
        try:
            return json.loads(COMPLETED_DEMOS.read_text())
        except Exception:
            return ["accounting"]

    def _get_emailed_industries(self) -> list[str]:
        """Read column 7 (Industry) from the outreach Excel log."""
        if not OUTREACH_EXCEL.exists():
            log.warning(f"Outreach Excel not found at {OUTREACH_EXCEL}")
            return []

        try:
            wb = openpyxl.load_workbook(OUTREACH_EXCEL, read_only=True, data_only=True)
            ws = wb.active
            seen = set()
            for row in ws.iter_rows(min_row=2, values_only=True):
                # Column 7 (index 6) = Industry
                if row and len(row) > 6 and row[6]:
                    s = slug(str(row[6]))
                    if s:
                        seen.add(s)
            wb.close()
            return sorted(seen)
        except Exception as e:
            log.error(f"Failed to read outreach Excel: {e}")
            return []
