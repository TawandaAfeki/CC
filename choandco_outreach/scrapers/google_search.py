import json
import logging
from datetime import datetime

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from leads.models import Lead

logger = logging.getLogger(__name__)


class GoogleSearchScraper(BaseScraper):
    """Find potential clients by crawling SA business websites directly.

    Since search engines block automated requests, this scraper uses
    yep.co.za search with pagination and additional keyword variations
    to maximize coverage beyond the DirectoryScraper.
    """

    BASE_URL = "https://www.yep.co.za/search"

    # More specific search terms that differ from the main directory scraper
    SEARCH_VARIATIONS = [
        "{industry} services",
        "{industry} company",
        "{industry} solutions",
        "{industry} suppliers",
    ]

    SA_CITIES = ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Bloemfontein"]

    def scrape(self, search_queries: list, max_results: int = 10) -> list:
        """Search for businesses using varied keyword combinations."""
        all_leads = []
        seen_emails = set()

        for industry in search_queries:
            if len(all_leads) >= max_results:
                break

            for variation in self.SEARCH_VARIATIONS:
                if len(all_leads) >= max_results:
                    break

                query = variation.format(industry=industry)

                for page in range(1, 4):  # Pages 1-3
                    if len(all_leads) >= max_results:
                        break

                    leads = self._search_page(query, page, industry, seen_emails)
                    all_leads.extend(leads)

        return all_leads[:max_results]

    def _search_page(self, query: str, page: int, industry: str, seen_emails: set) -> list:
        """Fetch one page of results from yep.co.za."""
        leads = []
        params = {"what": query, "page": page}
        resp = self._get(self.BASE_URL, params=params)
        if not resp:
            return leads

        soup = BeautifulSoup(resp.text, "html.parser")
        next_data = soup.find("script", id="__NEXT_DATA__")
        if not next_data or not next_data.string:
            return leads

        try:
            data = json.loads(next_data.string)
            results = self._find_results(data)
            if not results:
                return leads

            for item in results:
                email = item.get("email", "").strip()
                if not email or email in seen_emails:
                    continue

                name = item.get("name", "").strip()
                if not name:
                    continue

                seen_emails.add(email)
                phones = item.get("phone", []) or item.get("landline", [])
                address = item.get("address", {})
                city = address.get("city", "")
                province = address.get("province", "")
                location = f"{city}, {province}" if city and province else city or province

                categories = item.get("category", [])
                subcategories = item.get("subcategory", [])

                raw_contact = item.get("contact_person", "")
                dm_name, dm_title = self._parse_contact_person(raw_contact)

                leads.append(Lead(
                    company_name=name,
                    email=email,
                    phone=phones[0] if phones else "",
                    industry=subcategories[0] if subcategories else (categories[0] if categories else industry),
                    website=item.get("website", ""),
                    source="google_search",
                    location=location,
                    raw_snippet=item.get("description", ""),
                    scraped_at=datetime.now(),
                    decision_maker_name=dm_name,
                    decision_maker_title=dm_title,
                    linkedin_url="",
                ))

            logger.info("Search '%s' page %d: found %d leads", query, page, len(leads))

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("JSON parse error: %s", e)

        return leads

    def _find_results(self, obj):
        """Recursively find 'results' array in nested JSON."""
        if isinstance(obj, dict):
            if "results" in obj and isinstance(obj["results"], list):
                return obj["results"]
            for v in obj.values():
                r = self._find_results(v)
                if r is not None:
                    return r
        return None
