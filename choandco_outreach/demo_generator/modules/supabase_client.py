"""
Supabase client for the demo generator.

Responsibilities:
  1. Create a new Postgres table via the Supabase Management API (HTTPS)
  2. Batch-insert generated rows via the Supabase REST API (PostgREST)
  3. Upload the PDF report to Supabase Storage (Reports bucket)
"""
import logging
import os
import requests

from demo_generator.config import (
    SUPABASE_URL, SUPABASE_SERVICE_KEY,
    SUPABASE_PROJECT_REF, REPORTS_BUCKET,
)

log = logging.getLogger(__name__)

SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN", "")
_MGMT_BASE = "https://api.supabase.com/v1"


# ── Helpers ────────────────────────────────────────────────────────────────

def _rest_headers() -> dict:
    return {
        "apikey":        SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }


def _mgmt_headers() -> dict:
    return {
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type":  "application/json",
    }


# ── Public functions ───────────────────────────────────────────────────────

def create_table(table_name: str, columns: dict) -> None:
    """
    Create the industry demo table via the Supabase Management API
    and grant access to all roles so Metabase can discover it.
    """
    col_defs = ", ".join(f'"{k}" {v}' for k, v in columns.items())
    url = f"{_MGMT_BASE}/projects/{SUPABASE_PROJECT_REF}/database/query"

    statements = [
        f'CREATE TABLE IF NOT EXISTS public."{table_name}" ({col_defs});',
        f'GRANT ALL ON public."{table_name}" TO postgres, anon, authenticated, service_role;',
        f'ALTER TABLE public."{table_name}" ENABLE ROW LEVEL SECURITY;',
        f'CREATE POLICY IF NOT EXISTS "allow_all" ON public."{table_name}" FOR ALL USING (true);',
    ]

    log.info(f"Creating table '{table_name}' in Supabase...")
    for sql in statements:
        resp = requests.post(url, headers=_mgmt_headers(), json={"query": sql}, timeout=30)
        if resp.status_code not in (200, 201):
            # Policy creation errors are non-fatal (policy may already exist)
            if "policy" in sql.lower():
                log.warning(f"Policy setup warning (non-fatal): {resp.text[:200]}")
            else:
                raise RuntimeError(
                    f"Failed [{resp.status_code}] on: {sql[:80]} — {resp.text[:300]}"
                )
    log.info(f"Table '{table_name}' ready with permissions granted.")


def insert_rows(table_name: str, rows: list[dict]) -> None:
    """
    Batch-insert rows into the Supabase table via the REST (PostgREST) API.

    Args:
        table_name: target table
        rows:       list of dicts (each dict is one row, excluding 'id')
    """
    if not rows:
        return

    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    # PostgREST supports bulk insert natively
    resp = requests.post(url, headers=_rest_headers(), json=rows, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Row insert failed [{resp.status_code}]: {resp.text[:400]}"
        )
    log.info(f"Inserted {len(rows)} rows into '{table_name}'.")


def upload_pdf(pdf_bytes: bytes, filename: str) -> str:
    """
    Upload a PDF to the Supabase Storage 'Reports' bucket.

    Args:
        pdf_bytes: raw PDF content
        filename:  e.g. "Retail_Demo_Report.pdf"

    Returns:
        Public URL of the uploaded file.
    """
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{REPORTS_BUCKET}/{filename}"
    headers = {
        "apikey":        SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  "application/pdf",
        "x-upsert":      "true",   # overwrite if re-run
    }
    log.info(f"Uploading PDF '{filename}' to Supabase Storage...")
    resp = requests.post(upload_url, headers=headers, data=pdf_bytes, timeout=60)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"PDF upload failed [{resp.status_code}]: {resp.text[:400]}"
        )
    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{REPORTS_BUCKET}/{filename}"
    log.info(f"PDF uploaded: {public_url}")
    return public_url


def run_pipeline(table_name: str, columns: dict, rows: list[dict], pdf_bytes: bytes, industry_label: str) -> str:
    """
    Orchestrates: create table → insert rows → upload PDF.

    Returns:
        Public PDF URL.
    """
    create_table(table_name, columns)
    insert_rows(table_name, rows)
    filename = f"{industry_label.replace(' ', '_').title()}_Demo_Report.pdf"
    return upload_pdf(pdf_bytes, filename)
