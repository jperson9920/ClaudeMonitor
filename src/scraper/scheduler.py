# Scheduler for periodic scraping
import logging
import os
import json
from datetime import datetime
import time
from typing import Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except Exception:
    BackgroundScheduler = None
    IntervalTrigger = None

from .claude_scraper import ClaudeUsageScraper, DEFAULT_PROFILE_DIR

# Try to import optional retry_handler.retry decorator
try:
    from .retry_handler import retry as external_retry
except Exception:
    external_retry = None

logger = logging.getLogger(__name__)

DATA_DIR = os.environ.get("CLAUDE_SCRAPER_DATA_DIR", "./scraper/data")
os.makedirs(DATA_DIR, exist_ok=True)

def _default_retry(retries=3, backoff=2.0):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    logger.exception("Attempt %d/%d failed: %s", attempt, retries, e)
                    if attempt < retries:
                        sleep = backoff * (2 ** (attempt - 1))
                        time.sleep(sleep)
            raise last_exc
        return wrapped
    return decorator

# Choose retry decorator: prefer external if available (integration point)
if external_retry is not None:
    retry = external_retry
else:
    def retry(retries=3, backoff=2.0):
        return _default_retry(retries, backoff)

class ScraperScheduler:
    """
    Programmatic scheduler for running ClaudeUsageScraper periodically.

    Usage:
      from src.scraper.scheduler import ScraperScheduler
      s = ScraperScheduler(interval_minutes=5)
      s.start()
      ...
      s.stop()
    """

    def __init__(self, interval_minutes: int = 5, profile_path: Optional[str] = DEFAULT_PROFILE_DIR):
        self.interval_minutes = interval_minutes
        self.profile_path = profile_path
        if BackgroundScheduler is None:
            raise RuntimeError("APScheduler is not available; install apscheduler to use ScraperScheduler")
        self._sched = BackgroundScheduler()
        self._job = None

    @retry(retries=3, backoff=2.0)
    def _run_scrape(self):
        logger.info("Starting scrape run")
        driver = None
        try:
            # Create driver using same profile path so saved cookies/session are reused
            driver = ClaudeUsageScraper.create_driver(headless=False, profile_path=self.profile_path)
            ok = ClaudeUsageScraper.navigate_to_usage(driver, timeout=30, poll=2.0)
            if not ok:
                raise RuntimeError("Failed to navigate to usage page or challenge not cleared")
            payload = ClaudeUsageScraper.extract_live_data(driver)
            # Add collector timestamp (UTC ISO)
            collected_at = datetime.utcnow().isoformat() + "Z"
            record = {
                "collected_at": collected_at,
                "payload": payload,
            }
            fname = os.path.join(DATA_DIR, f"usage_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json")
            with open(fname, "w", encoding="utf-8") as fh:
                json.dump(record, fh, indent=2, ensure_ascii=False)
            logger.info("Scrape succeeded, stored results to %s", fname)
            return record
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    logger.exception("Error quitting driver")

    def start(self):
        if self._sched.running:
            logger.info("Scheduler already running")
            return
        trigger = IntervalTrigger(minutes=self.interval_minutes)
        self._job = self._sched.add_job(self._run_scrape, trigger, id="claude_usage_scrape", replace_existing=True)
        self._sched.start()
        logger.info("Scheduler started with interval %d minutes", self.interval_minutes)

    def stop(self, wait: bool = False):
        if not self._sched.running:
            logger.info("Scheduler not running")
            return
        try:
            self._sched.remove_job("claude_usage_scrape")
        except Exception:
            pass
        self._sched.shutdown(wait=wait)
        logger.info("Scheduler stopped")

    def is_running(self) -> bool:
        return getattr(self._sched, "running", False)

def create_and_start(interval_minutes: int = 5, profile_path: Optional[str] = DEFAULT_PROFILE_DIR) -> ScraperScheduler:
    s = ScraperScheduler(interval_minutes=interval_minutes, profile_path=profile_path)
    s.start()
    return s