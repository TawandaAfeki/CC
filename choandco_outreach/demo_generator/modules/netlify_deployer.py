"""
Creates a Netlify site for the industry demo via direct ZIP deploy.

Steps:
  1. Find existing site or create a new one (no GitHub link needed)
  2. POST the HTML as a ZIP directly to the Netlify deploy API
  3. Add custom domain alias: {industry_slug}.choandco.co.za
  4. Return the Netlify URL and custom domain URL
"""
import hashlib
import logging
import time
import requests

from demo_generator.config import (
    NETLIFY_TOKEN, NETLIFY_DOMAIN_SUFFIX,
)

log = logging.getLogger(__name__)

_API_BASE = "https://api.netlify.com/api/v1"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type":  "application/json",
    }


def _find_existing_site(industry_slug: str) -> tuple[str, str] | None:
    """
    Return (site_id, netlify_url) if a clean (non-repo-linked) site exists, else None.
    If a repo-linked site is found, delete it so we can create a clean ZIP-deploy site.
    """
    resp = requests.get(f"{_API_BASE}/sites", headers=_headers(), timeout=15)
    resp.raise_for_status()
    site_name = f"{industry_slug}-choandco"
    for site in resp.json():
        if site.get("name") == site_name:
            site_id = site["id"]
            # If this site has a GitHub repo link, delete it — the GitHub build
            # overrides ZIP deploys, causing raw HTML to be served instead of rendered HTML
            build_settings = site.get("build_settings") or {}
            if build_settings.get("repo_url") or build_settings.get("provider"):
                log.info(f"Deleting repo-linked site '{site_name}' (id={site_id}) to create a clean one.")
                del_resp = requests.delete(
                    f"{_API_BASE}/sites/{site_id}", headers=_headers(), timeout=15
                )
                if del_resp.ok:
                    log.info(f"Deleted old repo-linked site '{site_name}'.")
                else:
                    log.warning(f"Could not delete old site [{del_resp.status_code}]: {del_resp.text[:200]}")
                return None  # Fall through to create a fresh site
            # Clean site — reuse it
            url = site.get("ssl_url") or site.get("url", "")
            log.info(f"Found existing clean Netlify site '{site_name}' id={site_id}")
            return site_id, url
    return None


def _create_site(industry_slug: str) -> tuple[str, str]:
    """Create a plain static site (no GitHub repo link)."""
    site_name = f"{industry_slug}-choandco"
    payload = {"name": site_name}
    resp = requests.post(f"{_API_BASE}/sites", headers=_headers(), json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Netlify site creation failed [{resp.status_code}]: {resp.text[:400]}"
        )
    data = resp.json()
    site_id = data["id"]
    netlify_url = data.get("ssl_url") or data.get("url", "")
    log.info(f"Created Netlify site '{site_name}' id={site_id} url={netlify_url}")
    return site_id, netlify_url


def _deploy_files(site_id: str, html: str) -> str:
    """
    Deploy index.html using the Netlify Files API (digest-based).
    This is the same method used by the official Netlify CLI and guarantees
    correct Content-Type headers for HTML files.

    Steps:
      1. POST a file manifest (SHA1 digest of each file) to create a deploy
      2. PUT the actual file bytes for any file Netlify says it needs
      3. Poll until state == "ready"
    """
    html_bytes = html.encode("utf-8")
    sha1 = hashlib.sha1(html_bytes).hexdigest()

    # Step 1 — create deploy with file manifest
    resp = requests.post(
        f"{_API_BASE}/sites/{site_id}/deploys",
        headers=_headers(),
        json={"files": {"/index.html": sha1}, "async": False},
        timeout=30,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Netlify deploy manifest failed [{resp.status_code}]: {resp.text[:400]}")

    deploy_data    = resp.json()
    deploy_id      = deploy_data["id"]
    required_files = deploy_data.get("required", [])
    log.info(f"Deploy {deploy_id} created. Required uploads: {required_files}")

    # Step 2 — upload files Netlify doesn't already have cached
    if sha1 in required_files:
        up = requests.put(
            f"{_API_BASE}/deploys/{deploy_id}/files/index.html",
            headers={
                "Authorization": f"Bearer {NETLIFY_TOKEN}",
                "Content-Type":  "application/octet-stream",
            },
            data=html_bytes,
            timeout=30,
        )
        if not up.ok:
            raise RuntimeError(f"File upload failed [{up.status_code}]: {up.text[:300]}")
        log.info("index.html uploaded.")

    # Step 3 — poll until ready (max 120s)
    deploy_url = deploy_data.get("deploy_ssl_url") or deploy_data.get("deploy_url", "")
    deadline   = time.time() + 120
    while time.time() < deadline:
        time.sleep(4)
        poll = requests.get(f"{_API_BASE}/deploys/{deploy_id}", headers=_headers(), timeout=15)
        if poll.ok:
            state = poll.json().get("state", "")
            log.info(f"Deploy {deploy_id} state: {state}")
            if state == "ready":
                deploy_url = poll.json().get("deploy_ssl_url") or poll.json().get("deploy_url", deploy_url)
                break
            if state in ("error", "failed"):
                raise RuntimeError(f"Netlify deploy reached state '{state}'")

    log.info(f"Deploy live at: {deploy_url}")
    return deploy_url


def _add_domain_alias(site_id: str, industry_slug: str) -> str:
    """Add the custom subdomain alias and return it."""
    custom_domain = f"{industry_slug}.{NETLIFY_DOMAIN_SUFFIX}"
    payload = {"domain": custom_domain}
    resp = requests.post(
        f"{_API_BASE}/sites/{site_id}/domain_aliases",
        headers=_headers(),
        json=payload,
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        if resp.status_code == 422:
            log.warning(f"Domain alias '{custom_domain}' may already exist: {resp.text[:200]}")
        else:
            raise RuntimeError(
                f"Failed to add domain alias [{resp.status_code}]: {resp.text[:400]}"
            )
    log.info(f"Custom domain alias set: https://{custom_domain}")
    return custom_domain


def deploy(industry_slug: str, html: str) -> tuple[str, str]:
    """
    Deploy the HTML portal to Netlify via direct ZIP upload.

    Args:
        industry_slug: e.g. "retail"
        html:          Full HTML string for the portal

    Returns:
        (netlify_url, live_url)
        live_url is custom domain if DNS ready, otherwise netlify_url.
    """
    result = _find_existing_site(industry_slug)
    if result:
        site_id, netlify_url = result
    else:
        site_id, netlify_url = _create_site(industry_slug)

    # Files API deploy — correct Content-Type, same method as Netlify CLI
    _deploy_files(site_id, html)

    # Refresh site URL after deploy
    resp = requests.get(f"{_API_BASE}/sites/{site_id}", headers=_headers(), timeout=15)
    if resp.ok:
        netlify_url = resp.json().get("ssl_url") or resp.json().get("url", netlify_url)

    # Register custom domain alias — non-fatal if DNS isn't ready yet
    custom_domain = f"{industry_slug}.{NETLIFY_DOMAIN_SUFFIX}"
    try:
        _add_domain_alias(site_id, industry_slug)
        log.info(f"Custom domain alias registered (will activate when DNS propagates): {custom_domain}")
    except Exception as e:
        log.warning(f"Custom domain alias could not be set (DNS not ready): {e}")

    log.info(f"Portal live now at: {netlify_url}")
    log.info(f"Custom domain (pending DNS): https://{custom_domain}")
    return netlify_url, netlify_url
