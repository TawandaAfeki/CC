import json
import logging
from datetime import datetime

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from leads.models import Lead

logger = logging.getLogger(__name__)


class GoogleMapsScraper(BaseScraper):
    """Find local businesses via yep.co.za location-based search.

    Uses city-specific searches with pagination to find businesses
    that weren't captured by the broader industry searches.
    """

    BASE_URL = "https://www.yep.co.za/search"

    SA_CITIES = [
        "Stellenbosch", "George", "Nelspruit", "Polokwane",
        "Kimberley", "Pietermaritzburg", "East London", "Richards Bay",
        "Centurion", "Randburg", "Roodepoort", "Midrand",
    ]

    def scrape(self, search_queries: list, max_results: int = 10) -> list:
        """Search for businesses in smaller SA cities (secondary markets)."""
        all_leads = []
        seen_emails = set()

        for industry in search_queries:
            if len(all_leads) >= max_results:
                break

            for city in self.SA_CITIES:
                if len(all_leads) >= max_results:
                    break

                leads = self._search_city(industry, city, seen_emails)
                all_leads.extend(leads)
                if leads:
                    logger.info("Maps scraper: found %d leads for '%s' in %s", len(leads), industry, city)

        return all_leads[:max_results]

    def _search_city(self, industry: str, city: str, seen_emails: set) -> list:
        """Search yep.co.za for a specific industry in a specific city."""
        leads = []
        params = {"what": industry, "where": city}
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
                addr_city = address.get("city", city)
                province = address.get("province", "")
                location = f"{addr_city}, {province}" if addr_city and province else addr_city or province

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
                    source="google_maps",
                    location=location,
                    raw_snippet=item.get("description", ""),
                    scraped_at=datetime.now(),
                    decision_maker_name=dm_name,
                    decision_maker_title=dm_title,
                    linkedin_url="",
                ))

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("JSON parse error in maps scraper: %s", e)

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
