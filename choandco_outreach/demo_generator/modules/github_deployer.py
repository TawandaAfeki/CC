"""
Deploys the industry HTML to the GitHub CC repository.

Creates (or updates) a file at:
  {industry}/index.html

in the main branch of the CC repo owned by GITHUB_USERNAME.
"""
import base64
import logging
import requests

from demo_generator.config import GITHUB_TOKEN, GITHUB_USERNAME, GITHUB_REPO, GITHUB_BRANCH

log = logging.getLogger(__name__)

_API_BASE = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept":        "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_file_sha(path: str) -> str | None:
    """Return the SHA of an existing file, or None if it doesn't exist."""
    url  = f"{_API_BASE}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{path}"
    resp = requests.get(url, headers=_headers(), params={"ref": GITHUB_BRANCH}, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None


def deploy(industry_slug: str, html_content: str) -> str:
    """
    Create or update {industry_slug}/index.html in the CC repo.

    Returns:
        GitHub URL of the committed file.
    """
    path    = f"{industry_slug}/index.html"
    encoded = base64.b64encode(html_content.encode("utf-8")).decode("ascii")
    sha     = _get_file_sha(path)

    payload = {
        "message": f"Add {industry_slug} demo portal",
        "content": encoded,
        "branch":  GITHUB_BRANCH,
    }
    if sha:
        payload["message"] = f"Update {industry_slug} demo portal"
        payload["sha"] = sha

    url  = f"{_API_BASE}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{path}"
    resp = requests.put(url, headers=_headers(), json=payload, timeout=30)

    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"GitHub deploy failed [{resp.status_code}]: {resp.text[:400]}"
        )

    commit_url = resp.json().get("commit", {}).get("html_url", "")
    file_url   = f"https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"
    log.info(f"Deployed to GitHub: {file_url} (commit: {commit_url})")
    return file_url
