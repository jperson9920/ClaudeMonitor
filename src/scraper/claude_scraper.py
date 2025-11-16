"""
Claude usage scraper - high level orchestration with live browser support.

Provides:
- ClaudeUsageScraper.extract_usage_data() -> dict (HTML-mode)
- create_driver(headless=False) -> selenium webdriver (undetected-chromedriver)
- manual_login() -> open headed browser, wait for user to authenticate and save session
- navigate_to_usage() -> navigate and handle Cloudflare challenges
- extract_live_data(driver) -> run extractor against live page_source
- ClaudeUsageScraper.dump_json(path)
- fallback helper extract_from_text(page_source)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import re
import os
import time
from pathlib import Path
import logging

# Configure module-level logger for scraper diagnostics
logger = logging.getLogger("scraper")
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    log_path = Path("scraper/scraper.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _fh = logging.FileHandler(log_path, encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(_fh)

# Selenium / undetected-chromedriver imports
try:
    import undetected_chromedriver as uc
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.common.by import By
except Exception:
    uc = None  # will raise at runtime if used
    WebDriverException = Exception
    By = None

from .extractors import UsageExtractor
from .models import UsageComponent
from .session_manager import save_session, load_session

PERCENT_RE = re.compile(r"(\d{1,3})\s*%")
USAGE_URL = "https://claude.ai/settings/usage"
DEFAULT_PROFILE_DIR = "./scraper/chrome-profile"

class ClaudeUsageScraper:
    def __init__(self, html: str):
        self.html = html
        self.extractor = UsageExtractor(html)

    @staticmethod
    def create_driver(headless: bool = False, profile_path: str = DEFAULT_PROFILE_DIR):
        """
        Create an undetected-chromedriver instance configured for headed operation
        (headless=False as required by EPIC-02-STOR-02) with anti-detection flags.

        Note: caller must ensure undetected-chromedriver is installed.
        """
        if uc is None:
            raise RuntimeError("undetected-chromedriver is not available; install undetected-chromedriver and selenium")

        options = uc.ChromeOptions()
        # Use a persistent user-data-dir so cookies/sessions can be preserved
        profile_path = str(Path(profile_path).resolve())
        options.add_argument(f"--user-data-dir={profile_path}")
        # Headed mode per acceptance criteria
        if headless:
            options.add_argument("--headless=new")
        # Anti-detection and pragmatic flags
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1200,900")
        # Realistic user agent may be set by user profile; leave default otherwise
        # Use subprocess mode to improve compatibility on some Windows setups
        try:
            driver = uc.Chrome(options=options, use_subprocess=True)
        except TypeError:
            # Older uc versions may not accept use_subprocess kwarg
            driver = uc.Chrome(options=options)
        return driver

    @staticmethod
    def is_challenge_page(driver) -> bool:
        """
        Rudimentary Cloudflare challenge detection by looking for known phrases or short-circuit selectors.
        """
        try:
            src = driver.page_source or ""
            if "Checking your browser" in src or "Just a moment" in src or "Please enable JavaScript" in src:
                return True
            # Cloudflare sometimes displays an element with id="cf-challenge" or class "cf-browser-verification"
            if By is not None:
                try:
                    if driver.find_elements(By.ID, "cf-challenge"):
                        return True
                    if driver.find_elements(By.CLASS_NAME, "cf-browser-verification"):
                        return True
                except Exception:
                    pass
            return False
        except Exception:
            return False

    @classmethod
    def navigate_to_usage(
        cls,
        driver,
        timeout: int = 60,
        poll: float = 2.0,
        initial_delay: float = 1.0,
        multiplier: float = 2.0,
        max_attempts: int = 4,
    ) -> bool:
        """
        Navigate to USAGE_URL with Cloudflare-challenge awareness and an exponential-backoff
        retry strategy for navigation attempts.

        Returns True if navigation succeeded and page appears usable, False otherwise.

        Side-effect: attaches a diagnostics dict to the driver object as
        driver.scraper_diagnostics (when possible) so callers can inspect
        what happened (e.g., {'cloudflare_detected': True, 'retries': 2})
        """
        diagnostics: Dict[str, Any] = {"cloudflare_detected": False, "retries": 0, "error": None}
        # Helper to attach diagnostics when driver is available
        def _attach(diag: Dict[str, Any]) -> None:
            try:
                setattr(driver, "scraper_diagnostics", diag)
            except Exception:
                # best-effort only
                pass

        attempt = 0
        delay = initial_delay

        while attempt < max_attempts:
            attempt += 1
            diagnostics["attempt"] = attempt
            logger.debug(f"navigate_to_usage: attempt {attempt} navigating to {USAGE_URL}")
            try:
                driver.get(USAGE_URL)
            except WebDriverException as ex:
                diagnostics["error"] = "navigation_exception"
                diagnostics["exception"] = str(ex)
                logger.warning(f"navigate_to_usage: navigation exception on attempt {attempt}: {ex}")
                _attach(diagnostics)
                # fall through to retry after backoff
            start = time.time()
            # Wait for challenge resolution / successful page appearance
            while time.time() - start < timeout:
                try:
                    if not cls.is_challenge_page(driver):
                        diagnostics["cloudflare_detected"] = False
                        diagnostics["retries"] = attempt - 1
                        _attach(diagnostics)
                        logger.debug("navigate_to_usage: page usable, exiting wait loop")
                        return True
                    else:
                        # mark that we saw a challenge
                        diagnostics["cloudflare_detected"] = True
                        _attach(diagnostics)
                        logger.info("navigate_to_usage: Cloudflare/challenge detected; polling for resolution")
                except Exception as ex:
                    logger.exception(f"navigate_to_usage: error during challenge detection: {ex}")
                time.sleep(poll)

            # If we reach here, the wait timed out without resolving the challenge
            diagnostics["retries"] = attempt
            logger.warning(f"navigate_to_usage: attempt {attempt} timed out waiting for challenge resolution")
            _attach(diagnostics)

            if attempt < max_attempts:
                logger.debug(f"navigate_to_usage: backing off for {delay}s before retry #{attempt+1}")
                time.sleep(delay)
                delay *= multiplier
            else:
                diagnostics["error"] = "navigation_failed"
                logger.error("navigate_to_usage: max attempts reached; navigation failed")
                _attach(diagnostics)
                return False

        # Defensive fallback
        diagnostics["error"] = "navigation_failed"
        _attach(diagnostics)
        return False

    @classmethod
    def manual_login(cls, driver=None, profile_path: str = DEFAULT_PROFILE_DIR) -> dict:
        """
        Open a headed browser for manual login and save session cookies.
        Caller should instruct user not to close the browser window used by the scraper.
        Returns saved session dict on success.
        """
        created = False
        if driver is None:
            driver = cls.create_driver(headless=False, profile_path=profile_path)
            created = True

        # Open the usage page which also serves as a login landing
        driver.get(USAGE_URL)

        # Wait for user to perform interactive login (CAPTCHA/2FA) and press Enter in terminal
        print("Manual login required. Please authenticate in the opened browser window.")
        print("Do NOT close the browser window used by the scraper. After login completes, press Enter here to continue.")
        try:
            input("Press Enter after login is complete...")
        except KeyboardInterrupt:
            # User cancelled
            if created:
                try:
                    driver.quit()
                except Exception:
                    pass
            raise

        # Optionally wait a moment for redirects and cookie set
        time.sleep(2)
        # Save session cookies and metadata
        save_session(driver)
        return load_session()

    @classmethod
    def extract_live_data(cls, driver) -> Dict[str, Any]:
        """
        Extract usage data from the live page by reading page_source and delegating to UsageExtractor.
        Returns same structured output as extract_usage_data() but constructed from live HTML.
        """
        page_source = driver.page_source or ""
        extractor = UsageExtractor(page_source)
        scraped = extractor.extract_all()
        # Build a lightweight ClaudeUsageScraper instance from HTML to reuse normalization logic
        inst = cls(page_source)
        inst.extractor = extractor
        return inst.extract_usage_data()

    def extract_usage_data(self) -> Dict[str, Any]:
        """
        Existing HTML-only extraction; kept for compatibility.
        """
        scraped = self.extractor.extract_all()
        components = []
        found = 0
        diagnostics = {"selectors_attempted": []}
        status = "ok"

        for item in scraped:
            comp_id = item.get("component_id")
            label = item.get("label")
            percent = item.get("percent")
            raw_text = item.get("raw_text", "")
            scraped_at = item.get("scraped_at") or datetime.utcnow()
            selector_used = item.get("selector_used")
            if selector_used:
                diagnostics["selectors_attempted"].append({comp_id: selector_used})

            if percent is not None:
                found += 1

            # Build plain dicts to avoid Pydantic serialization differences across environments
            comp_dict = {
                "component_id": comp_id,
                "label": label,
                "percent": percent,
                "raw_text": raw_text,
                "scraped_at": scraped_at,
            }
            components.append(comp_dict)

        if found < len(components):
            status = "partial"
        if found == 0:
            status = "error"

        # Normalize components to plain dicts and convert datetimes to ISO strings
        normalized = []
        for c in components:
            # c may already be a dict or a Pydantic model; handle both
            if hasattr(c, "dict"):
                cd = c.dict()
            else:
                cd = dict(c)
            sa = cd.get("scraped_at")
            if isinstance(sa, datetime):
                cd["scraped_at"] = sa.isoformat() + "Z"
            normalized.append(cd)

        return {
            "components": normalized,
            "found_components": found,
            "status": status,
            "diagnostics": diagnostics,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def dump_json(self, path: str) -> None:
        payload = self.extract_usage_data()
        # Convert datetime objects to ISO strings inside components
        for c in payload["components"]:
            if isinstance(c.get("scraped_at"), datetime):
                c["scraped_at"] = c["scraped_at"].isoformat() + "Z"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload["components"], fh, indent=2, ensure_ascii=False)


def extract_from_text(page_source: str) -> List[Dict[str, Any]]:
    """
    Fallback text extractor: returns list of found {raw_text, percent}
    Uses regex to find all occurrences of '\d+% used' or '\d+%'.
    """
    results = []
    for m in PERCENT_RE.finditer(page_source or ""):
        txt = m.group(0)
        try:
            pct = float(m.group(1))
        except Exception:
            pct = None
        results.append({"raw_text": txt, "percent": pct})
    return results