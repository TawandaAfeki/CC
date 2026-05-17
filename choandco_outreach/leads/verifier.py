import logging
import re
import dns.resolver
from typing import Optional

from leads.models import Lead

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Known invalid or placeholder domains
SKIP_DOMAINS = {"example.com", "test.com", "localhost", "invalid.com"}


def verify_email(email: str) -> bool:
    """
    Verify an email address is likely valid by:
    1. Syntax check (valid format)
    2. Domain structure check (has proper TLD like .co.za not .coza)
    3. MX record lookup (domain actually accepts email)
    """
    email = email.strip().lower()

    # Step 1: Syntax
    if not EMAIL_PATTERN.match(email):
        logger.debug("Failed syntax check: %s", email)
        return False

    domain = email.split("@")[1]

    if domain in SKIP_DOMAINS:
        return False

    # Step 2: Domain structure check
    # Catch common directory typos like "company.coza" instead of "company.co.za"
    if domain.endswith("coza") and not domain.endswith(".co.za"):
        logger.info("Bad domain (missing dot): %s", email)
        return False
    if domain.endswith("coза") and not domain.endswith(".co.za"):
        return False

    # Step 3: MX record check - does the domain accept email?
    if not _has_mx_record(domain):
        logger.info("No MX record for domain: %s (%s)", domain, email)
        return False

    return True


def _has_mx_record(domain: str) -> bool:
    """
    Check if a domain has valid MX records AND that the MX host actually
    resolves to a real IP address.
    Fails closed — any timeout or unresolvable host returns False.
    """
    try:
        records = dns.resolver.resolve(domain, "MX")
        if not records:
            return False

        # Pick the highest-priority (lowest preference number) MX host
        mx_host = str(min(records, key=lambda r: r.preference).exchange).rstrip(".")

        # Confirm the MX host resolves to a real A record (not DNSNULL)
        try:
            dns.resolver.resolve(mx_host, "A")
            return True
        except Exception:
            logger.warning("MX host %s for %s does not resolve — treating as invalid", mx_host, domain)
            return False

    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return False
    except dns.resolver.LifetimeTimeout:
        # Fail closed — a domain whose DNS times out cannot be trusted
        logger.warning("MX lookup timed out for %s — treating as invalid", domain)
        return False
    except Exception as e:
        logger.warning("MX lookup error for %s: %s — treating as invalid", domain, e)
        return False


def verify_leads(leads: list) -> list:
    """Filter leads to only those with verified email addresses."""
    verified = []
    for lead in leads:
        if verify_email(lead.email):
            verified.append(lead)
        else:
            logger.info("Removed invalid email: %s (%s)", lead.email, lead.company_name)
    logger.info("Email verification: %d/%d passed", len(verified), len(leads))
    return verified
