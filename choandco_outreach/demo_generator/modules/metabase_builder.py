"""
Metabase dashboard builder.

Steps per industry:
  1. Authenticate (session token via /api/session or API key header)
  2. Find the Supabase database connection in Metabase
  3. Trigger schema sync and wait for the new table to appear
  4. Create KPI scalar cards (one per KPI metric)
  5. Create chart line/bar cards (one per chart metric)
  6. Create a new dashboard
  7. Add all cards to the dashboard (KPIs row 1, charts rows 2-4)
  8. Enable public sharing → return public URL
  9. Export dashboard as PDF → return PDF bytes
"""
import logging
import time
import requests

from demo_generator.config import METABASE_URL, METABASE_API_KEY, METABASE_USERNAME, METABASE_PASSWORD, METABASE_DB_ID

log = logging.getLogger(__name__)

# ── Auth ───────────────────────────────────────────────────────────────────

def _get_session_token() -> str:
    """
    Authenticate and return a token string.
    If METABASE_API_KEY is set (starts with 'mb_'), it is used directly.
    Otherwise, a session token is obtained via username/password.
    """
    if METABASE_API_KEY:
        return METABASE_API_KEY

    resp = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Metabase auth failed [{resp.status_code}]: {resp.text[:300]}")
    return resp.json()["id"]


def _headers(token: str) -> dict:
    """
    Metabase 0.46+ API keys (mb_...) use X-API-Key.
    Session tokens (uuid strings) use X-Metabase-Session.
    """
    if token.startswith("mb_"):
        return {"X-API-Key": token, "Content-Type": "application/json"}
    return {"X-Metabase-Session": token, "Content-Type": "application/json"}


# ── Database discovery ─────────────────────────────────────────────────────

def _find_supabase_db_id(token: str, supabase_host: str) -> int:
    """Return the Metabase database ID that connects to our Supabase project."""
    resp = requests.get(f"{METABASE_URL}/api/database", headers=_headers(token), timeout=15)
    resp.raise_for_status()
    for db in resp.json().get("data", resp.json() if isinstance(resp.json(), list) else []):
        details = db.get("details", {})
        host    = details.get("host", "")
        if supabase_host in host:
            log.info(f"Found Supabase DB in Metabase: id={db['id']} name={db['name']}")
            return db["id"]
    raise RuntimeError(
        f"No Metabase database found with host containing '{supabase_host}'. "
        "Please ensure Supabase is connected to Metabase."
    )


# ── Schema sync ────────────────────────────────────────────────────────────

def _sync_and_wait(token: str, db_id: int, table_name: str, timeout: int = 300) -> int:
    """
    Trigger a schema sync and poll until the target table appears.
    Returns the Metabase table ID.
    """
    log.info(f"Triggering schema sync for database {db_id}...")
    requests.post(
        f"{METABASE_URL}/api/database/{db_id}/sync_schema",
        headers=_headers(token),
        timeout=15,
    )
    # Give Metabase time to start the sync before polling
    log.info("Waiting 20s for sync to begin...")
    time.sleep(20)

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(10)
        meta = requests.get(
            f"{METABASE_URL}/api/database/{db_id}/metadata",
            headers=_headers(token),
            timeout=20,
        )
        meta.raise_for_status()
        for tbl in meta.json().get("tables", []):
            if tbl.get("name", "").lower() == table_name.lower():
                log.info(f"Table '{table_name}' found in Metabase with id={tbl['id']}")
                return tbl["id"]

    raise TimeoutError(
        f"Table '{table_name}' did not appear in Metabase within {timeout}s. "
        "Check Supabase connection and table name."
    )


# ── Card creation (native SQL — no schema sync required) ───────────────────

def _create_scalar_card(token: str, db_id: int, table_id: int, col_name: str, label: str, collection_id=None) -> int:
    """Create a KPI scalar card using native SQL."""
    # table_id unused — kept for signature compatibility
    table_name = _current_table  # set by build_dashboard before card creation
    sql = f'SELECT SUM("{col_name}") AS "{label}" FROM public."{table_name}"'
    payload = {
        "name":          label,
        "dataset_query": {
            "type":     "native",
            "database": db_id,
            "native":   {"query": sql},
        },
        "display": "scalar",
        "visualization_settings": {},
    }
    if collection_id:
        payload["collection_id"] = collection_id

    resp = requests.post(f"{METABASE_URL}/api/card", headers=_headers(token), json=payload, timeout=15)
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Failed to create scalar card '{label}': {resp.text[:300]}")
    card_id = resp.json()["id"]
    log.info(f"Created scalar card '{label}' id={card_id}")
    return card_id


def _create_line_card(token: str, db_id: int, table_id: int, col_name: str, label: str, collection_id=None) -> int:
    """Create a line chart card using native SQL."""
    table_name = _current_table
    sql = (
        f'SELECT DATE_TRUNC(\'month\', "month") AS "Month", '
        f'SUM("{col_name}") AS "{label}" '
        f'FROM public."{table_name}" '
        f'GROUP BY 1 ORDER BY 1'
    )
    payload = {
        "name":          label,
        "dataset_query": {
            "type":     "native",
            "database": db_id,
            "native":   {"query": sql},
        },
        "display": "line",
        "visualization_settings": {
            "graph.dimensions": ["Month"],
            "graph.metrics":    [label],
        },
    }
    if collection_id:
        payload["collection_id"] = collection_id

    resp = requests.post(f"{METABASE_URL}/api/card", headers=_headers(token), json=payload, timeout=15)
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Failed to create line card '{label}': {resp.text[:300]}")
    card_id = resp.json()["id"]
    log.info(f"Created line card '{label}' id={card_id}")
    return card_id


