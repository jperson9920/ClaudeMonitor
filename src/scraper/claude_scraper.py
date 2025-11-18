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
import sys

# Configure module-level logger for scraper diagnostics
logger = logging.getLogger("scraper")
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    log_path = Path("scraper/scraper.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _fh = logging.FileHandler(log_path, encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(_fh)

def _sanitize_diagnostics(diag: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Remove sensitive keys from diagnostics before emitting to stderr/logs."""
    if diag is None:
        return None
    if not isinstance(diag, dict):
        return diag
    sanitized = {}
    sensitive_keys = {"cookies", "set_cookie", "authorization", "auth", "token", "session"}
    for k, v in diag.items():
        if k.lower() in sensitive_keys:
            sanitized[k] = "<redacted>"
        else:
            sanitized[k] = v
    return sanitized

def emit_error(error_code: str, message: str, details: str = None, diagnostics: dict = None, attempts: int = None) -> None:
    """Emit a structured JSON error to stderr and log the event.
    Fields: error_code, message, details (optional), timestamp, attempts, diagnostics (sanitized).
    """
    err = {
        "error_code": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if details:
        err["details"] = str(details)
    if attempts is not None:
        err["attempts"] = attempts
    if diagnostics:
        err["diagnostics"] = _sanitize_diagnostics(diagnostics)
    # Print to stderr for the Rust backend to parse
    print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
    sys.stderr.flush()
    # Also log an explanatory message (no sensitive data)
    logger.error(f"[{error_code}] {message} - details={details} attempts={attempts} diagnostics={bool(diagnostics)}")

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
from .session_manager import save_session, load_session, is_session_expired
# Support multiple execution layouts:
# 1) Package/module import (e.g. `python -m src.scraper.claude_scraper`) -> relative import
# 2) Project root/script import (e.g. `python src/scraper/claude_scraper.py`) -> absolute package import `scraper.retry_handler`
# 3) Script executed from scraper/ directory (e.g. `python claude_scraper.py`) -> local module `retry_handler`
try:
    from .retry_handler import RetryPolicy, with_retry
except Exception:
    try:
        from scraper.retry_handler import RetryPolicy, with_retry
    except Exception:
        from retry_handler import RetryPolicy, with_retry

# Monitoring helper (best-effort import; fallback to no-op)
try:
    from .monitoring import log_event
except Exception:
    def log_event(level, ev): pass

PERCENT_RE = re.compile(r"(\d{1,3})\s*%")
USAGE_URL = "https://claude.ai/settings/usage"
DEFAULT_PROFILE_DIR = "./scraper/chrome-profile"

def cleanup_profile_locks(profile_path: str) -> None:
    """Clean up Chrome profile locks by killing zombie processes and removing lock files.
    
    This fixes the 'session not created: cannot connect to chrome' error caused by
    previous Chrome instances that crashed or were not properly cleaned up.
    """
    if not profile_path:
        return
    
    profile_path = str(Path(profile_path).resolve())
    logger.debug(f'Cleaning up profile locks for: {profile_path}')
    
    # Step 1: Kill zombie Chrome/chromedriver processes
    try:
        import psutil
        killed_count = 0
        skipped_count = 0
        now = time.time()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                cmdline = proc.info.get('cmdline') or []
                cmdline_str = ' '.join(cmdline).lower()
                
                if ('chrome' in (proc.info.get('name') or "").lower() or 'chromedriver' in (proc.info.get('name') or "").lower()):
                    if profile_path.lower() in cmdline_str:
                        # Only kill processes older than 30 seconds to avoid racing with recently-started legitimate processes
                        try:
                            create_ts = float(proc.info.get('create_time') or proc.create_time())
                        except Exception:
                            # If create_time not available, conservatively skip killing
                            create_ts = now
                        age_seconds = now - create_ts
                        if age_seconds > 30:
                            logger.warning(f"Killing zombie process: {proc.info.get('name')} (PID {proc.info.get('pid')}) age={age_seconds:.1f}s")
                            try:
                                proc.kill()
                                proc.wait(timeout=5)
                                killed_count += 1
                            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                                pass
                        else:
                            skipped_count += 1
                            # Log for auditability using structured event log when available.
                            # Emit an INFO-level message so tests and auditors can observe recent-instance skips.
                            try:
                                log_event("info", {"msg": "cleanup_skip_recent", "pid": proc.info.get('pid'), "age": age_seconds})
                            except Exception:
                                logger.info(f"Skipping recently-started Chrome (PID={proc.info.get('pid')}) age={age_seconds:.1f}s")
                            # Also emit debug copy for lower-level diagnostic sinks
                            logger.debug(f"cleanup_skip_recent pid={proc.info.get('pid')} age={age_seconds:.1f}s")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed_count > 0:
            logger.info(f'Killed {killed_count} zombie Chrome/chromedriver process(es)')
            time.sleep(1)
        if skipped_count > 0:
            logger.info(f'Skipped {skipped_count} recent Chrome/chromedriver process(es) (<=30s)')
    except ImportError:
        logger.warning('psutil not available; skipping process cleanup')
    
    # Step 2: Remove lock files
    profile_dir = Path(profile_path)
    if not profile_dir.exists():
        return
    
    lock_files = ['lockfile', 'SingletonLock', 'SingletonSocket', 'SingletonCookie']
    removed_count = 0
    
    for lock_name in lock_files:
        lock_path = profile_dir / lock_name
        if lock_path.exists():
            try:
                lock_path.unlink()
                removed_count += 1
                logger.debug(f'Removed lock file: {lock_name}')
            except Exception as e:
                logger.warning(f'Failed to remove {lock_name}: {e}')
    
    if removed_count > 0:
        logger.info(f'Removed {removed_count} lock file(s) from profile directory')


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
        # Clean up any zombie processes and lock files before creating driver
        # Gate pre-create cleanup behind explicit opt-in to avoid accidental kills on startup
        try:
            if os.getenv("ENABLE_PRE_CREATE_CLEANUP", "false").lower() == "true":
                cleanup_profile_locks(profile_path)
                try:
                    log_event("info", {"msg": "pre_create_cleanup_executed", "profile": profile_path})
                except Exception:
                    logger.info("pre_create_cleanup_executed")
                # Small backoff to let OS settle after killing processes
                time.sleep(1)
            else:
                try:
                    log_event("info", {"msg": "pre_create_cleanup_skipped", "profile": profile_path})
                except Exception:
                    logger.info("pre_create_cleanup_skipped")
        except Exception:
            # Don't let monitoring/logging errors block driver creation
            logger.exception("pre-create cleanup check failed")
        
        # When the caller uses the default profile dir, create a unique per-run
        # user-data-dir to avoid contention/lockfile issues and DevToolsActivePort crashes.
        # If the caller supplied an explicit profile path, preserve it.
        profile_path_resolved = str(Path(profile_path).resolve())
        default_resolved = str(Path(DEFAULT_PROFILE_DIR).resolve())
        if profile_path_resolved == default_resolved:
            import time
            ts = int(time.time())
            unique_dir = str(Path(profile_path_resolved) / f"tmp-repro-{ts}")
            Path(unique_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f'Using unique user-data-dir for this run: {unique_dir}')
            profile_path = unique_dir
        else:
            profile_path = profile_path_resolved

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
        options.add_argument("--remote-debugging-port=0")  # EPIC-TROUBLE-STOR-03: prevent DevToolsActivePort crash
        # Realistic user agent may be set by user profile; leave default otherwise
        # Use subprocess mode to improve compatibility on some Windows setups
        try:
            driver = uc.Chrome(options=options, use_subprocess=True)
        except TypeError:
            # Older uc versions may not accept use_subprocess kwarg
            driver = uc.Chrome(options=options)
        # Expose the selected user_data_dir on the driver object for downstream cleanup/logging
        try:
            setattr(driver, "user_data_dir", profile_path)
        except Exception:
            pass
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
                # EPIC-02-STOR-01: ensure post-quit cleanup to remove profile locks and terminate leftover Chrome processes
                time.sleep(2)  # let Chrome exit and OS release handles
                try:
                    cleanup_profile_locks(profile_path)
                except Exception:
                    logger.exception("post-quit cleanup failed")
            raise

        # Optionally wait a moment for redirects and cookie set
        time.sleep(2)

        # Import structured logging and session helpers locally to avoid circular/top-level import issues
        try:
            from .monitoring import log_event
        except Exception:
            def log_event(*args, **kwargs):  # type: ignore
                logger.debug("log_event fallback: %s %s", args, kwargs)

        try:
            from .session_manager import load_session, save_session, SESSION_FILE_DEFAULT
        except Exception:
            # Fallback names if import fails; preserve original behavior
            load_session = globals().get("load_session")
            save_session = globals().get("save_session")
            SESSION_FILE_DEFAULT = "./scraper/chrome-profile/session.json"

        # Log that we're about to save the session
        log_event("manual_login_saving_session", level="INFO")

        # Save session cookies and metadata
        try:
            save_session(driver)
        except Exception as e:
            # If save_session raises (should be best-effort), log the failure
            log_event("manual_login_save_error", level="ERROR", error=str(e))

        # Validate session was actually saved
        saved_session = load_session()
        # Structured post-save log
        try:
            log_event(
                "manual_login_session_saved",
                level="INFO",
                session_file_exists=saved_session is not None,
                has_cookies=bool(saved_session.get("cookies")) if saved_session else False,
            )
        except Exception:
            logger.info("manual_login: session saved exists=%s has_cookies=%s", saved_session is not None, bool(saved_session.get("cookies")) if saved_session else False)

        if not saved_session or not saved_session.get("cookies"):
            # Emit explicit error event for diagnostics and print a console warning
            log_event(
                "manual_login_save_failed",
                level="ERROR",
                session_file=str(SESSION_FILE_DEFAULT),
                saved_session_is_none=saved_session is None,
                cookie_count=len(saved_session.get("cookies", [])) if saved_session else 0,
            )
            print(f"WARNING: Session may not have been saved correctly. Check {SESSION_FILE_DEFAULT}")

        return saved_session

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
    Uses regex to find all occurrences of '\\d+% used' or '\\d+%'.
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
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Claude usage scraper CLI")
    parser.add_argument("--poll_once", action="store_true", help="Run single poll and exit (used by Rust backend)")
    parser.add_argument("--check-session", action="store_true", help="Check if a saved session exists and is valid")
    parser.add_argument("--login", action="store_true", help="Open headed browser for manual login and save session")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for navigation/challenge resolution (seconds)")
    args = parser.parse_args()

    # Helper to print JSON to stdout
    def out_json(obj):
        print(json.dumps(obj, ensure_ascii=False))
        sys.stdout.flush()

    try:
        if args.check_session:
            sess = load_session()
            ok = sess is not None and not is_session_expired(sess)
            out_json({"session_valid": ok})
            sys.exit(0 if ok else 2)

        if args.login:
            try:
                result = ClaudeUsageScraper.manual_login(profile_path=DEFAULT_PROFILE_DIR)
                out_json({"login": "success", "session": result})
                sys.exit(0)
            except Exception as e:
                logger.exception("manual_login failed")
                emit_error("manual_login_failed", "manual login failed", details=str(e))
                sys.exit(1)

        if args.poll_once:
            # Single-run poll: require a saved session
            sess = load_session()
            if not sess:
                emit_error("session_required", "No valid session", details="no saved session found")
                sys.exit(1)
            driver = None
            try:
                driver = ClaudeUsageScraper.create_driver(headless=False, profile_path=DEFAULT_PROFILE_DIR)

                # EPIC-08-STOR-03 FIX: Restore saved cookies before navigation
                # The issue was that poll_once created a new Chrome profile without restoring the saved session
                from .session_manager import _restore_cookies
                logger.info('Restoring saved session cookies to Chrome instance')
                if sess and sess.get('cookies'):
                    restored = _restore_cookies(driver, sess)
                    if restored:
                        logger.info(f"Successfully restored {len(sess.get('cookies', []))} cookie(s)")
                    else:
                        logger.warning('Failed to restore cookies, authentication may fail')
                # Give cookies time to settle
                import time
                time.sleep(2)

                # Define operation combining navigation and extraction so we can retry it.
                policy = RetryPolicy()  # defaults: 1s initial, 2x multiplier, 4 attempts, 60s max
                def operation():
                    ok = ClaudeUsageScraper.navigate_to_usage(driver, timeout=args.timeout, poll=2.0)
                    if not ok:
                        # navigate_to_usage attaches diagnostics to driver; raise to trigger retry
                        raise RuntimeError("navigation_failed")
                    return ClaudeUsageScraper.extract_live_data(driver)

                try:
                    data = with_retry(operation, policy, on_retry=lambda attempt, delay, exc: logger.warning(f"poll_once retry {attempt} after {delay}s: {exc}"))  # type: ignore
                    out_json(data)
                    sys.exit(0)
                except Exception as e:
                    logger.exception("poll_once failed after retries")
                    diag = getattr(driver, "scraper_diagnostics", None)
                    emit_error("navigation_failed", "navigation or extraction failed after retries", details=str(e), diagnostics=diag)
                    sys.exit(1)
            except Exception as e:
                logger.exception("poll_once failed")
                diag = getattr(driver, "scraper_diagnostics", None)
                emit_error("fatal", "poll_once failed", details=str(e), diagnostics=diag)
                sys.exit(1)
            finally:
                # Decision: keep browser open if manual login appears required
                try:
                    if driver is not None:
                        # Build correlation/run identifiers
                        run_id = int(time.time())
                        profile_path = getattr(driver, "user_data_dir", None) or (sess.get("profile_path") if sess else DEFAULT_PROFILE_DIR)
                        # Log session check start
                        try:
                            log_event("info", {"msg": "session_check_start", "profile": profile_path, "run_id": run_id})
                        except Exception:
                            logger.info(f"session_check_start profile={profile_path} run_id={run_id}")

                        # Perform structured session validation (best-effort)
                        try:
                            from .session_manager import validate_session
                            use_profile = bool(sess.get("profile_path")) if sess else bool(getattr(driver, "user_data_dir", None))
                            result = validate_session(driver, timeout=args.timeout, use_profile=use_profile)
                        except Exception as ex:
                            logger.exception(f"session_check failed: {ex}")
                            result = {"valid": False, "reason": "validation_exception", "requires_manual_login": True}

                        # Log completion
                        try:
                            log_event("info", {"msg": "session_check_complete", "valid": result.get("valid"), "reason": result.get("reason"), "requires_manual": result.get("requires_manual_login"), "run_id": run_id})
                        except Exception:
                            logger.info(f"session_check_complete valid={result.get('valid')} reason={result.get('reason')} requires_manual={result.get('requires_manual_login')} run_id={run_id}")

                        should_close_browser = bool(result.get("valid") and not result.get("requires_manual_login"))

                        if should_close_browser:
                            try:
                                log_event("info", {"msg": "browser_close_decision", "reason": "session_valid_extraction_complete", "run_id": run_id, "profile": profile_path})
                            except Exception:
                                logger.info("browser_close_decision: session_valid_extraction_complete")
                            try:
                                driver.quit()
                            except Exception:
                                pass
                            # EPIC-02-STOR-01: post-quit cleanup to remove profile locks and terminate leftover Chrome processes
                            time.sleep(2)  # let Chrome exit and OS release handles
                            try:
                                profile_path_to_clean = getattr(driver, "user_data_dir", None) or DEFAULT_PROFILE_DIR
                                cleanup_profile_locks(profile_path_to_clean)
                            except Exception:
                                logger.exception("post-quit cleanup failed")
                        else:
                            try:
                                log_event("info", {"msg": "browser_keep_open", "reason": "manual_login_required", "run_id": run_id, "profile": profile_path})
                            except Exception:
                                logger.info("browser_keep_open: manual_login_required")
                            # Intentionally do not quit the driver nor run post-quit cleanup so user can interact with browser
                except Exception:
                    # Ensure no exceptions leak from finally; best-effort only
                    try:
                        if driver is not None:
                            driver.quit()
                    except Exception:
                        pass

        # If no recognized flag, show help
        parser.print_help()
        sys.exit(0)
    except Exception as e:
        logger.exception("cli main failure")
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)