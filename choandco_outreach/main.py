import logging
import random
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    EMAIL_DELAY_RANGE, MAX_EMAILS_PER_RUN, INDUSTRIES, LOG_PATH,
    SMTP_USER, SMTP_PASSWORD, SUMMARY_RECIPIENT,
)
from scrapers.google_search import GoogleSearchScraper
from scrapers.directories import DirectoryScraper
from scrapers.google_maps import GoogleMapsScraper
from scrapers.linkedin import LinkedInScraper
from leads.dedup import deduplicate_leads, mark_sent
from leads.qualifier import qualify
from leads.verifier import verify_leads
from leads.sequence import run_followup_stage
from email_engine.composer import compose_email
from email_engine.sender import send_with_retry, send_email
from tracking.logger import init_workbook, log_email, get_todays_count
from tracking.summary import send_daily_summary

logger = logging.getLogger("choandco_outreach")


def setup_logging():
    """Configure logging to console and rotating file."""
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler
    file_handler = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Apply to all child loggers
    logging.basicConfig(level=logging.INFO, handlers=[console, file_handler])


def build_search_queries() -> list:
    """Select 3 industries for this run, rotating by day."""
    day_of_year = datetime.now().timetuple().tm_yday
    start_idx = (day_of_year * 3) % len(INDUSTRIES)
    selected = []
    for i in range(3):
        idx = (start_idx + i) % len(INDUSTRIES)
        selected.append(INDUSTRIES[idx])
    logger.info("Today's target industries: %s", selected)
    return selected


def _send_start_notification():
    """Send a short email to notify that the outreach run has started."""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        send_email(
            SUMMARY_RECIPIENT,
            f"Cho&Co Outreach Agent Started - {now}",
            f"Hi Tawanda,\n\nThe Cho&Co outreach agent has started a new run at {now}.\n\nYou will receive another email with the results and Excel log once it finishes.\n",
        )
        logger.info("Start notification sent to %s", SUMMARY_RECIPIENT)
    except Exception as e:
        logger.warning("Could not send start notification: %s", e)


def run_all_followups(max_per_stage: int = 10) -> int:
    """Run all 3 follow-up stages before starting new outreach. Returns total sent."""
    total = 0
    for stage in ["followup1", "followup2", "followup3"]:
        try:
            sent = run_followup_stage(stage, max_emails=max_per_stage)
            total += sent
            logger.info("Follow-up stage %s: %d emails sent", stage, sent)
        except Exception as e:
            logger.error("Follow-up stage %s failed: %s", stage, e)
    return total


def _send_completion_notification(sent_count: int, total_leads: int, industries: list, followup_count: int = 0):
    """Send a short email with run results."""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        industry_list = ", ".join(industries)
        send_email(
            SUMMARY_RECIPIENT,
            f"Cho&Co Outreach Agent Complete - {sent_count + followup_count} emails sent",
            (
                f"Hi Tawanda,\n\n"
                f"The outreach run has finished at {now}.\n\n"
                f"Results:\n"
                f"- New outreach emails sent: {sent_count}\n"
                f"- Follow-up emails sent: {followup_count}\n"
                f"- Total emails this run: {sent_count + followup_count}\n"
                f"- Total leads found: {total_leads}\n"
                f"- Industries targeted: {industry_list}\n\n"
                f"The updated Excel log is attached in a separate email.\n"
            ),
        )
        logger.info("Completion notification sent to %s", SUMMARY_RECIPIENT)
    except Exception as e:
        logger.warning("Could not send completion notification: %s", e)


def run():
    """Execute the full outreach pipeline."""
    setup_logging()
    logger.info("=" * 60)
    logger.info("Cho&Co Outreach Agent - Run started at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    # Validate credentials
    if not SMTP_USER or not SMTP_PASSWORD or SMTP_PASSWORD == "your_password_here":
        logger.critical("SMTP credentials not configured. Please update the .env file.")
        return

    # Initialize workbook (migrates legacy schema if needed)
    init_workbook()

    # Notify that the run has started
    _send_start_notification()

    # Run follow-up sequences FIRST — warm leads take priority
    followup_count = run_all_followups(max_per_stage=10)
    logger.info("Follow-up phase complete: %d total follow-up emails sent", followup_count)

    # Check daily cap
    already_sent = get_todays_count()
    remaining = MAX_EMAILS_PER_RUN - already_sent
    if remaining <= 0:
        logger.info("Daily email cap reached (%d sent today). Skipping.", already_sent)
        send_daily_summary()
        return

    # Build search queries
    queries = build_search_queries()

    # Run scrapers sequentially (respecting rate limits)
    all_leads = []
    scrapers = [
        ("Directories", DirectoryScraper),
        ("Google Search", GoogleSearchScraper),
        ("Google Maps", GoogleMapsScraper),
        ("LinkedIn", LinkedInScraper),
    ]

    for name, scraper_cls in scrapers:
        try:
            logger.info("Running %s scraper...", name)
            scraper = scraper_cls()
            leads = scraper.scrape(queries, max_results=15)
            all_leads.extend(leads)
            logger.info("%s scraper returned %d leads", name, len(leads))
        except Exception as e:
            logger.error("%s scraper failed: %s", name, e)

    logger.info("Total raw leads: %d", len(all_leads))

    if not all_leads:
        logger.warning("No leads found. Check your internet connection and scraper configuration.")
        send_daily_summary()
        return

    # Deduplicate
    unique_leads = deduplicate_leads(all_leads)
    logger.info("After deduplication: %d leads", len(unique_leads))

    # Qualify
    qualified_leads = qualify(unique_leads)
    logger.info("After qualification: %d leads", len(qualified_leads))

    # Verify email addresses exist before sending
    verified_leads = verify_leads(qualified_leads)
    logger.info("After email verification: %d leads", len(verified_leads))
    qualified_leads = verified_leads

    if not qualified_leads:
        logger.info("No qualified leads this run.")
        send_daily_summary()
        return

    # Cap to remaining daily limit
    batch = qualified_leads[:remaining]
    logger.info("Sending emails to %d leads", len(batch))

    # Send emails
    sent_count = 0
    for i, lead in enumerate(batch, 1):
        try:
            subject, body = compose_email(lead)
            logger.info("[%d/%d] Sending to %s (%s)...", i, len(batch), lead.company_name, lead.email)

            success = send_with_retry(lead.email, subject, body)
            if success:
                mark_sent(lead, original_subject=subject)
                log_email(lead, datetime.now(), original_subject=subject)
                sent_count += 1
                logger.info("Successfully sent to %s", lead.email)
            else:
                logger.warning("Failed to send to %s after retries", lead.email)

            # Delay between emails
            if i < len(batch):
                delay = random.uniform(*EMAIL_DELAY_RANGE)
                logger.info("Waiting %.0f seconds before next email...", delay)
                time.sleep(delay)

        except Exception as e:
            logger.error("Error processing lead %s: %s", lead.company_name, e)

    logger.info("Run complete. Sent %d/%d emails.", sent_count, len(batch))

    # Send completion notification and daily summary
    _send_completion_notification(sent_count, len(all_leads), queries, followup_count=followup_count)
    send_daily_summary()

    # Trigger demo generator for any new industries found in this batch
    try:
        from demo_generator.main import run as run_demo_generator
        run_demo_generator()
    except Exception as demo_err:
        logger.error("Demo generator encountered an error: %s", demo_err)

    logger.info("=" * 60)
    logger.info("Cho&Co Outreach Agent - Run completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
