"""
leads/suppression.py

Permanent email suppression list.
Emails added here will never be contacted again — neither initial sends
nor follow-ups. Backed by data/suppressed_emails.json.

Usage:
    add_suppressed("bad@domain.co.za")    # add manually or on bounce
    is_suppressed("bad@domain.co.za")     # returns True
"""
import json
import logging
from pathlib import Path

from config import DATA_DIR

logger = logging.getLogger(__name__)

SUPPRESSION_PATH = DATA_DIR / "suppressed_emails.json"

# In-memory cache (loaded once per process)
_cache: set | None = None


def _load() -> set:
    """Load suppression list from disk into memory cache."""
    global _cache
    if _cache is not None:
        return _cache
    if not SUPPRESSION_PATH.exists():
        _cache = set()
        return _cache
    try:
        with open(SUPPRESSION_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache = {e.strip().lower() for e in data if isinstance(e, str)}
        logger.info("Loaded %d suppressed emails from %s", len(_cache), SUPPRESSION_PATH)
    except Exception as e:
        logger.warning("Could not load suppression list: %s", e)
        _cache = set()
    return _cache


def _save(suppressed: set) -> None:
    """Persist the suppression set to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SUPPRESSION_PATH, "w", encoding="utf-8") as f:
            json.dump(sorted(suppressed), f, indent=2)
    except Exception as e:
        logger.error("Could not save suppression list: %s", e)


def is_suppressed(email: str) -> bool:
    """Return True if this email address is on the suppression list."""
    if not email:
        return False
    return email.strip().lower() in _load()


def add_suppressed(email: str) -> None:
    """Add an email to the suppression list and persist immediately."""
    if not email:
        return
    email = email.strip().lower()
    suppressed = _load()
    if email not in suppressed:
        suppressed.add(email)
        _save(suppressed)
        logger.info("Suppressed: %s", email)


def load_suppressions() -> set:
    """Return the full suppression set (lowercase emails)."""
    return _load()
