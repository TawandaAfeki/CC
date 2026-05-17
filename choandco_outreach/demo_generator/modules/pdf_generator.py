"""
PDF report generator using fpdf2.
Creates a branded Cho&Co industry analytics report.
"""
import logging
from fpdf import FPDF

log = logging.getLogger(__name__)

# Brand colours (RGB)
_NAVY  = (13,  27,  64)
_GOLD  = (193, 154,  79)
_LIGHT = (245, 245, 248)
_WHITE = (255, 255, 255)
_DARK  = (30,  30,  40)


def _safe(text: str) -> str:
    """Replace characters outside Latin-1 with ASCII equivalents."""
    return (str(text)
        .replace("\u2014", "-")   # em dash
        .replace("\u2013", "-")   # en dash
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2026", "...")
        .encode("latin-1", errors="replace")
        .decode("latin-1")
    )


class _Report(FPDF):
    def __init__(self, industry_label: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.industry_label = industry_label
        self.set_margins(20, 20, 20)

    def header(self):
        self.set_fill_color(*_NAVY)
        self.rect(0, 0, 210, 14, "F")
        self.set_y(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*_GOLD)
        self.cell(0, 8, "CHO & CO  |  Business Intelligence", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*_WHITE)
        self.set_y(3)
        self.cell(0, 8, _safe(f"{self.industry_label} Analytics Report"), align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-12)
        self.set_fill_color(*_NAVY)
        self.rect(0, 285, 210, 12, "F")
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*_GOLD)
        self.cell(0, 12, "Confidential - Prepared by Cho & Co  |  www.choandco.co.za", align="C")


def generate_pdf(industry_label: str, data: dict, dashboard_url: str) -> bytes:
    """
    Build a branded PDF report from industry data dict.

    Args:
        industry_label: Human-readable label e.g. "Retail"
        data: Dict returned by data_generator.generate_data()
        dashboard_url: Public Metabase dashboard URL

    Returns:
        PDF as bytes.
    """
    pdf = _Report(industry_label)
    pdf.add_page()

    # ── Cover section ───────────────────────────────────────────────────────
    pdf.set_fill_color(*_NAVY)
    pdf.rect(0, 14, 210, 50, "F")
    pdf.set_y(22)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*_GOLD)
    pdf.cell(0, 12, _safe(industry_label.upper()), align="C", ln=True)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(*_WHITE)
    pdf.cell(0, 8, "Analytics & Performance Report  |  Cho & Co", align="C", ln=True)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 6, _safe(data.get("reporting_subtitle", "")), align="C", ln=True)
    pdf.ln(30)

    # ── KPI headline cards ──────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*_NAVY)
    pdf.cell(0, 8, "KEY PERFORMANCE INDICATORS", ln=True)
    pdf.set_draw_color(*_GOLD)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    rows = data.get("rows", [])
    kpi_metrics = data.get("kpi_metrics", [])

    recent = rows[-3:] if len(rows) >= 3 else rows
    card_w = 80
    card_h = 22
    x_start = 20
    gap = 10
    col = 0
    x = x_start
    y = pdf.get_y()

    for col_name, label in kpi_metrics[:4]:
        vals = [r.get(col_name, 0) for r in recent if isinstance(r.get(col_name), (int, float))]
        total = sum(vals)
        display = f"{total:,.0f}" if total >= 1 else f"{total:.2f}"

        pdf.set_fill_color(*_LIGHT)
        pdf.rect(x, y, card_w, card_h, "F")
        pdf.set_draw_color(*_GOLD)
        pdf.rect(x, y, card_w, card_h)
        pdf.set_fill_color(*_GOLD)
        pdf.rect(x, y, card_w, 2, "F")

        pdf.set_xy(x + 3, y + 4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*_NAVY)
        pdf.cell(card_w - 6, 7, display, align="C", ln=False)

        pdf.set_xy(x + 3, y + 13)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 100, 110)
        pdf.cell(card_w - 6, 5, _safe(label[:35]), align="C", ln=False)

        col += 1
        if col % 2 == 0:
            y += card_h + 6
            x = x_start
        else:
            x += card_w + gap

    pdf.set_y(y + card_h + 10)

    # ── Monthly data table ──────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*_NAVY)
    pdf.cell(0, 8, "MONTHLY DATA SUMMARY", ln=True)
    pdf.set_draw_color(*_GOLD)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    display_cols = [("month", "Month")] + [(c, l[:18]) for c, l in kpi_metrics[:3]]
    col_widths = [30] + [50] * (len(display_cols) - 1)

    # Header row
    pdf.set_fill_color(*_NAVY)
    pdf.set_text_color(*_WHITE)
    pdf.set_font("Helvetica", "B", 8)
    for (_, lbl), w in zip(display_cols, col_widths):
        pdf.cell(w, 7, _safe(lbl), border=0, fill=True, align="C")
    pdf.ln()

    # Data rows (last 12)
    for i, row in enumerate(rows[-12:]):
        if i % 2 == 0:
            pdf.set_fill_color(*_LIGHT)
        else:
            pdf.set_fill_color(*_WHITE)
        pdf.set_text_color(*_DARK)
        pdf.set_font("Helvetica", "", 8)
        for (col_key, _), w in zip(display_cols, col_widths):
            val = row.get(col_key, "")
            if isinstance(val, float):
                text = f"{val:,.1f}"
            elif isinstance(val, int):
                text = f"{val:,}"
            else:
                text = _safe(str(val))
            pdf.cell(w, 6, text, border=0, fill=True, align="C")
        pdf.ln()

    pdf.ln(8)

    # ── Dashboard link ──────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*_NAVY)
    pdf.cell(0, 7, "LIVE ANALYTICS DASHBOARD", ln=True)
    pdf.set_draw_color(*_GOLD)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 200)
    pdf.cell(0, 6, dashboard_url, link=dashboard_url, ln=True)

    pdf.ln(6)

    # ── Report cards (insights) ─────────────────────────────────────────────
    report_cards = data.get("report_cards", [])
    if report_cards:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*_NAVY)
        pdf.cell(0, 7, "INSIGHTS & HIGHLIGHTS", ln=True)
        pdf.set_draw_color(*_GOLD)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)

        for card in report_cards[:6]:
            pdf.set_fill_color(*_LIGHT)
            pdf.set_draw_color(*_GOLD)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*_NAVY)
            pdf.cell(0, 6, _safe(f"  {card.get('title', '')}"), fill=True, border="L", ln=True)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*_DARK)
            pdf.multi_cell(0, 5, _safe(f"  {card.get('desc', '')}"))
            pdf.ln(3)

    # Output as bytes
    output = pdf.output()
    result = bytes(output) if isinstance(output, bytearray) else output
    log.info(f"Generated PDF report: {len(result):,} bytes")
    return result