# Module-level variable set by build_dashboard so card functions know the table name
_current_table: str = ""


# ── Dashboard assembly ─────────────────────────────────────────────────────

def _create_dashboard(token: str, name: str, description: str, collection_id=None) -> int:
    payload = {"name": name, "description": description}
    if collection_id:
        payload["collection_id"] = collection_id
    resp = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers=_headers(token),
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    dash_id = resp.json()["id"]
    log.info(f"Created dashboard '{name}' id={dash_id}")
    return dash_id


def _add_cards_to_dashboard(token: str, dash_id: int, kpi_card_ids: list[int], chart_card_ids: list[int]):
    """
    Layout: KPI scalars as a row of small squares at top, charts in full-width rows below.
    Metabase dashboard card size units: col/row are 0-based grid coords, size_x/size_y in grid cells.
    """
    cards_payload = []

    # KPI row: each scalar card is 3 wide × 2 tall, side by side
    kpi_width = 3
    kpi_height = 2
    for idx, card_id in enumerate(kpi_card_ids):
        cards_payload.append({
            "id":          -(idx + 1),   # temporary negative ID for new cards
            "card_id":     card_id,
            "col":         idx * kpi_width,
            "row":         0,
            "size_x":      kpi_width,
            "size_y":      kpi_height,
            "parameter_mappings": [],
            "visualization_settings": {},
        })

    # Chart rows: each chart is 9 wide × 6 tall, two per row
    chart_col_positions = [0, 9]
    chart_width  = 9
    chart_height = 6
    start_row    = kpi_height + 1

    for idx, card_id in enumerate(chart_card_ids):
        col = chart_col_positions[idx % 2]
        row = start_row + (idx // 2) * (chart_height + 1)
        cards_payload.append({
            "id":          -(len(kpi_card_ids) + idx + 1),
            "card_id":     card_id,
            "col":         col,
            "row":         row,
            "size_x":      chart_width,
            "size_y":      chart_height,
            "parameter_mappings": [],
            "visualization_settings": {},
        })

    resp = requests.put(
        f"{METABASE_URL}/api/dashboard/{dash_id}/cards",
        headers=_headers(token),
        json={"cards": cards_payload},
        timeout=20,
    )
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Failed to add cards to dashboard: {resp.text[:300]}")
    log.info(f"Added {len(kpi_card_ids)} KPI cards + {len(chart_card_ids)} chart cards to dashboard {dash_id}.")


def _get_admin_session_token() -> str:
    """Get a full-admin session token via username/password login."""
    resp = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Metabase admin login failed [{resp.status_code}]: {resp.text[:300]}")
    return resp.json()["id"]


def _enable_public_link(token: str, dash_id: int) -> str:
    """Enable public sharing using admin session token, then create the public link."""
    # Use full admin session token — API keys lack permission for public link creation
    admin_token = _get_admin_session_token()
    admin_headers = {"X-Metabase-Session": admin_token, "Content-Type": "application/json"}

    resp = requests.post(
        f"{METABASE_URL}/api/dashboard/{dash_id}/public_link",
        headers=admin_headers,
        timeout=15,
    )
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Failed to enable public link: {resp.text[:300]}")
    uuid = resp.json()["uuid"]
    url  = f"{METABASE_URL}/public/dashboard/{uuid}"
    log.info(f"Public dashboard URL: {url}")
    return url


def _export_pdf(token: str, dash_id: int) -> bytes:
    """
    Metabase Community Edition does not support PDF export via API.
    PDF is generated directly from the industry data by generate_pdf().
    This function is kept for signature compatibility but returns empty bytes —
    the caller (build_dashboard) uses the pre-generated PDF instead.
    """
    log.info("Metabase PDF export not available in Community Edition — using generated PDF.")
    return b""


# ── Main entry point ───────────────────────────────────────────────────────

def build_dashboard(
    industry_slug: str,
    industry_label: str,
    table_name: str,
    kpi_metrics: list[tuple],
    chart_metrics: list[tuple],
    supabase_host: str,
) -> tuple[str, bytes]:
    """
    Full pipeline: find DB → sync → create cards → assemble dashboard → public link → PDF.

    Args:
        industry_slug:  e.g. "retail"
        industry_label: human-readable e.g. "Retail"
        table_name:     Supabase table name
        kpi_metrics:    list of (col_name, label)
        chart_metrics:  list of (col_name, label)
        supabase_host:  e.g. "db.ahdctxgdszwncyuvwbtp.supabase.co"

    Returns:
        (public_dashboard_url, pdf_bytes)
    """
    global _current_table
    _current_table = table_name

    token  = _get_session_token()
    db_id  = METABASE_DB_ID if METABASE_DB_ID else _find_supabase_db_id(token, supabase_host)
    tbl_id = 0  # not needed — native SQL cards don't require a table ID

    # Create KPI scalar cards
    kpi_ids = [
        _create_scalar_card(token, db_id, tbl_id, col, lbl)
        for col, lbl in kpi_metrics
    ]

    # Create chart cards
    chart_ids = [
        _create_line_card(token, db_id, tbl_id, col, lbl)
        for col, lbl in chart_metrics
    ]

    dash_id = _create_dashboard(
        token,
        name=f"{industry_label} Analytics Dashboard",
        description=f"Cho&Co demo dashboard for the {industry_label} industry.",
    )

    _add_cards_to_dashboard(token, dash_id, kpi_ids, chart_ids)

    public_url = _enable_public_link(token, dash_id)
    pdf_bytes  = _export_pdf(token, dash_id)

    return public_url, pdf_bytes
