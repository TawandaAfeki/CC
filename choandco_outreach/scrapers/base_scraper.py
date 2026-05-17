import logging
import random
import time
from abc import ABC, abstractmethod

import requests
from fake_useragent import UserAgent

from config import SCRAPE_DELAY_RANGE, REQUEST_TIMEOUT
from leads.models import Lead

logger = logging.getLogger(__name__)

try:
    _ua = UserAgent()
except Exception:
    _ua = None


class BaseScraper(ABC):
    """Abstract base class for all lead scrapers."""

    def __init__(self):
        self.session = requests.Session()
        self._update_headers()

    def _update_headers(self):
        """Set headers with a rotated User-Agent."""
        ua_string = _ua.random if _ua else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.session.headers.update({
            "User-Agent": ua_string,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })

    @abstractmethod
    def scrape(self, search_queries: list, max_results: int = 10) -> list:
        """Return a list of Lead objects."""
        ...

    def _get(self, url: str, params: dict = None) -> requests.Response | None:
        """Make a GET request with error handling and rate limiting."""
        self._random_delay()
        self._update_headers()
        try:
            resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 429:
                logger.warning("Rate limited on %s, backing off", url)
                time.sleep(30)
                return None
            if resp.status_code == 403:
                logger.warning("Blocked (403) on %s", url)
                return None
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.error("Request failed for %s: %s", url, e)
            return None

    def _random_delay(self):
        """Sleep a random interval to avoid rate limiting."""
        delay = random.uniform(*SCRAPE_DELAY_RANGE)
        time.sleep(delay)

    def _extract_emails_from_text(self, text: str) -> list:
        """Extract email addresses from a block of text."""
        import re
        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(pattern, text)
        # Filter out image/file extensions that look like emails
        valid = [e for e in emails if not e.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js"))]
        return list(set(valid))

    def _extract_phones_from_text(self, text: str) -> list:
        """Extract South African phone numbers from text."""
        import re
        patterns = [
            r"\+27\s?\d{2}\s?\d{3}\s?\d{4}",
            r"0\d{2}\s?\d{3}\s?\d{4}",
            r"\(\d{3}\)\s?\d{3}[\s-]?\d{4}",
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))

    def _parse_contact_person(self, raw: str) -> tuple:
        """
        Parse a contact person string into (name, title).
        Handles formats like:
          "Amin Mohammed (Manager)"  -> ("Amin Mohammed", "Manager")
          "Sarah van der Berg"       -> ("Sarah van der Berg", "")
          ""                         -> ("", "")
        """
        import re
        if not raw or not raw.strip():
            return ("", "")
        raw = raw.strip()
        match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", raw)
        if match:
            name = match.group(1).strip()
            title = match.group(2).strip()
            return (name, title)
        return (raw, "")

    def _derive_email_candidates(self, full_name: str, domain: str) -> list:
        """
        Generate likely email addresses from a person's name and company domain.
        Returns candidates in order of likelihood:
          firstname@domain, firstname.lastname@domain
        Tries both .co.za and .com TLDs if not already present.
        Returns empty list if name or domain is empty.
        """
        import re
        if not full_name or not full_name.strip() or not domain or not domain.strip():
            return []

        # Clean up domain — strip protocol, www., trailing slashes, paths
        domain = re.sub(r"^https?://", "", domain.strip())
        domain = re.sub(r"^www\.", "", domain)
        domain = domain.split("/")[0].split("?")[0].strip().lower()

        if not domain:
            return []

        parts = full_name.strip().lower().split()
        # Remove punctuation from name parts
        parts = [re.sub(r"[^a-z]", "", p) for p in parts]
        parts = [p for p in parts if p]

        if not parts:
            return []

        firstname = parts[0]
        candidates = []

        if len(parts) >= 2:
            lastname = parts[-1]
            candidates.append(f"{firstname}@{domain}")
            candidates.append(f"{firstname}.{lastname}@{domain}")
        else:
            candidates.append(f"{firstname}@{domain}")

        return candidates
