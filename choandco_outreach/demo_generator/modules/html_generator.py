"""
Generates a customised analytics portal HTML for a given industry.

Takes the base.html template (accounting version) and substitutes:
  - METABASE dashboard iframe URL
  - Supabase PDF report iframe + card onclick URL
  - Reporting tab subtitle
  - Report cards HTML block
  - FAQ accordion HTML block
"""
import logging
from pathlib import Path

from demo_generator.config import TEMPLATES_DIR

log = logging.getLogger(__name__)

_BASE_HTML = TEMPLATES_DIR / "base.html"

# ── Marker strings in base.html that we target for replacement ─────────────
_DASH_URL_MARKER    = "%%METABASE_DASHBOARD_URL%%"
_PDF_URL_MARKER     = "%%PDF_REPORT_URL%%"
_SUBTITLE_MARKER    = "%%REPORTING_SUBTITLE%%"
_REPORT_CARDS_MARKER = "%%REPORT_CARDS_HTML%%"
_FAQ_MARKER         = "%%FAQ_HTML%%"


def _render_report_cards(report_cards: list[dict], pdf_url: str) -> str:
    """Build the inner HTML of the .rgrid div."""
    parts = []
    for i, card in enumerate(report_cards):
        onclick = f"onclick=\"window.open('{pdf_url}', '_blank')\"" if i == 0 and pdf_url else ""
        parts.append(f"""      <div class="rcard {card['color']}" {onclick}><div class="rtype {card['type_color']}">{card['type']}</div><div class="rtitle">{card['title']}</div><div class="rdesc">{card['desc']}</div><div class="rmeta"><span class="rper">{card['period']}</span><span class="rst {card['status']}">{card['status_label']}</span></div></div>""")
    return "\n".join(parts)


def _render_faq(faq: list[tuple]) -> str:
    """Build the FAQ accordion HTML."""
    parts = []
    for question, answer in faq:
        parts.append(
            f'        <div class="fi"><button class="fq" onclick="tf(this)">{question} <span class="farr">&#9660;</span></button>'
            f'<div class="fa">{answer}</div></div>'
        )
    return "\n".join(parts)


def generate_html(
    industry_slug: str,
    industry_label: str,
    dashboard_url: str,
    pdf_url: str,
    reporting_subtitle: str,
    report_cards: list[dict],
    faq: list[tuple],
) -> str:
    """
    Returns the full HTML string for the industry portal.

    Args:
        industry_slug:      e.g. "retail"
        industry_label:     e.g. "Retail"
        dashboard_url:      Metabase public dashboard URL
        pdf_url:            Supabase public PDF URL
        reporting_subtitle: short description for the Reports tab header
        report_cards:       list of report card dicts
        faq:                list of (question, answer) tuples
    """
    template = _BASE_HTML.read_text(encoding="utf-8")

    cards_html = _render_report_cards(report_cards, pdf_url)
    faq_html   = _render_faq(faq)

    html = (
        template
        .replace(_DASH_URL_MARKER,     dashboard_url)
        .replace(_PDF_URL_MARKER,      pdf_url)
        .replace(_SUBTITLE_MARKER,     reporting_subtitle)
        .replace(_REPORT_CARDS_MARKER, cards_html)
        .replace(_FAQ_MARKER,          faq_html)
    )

    log.info(f"Generated HTML for '{industry_label}' ({len(html):,} chars).")
    return html
