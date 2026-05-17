import json
import logging
from datetime import datetime

from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from leads.models import Lead

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Find businesses using additional yep.co.za search categories.

    Uses broader business-related search terms to find companies that
    might not appear under specific industry searches.
    """

    BASE_URL = "https://www.yep.co.za/search"

    SEARCH_TERMS = [
        "{industry} management",
        "{industry} consulting",
        "{industry} agency",
        "{industry} group",
        "{industry} trading",
        "{industry} distributors",
    ]

    SA_CITIES = ["Johannesburg", "Cape Town", "Durban", "Pretoria"]

    def scrape(self, search_queries: list, max_results: int = 10) -> list:
        """Search using business-type variations."""
        all_leads = []
        seen_emails = set()

        for industry in search_queries:
            if len(all_leads) >= max_results:
                break

            for term in self.SEARCH_TERMS:
                if len(all_leads) >= max_results:
                    break

                query = term.format(industry=industry)

                for city in self.SA_CITIES:
                    if len(all_leads) >= max_results:
                        break

                    leads = self._search(query, city, industry, seen_emails)
                    all_leads.extend(leads)

        return all_leads[:max_results]

    def _search(self, query: str, city: str, industry: str, seen_emails: set) -> list:
        """Search yep.co.za for a specific query in a city."""
        leads = []
        params = {"what": query, "where": city}
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
                    source="linkedin",
                    location=location,
                    raw_snippet=item.get("description", ""),
                    scraped_at=datetime.now(),
                    decision_maker_name=dm_name,
                    decision_maker_title=dm_title,
                    linkedin_url="",
                ))

            if leads:
                logger.info("LinkedIn scraper: found %d leads for '%s' in %s", len(leads), query, city)

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("JSON parse error in LinkedIn scraper: %s", e)

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
