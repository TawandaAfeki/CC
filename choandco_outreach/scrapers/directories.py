import json
import logging
from datetime import datetime

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from leads.models import Lead

logger = logging.getLogger(__name__)


class DirectoryScraper(BaseScraper):
    """Scrape South African business directories for leads.

    Uses yep.co.za (formerly yellowpages.co.za) which embeds structured
    JSON data in __NEXT_DATA__ script tags.
    """

    BASE_URL = "https://www.yep.co.za/search"

    SA_CITIES = [
        "Johannesburg", "Cape Town", "Durban", "Pretoria",
        "Port Elizabeth", "Bloemfontein", "Sandton", "Midrand",
    ]

    def scrape(self, search_queries: list, max_results: int = 10) -> list:
        """Scrape yep.co.za for business leads."""
        all_leads = []

        for query in search_queries:
            for city in self.SA_CITIES:
                if len(all_leads) >= max_results:
                    break
                try:
                    leads = self._search_yep(query, city)
                    all_leads.extend(leads)
                    logger.info("Found %d leads from yep.co.za for '%s' in %s", len(leads), query, city)
                except Exception as e:
                    logger.error("Directory scraper error (%s, %s): %s", query, city, e)

            if len(all_leads) >= max_results:
                break

        return all_leads[:max_results]

    def _search_yep(self, query: str, city: str) -> list:
        """Search yep.co.za and parse the __NEXT_DATA__ JSON."""
        leads = []

        params = {"what": query, "where": city}
        resp = self._get(self.BASE_URL, params=params)
        if not resp:
            return leads

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract structured data from __NEXT_DATA__
        next_data = soup.find("script", id="__NEXT_DATA__")
        if not next_data or not next_data.string:
            logger.debug("No __NEXT_DATA__ found for %s in %s", query, city)
            return leads

        try:
            data = json.loads(next_data.string)
            results = self._find_results(data)
            if not results:
                return leads

            for item in results:
                lead = self._parse_result(item, query)
                if lead:
                    leads.append(lead)

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse yep.co.za JSON: %s", e)

        return leads

    def _find_results(self, obj):
        """Recursively find the 'results' array in nested JSON."""
        if isinstance(obj, dict):
            if "results" in obj and isinstance(obj["results"], list):
                return obj["results"]
            for v in obj.values():
                r = self._find_results(v)
                if r is not None:
                    return r
        return None

    def _parse_result(self, item: dict, query: str) -> Lead | None:
        """Parse a single yep.co.za result into a Lead."""
        name = item.get("name", "").strip()
        if not name:
            return None

        email = item.get("email", "").strip()
        website = item.get("website", "") or ""

        # Extract decision-maker info
        raw_contact = item.get("contact_person", "")
        dm_name, dm_title = self._parse_contact_person(raw_contact)

        # If no direct email, try to derive one from the decision-maker name + domain
        if not email and dm_name and website:
            candidates = self._derive_email_candidates(dm_name, website)
            email = candidates[0] if candidates else ""

        if not email:
            return None

        # Get phone
        phones = item.get("phone", []) or item.get("landline", [])
        phone = phones[0] if phones else ""

        # Get address info
        address = item.get("address", {})
        city = address.get("city", "")
        province = address.get("province", "")
        location = f"{city}, {province}" if city and province else city or province

        # Get category/industry
        categories = item.get("category", [])
        subcategories = item.get("subcategory", [])
        industry = subcategories[0] if subcategories else (categories[0] if categories else query)

        # Get description for context
        description = item.get("description", "")

        return Lead(
            company_name=name,
            email=email,
            phone=phone,
            industry=industry,
            website=website,
            source="yep.co.za",
            location=location,
            raw_snippet=f"{description}. Categories: {', '.join(categories + subcategories)}",
            scraped_at=datetime.now(),
            decision_maker_name=dm_name,
            decision_maker_title=dm_title,
            linkedin_url="",
        )
