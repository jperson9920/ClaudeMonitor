from pathlib import Path
import json
import time
import logging
import re
from typing import Optional, Dict, Any

SESSION_FILE_DEFAULT = Path("./scraper/chrome-profile/session.json")

logger = logging.getLogger("scraper")


def _ensure_profile_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_session(driver, session_file: str = str(SESSION_FILE_DEFAULT)) -> None:
    """
    Save driver cookies and minimal metadata to session_file atomically.
    Best-effort: does not fail on non-critical errors.
    """
    sf = Path(session_file)
    _ensure_profile_dir(sf)

    # Structured start event for diagnostics
    try:
        from .monitoring import log_event
    except Exception:
        # Fallback to logger if structured logger not available
        def log_event(*args, **kwargs):  # type: ignore
            logger.debug("log_event fallback: %s %s", args, kwargs)

    log_event("session_save_start", level="DEBUG", session_file=session_file)

    session: Dict[str, Any] = {
        "timestamp": int(time.time()),
        "cookies": [],
        "user_agent": None,
        "profile_path": None,
    }

    try:
        session["cookies"] = driver.get_cookies() or []
    except Exception as e:
        # best-effort capture with explicit error logging for diagnostics
        log_event("session_save_error", level="ERROR", component="cookies", error=str(e))
    else:
        # Log cookie capture immediately for diagnostics
        cookie_count = len(session.get("cookies", []))
        log_event("session_cookies_captured", level="DEBUG", cookie_count=cookie_count)

    try:
        ua = driver.execute_script("return navigator.userAgent")
        session["user_agent"] = ua
    except Exception as e:
        log_event("session_save_error", level="ERROR", component="user_agent", error=str(e))

    # Try to capture profile path if driver exposes it
    try:
        profile_path = getattr(driver, "user_data_dir", None)
        if profile_path:
            session["profile_path"] = str(profile_path)
    except Exception as e:
        log_event("session_save_error", level="ERROR", component="profile_path", error=str(e))

    # Persist atomically, but log any file write failures
    tmp = sf.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(session, fh, indent=2, ensure_ascii=False)
        tmp.replace(sf)
    except Exception as e:
        log_event("session_save_error", level="ERROR", component="file_write", error=str(e))
        # best-effort: do not raise to preserve existing behavior

    # Final success/info event with metadata
    try:
        log_event(
            "session_save_complete",
            level="INFO",
            session_file=str(sf),
            cookie_count=len(session.get("cookies", [])),
            has_user_agent=bool(session.get("user_agent")),
            profile_path=session.get("profile_path"),
        )
    except Exception:
        logger.info(
            "save_session: saved session to %s cookies=%d ua=%s profile=%s",
            str(sf),
            len(session.get("cookies", [])),
            bool(session.get("user_agent")),
            session.get("profile_path"),
        )


def load_session(session_file: str = str(SESSION_FILE_DEFAULT)) -> Optional[Dict[str, Any]]:
    sf = Path(session_file)
    if not sf.exists():
        return None
    try:
        with sf.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def is_session_expired(session_data: Dict[str, Any], max_age_days: int = 7) -> bool:
    if not session_data or "timestamp" not in session_data:
        return True
    try:
        age = int(time.time()) - int(session_data.get("timestamp", 0))
        return age > int(max_age_days) * 86400
    except Exception:
        return True


def validate_session(driver, timeout: int = 60, use_profile: bool = False) -> Dict[str, object]:
    """
    Validate an active browser session and return structured result.

    Returns:
      {"valid": bool, "reason": str, "requires_manual_login": bool}
    """
    # Default failure result
    def _fail(reason: str, manual: bool = True) -> Dict[str, object]:
        try:
            log_event("warning", {"msg": "validate_session_result", "valid": False, "reason": reason, "requires_manual_login": manual})
        except Exception:
            logger.debug(f"validate_session: result(valid=False reason={reason} requires_manual={manual})")
        return {"valid": False, "reason": reason, "requires_manual_login": manual}

    try:
        # local import to avoid circular top-level imports
        try:
            from .claude_scraper import USAGE_URL, ClaudeUsageScraper
        except Exception:
            USAGE_URL = "https://claude.ai/settings/usage"
            ClaudeUsageScraper = None

        # Quick-profile based check: prefer explicit session cookie presence
        if use_profile:
            try:
                cookies = {c.get("name"): c for c in (driver.get_cookies() or [])}
                sk = cookies.get("sessionKey")
                if sk:
                    expiry = sk.get("expiry", 0) or 0
                    if int(expiry) > int(time.time()):
                        # Still require an explicit UI indicator after navigation to be confident
                        logger.debug("validate_session: sessionKey cookie present and not expired; performing quick UI verify")
                        if ClaudeUsageScraper:
                            success = ClaudeUsageScraper.navigate_to_usage(driver, timeout=30, poll=2.0)
                            if success:
                                # Confirm explicit indicators in page source
                                try:
                                    src = (getattr(driver, "page_source", "") or "").lower()
                                    has_percentage = bool(re.search(r"\d{1,3}\s*%", src))
                                    has_usage_text = "usage" in src and "limit" in src
                                    if has_percentage or has_usage_text:
                                        return {"valid": True, "reason": "logged_in", "requires_manual_login": False}
                                    else:
                                        return _fail("no_login_indicators_after_quick_nav", True)
                                except Exception as ex:
                                    logger.debug(f"validate_session: error inspecting page after quick nav: {ex}")
                                    return _fail("inspection_error", True)
                        else:
                            try:
                                driver.get(USAGE_URL)
                                time.sleep(2)
                                cur = (getattr(driver, "current_url", "") or "").lower()
                                if "login" not in cur and "signin" not in cur:
                                    # Still mark as valid only if explicit indicators present
                                    src = (getattr(driver, "page_source", "") or "").lower()
                                    if re.search(r"\d{1,3}\s*%", src) or ("usage" in src and "limit" in src):
                                        return {"valid": True, "reason": "logged_in", "requires_manual_login": False}
                                    else:
                                        return _fail("no_login_indicators_after_quick_nav", True)
                                else:
                                    return _fail("login_url_detected", True)
                            except Exception as ex:
                                logger.debug(f"validate_session: quick profile nav failed: {ex}")
                                return _fail("navigation_error", True)
            except Exception as ex:
                logger.debug(f"validate_session: error during quick profile cookie check: {ex}")
                # continue to full validation

        logger.debug("validate_session: performing full Cloudflare-aware validation")

        # Use ClaudeUsageScraper.navigate_to_usage to handle Cloudflare
        if ClaudeUsageScraper:
            success = ClaudeUsageScraper.navigate_to_usage(
                driver,
                timeout=timeout,
                poll=2.0,
                initial_delay=1.0
            )

            if not success:
                logger.debug("validate_session: navigate_to_usage failed (challenge timeout or navigation error)")
                return _fail("navigation_failed", True)

            # After successful navigation, require explicit UI indicators
            logger.debug("validate_session: navigation succeeded, performing final session check")
            inspection_timeout = 10
            start = time.time()
            while time.time() - start < inspection_timeout:
                try:
                    src = (getattr(driver, "page_source", "") or "").lower()
                    if "sign in" in src or "log in" in src or "please sign in" in src:
                        logger.debug("validate_session: detected sign-in markers after navigation")
                        return _fail("sign_in_markers", True)
                    has_percentage = bool(re.search(r"\d{1,3}\s*%", src))
                    has_usage_text = "usage" in src and "limit" in src
                    if has_percentage or has_usage_text:
                        logger.debug(f"validate_session: success (percentage={has_percentage}, usage_text={has_usage_text})")
                        try:
                            log_event("info", {"msg": "validate_session_success", "indicators": "chat_ui_present"})
                        except Exception:
                            logger.info("validate_session: validate success")
                        return {"valid": True, "reason": "logged_in", "requires_manual_login": False}
                except Exception as ex:
                    logger.debug(f"validate_session: error during final inspection: {ex}")
                time.sleep(1)

            # For persistent profile, be conservative: prefer keeping browser open for manual verification
            if use_profile:
                logger.warning("validate_session: inspection timeout without indicators; treating as manual-login-required for profile session")
                return _fail("no_login_indicators", True)

            logger.debug("validate_session: inspection timeout without success indicators")
            return _fail("no_login_indicators", True)
        else:
            # Fallback simple navigation path
            logger.warning("validate_session: ClaudeUsageScraper not available, using simple navigation")
            try:
                driver.get(USAGE_URL)
            except Exception as ex:
                logger.warning(f"validate_session: driver.get failed: {ex}")
                return _fail("navigation_error", True)

            start = time.time()
            while time.time() - start < timeout:
                try:
                    src = (getattr(driver, "page_source", "") or "").lower()
                    if "sign in" in src or "log in" in src or "please sign in" in src:
                        return _fail("sign_in_markers", True)
                    has_percentage = bool(re.search(r"\d{1,3}\s*%", src))
                    has_usage_text = "usage" in src and "limit" in src
                    if has_percentage or has_usage_text:
                        return {"valid": True, "reason": "logged_in", "requires_manual_login": False}
                except Exception as ex:
                    logger.debug(f"validate_session: error while inspecting page: {ex}")
                time.sleep(1)

            cur = (getattr(driver, "current_url", "") or "").lower()
            if "login" in cur or "signin" in cur:
                return _fail("login_url_detected", True)

            if use_profile:
                logger.warning("validate_session: timeout without login markers; treating as manual-login-required for profile-based session")
                return _fail("no_login_indicators", True)

            logger.debug("validate_session: timeout reached without conclusive login markers; assume invalid")
            return _fail("no_login_indicators", True)
    except Exception as ex:
        logger.exception(f"validate_session: unexpected error: {ex}")
        return {"valid": False, "reason": "exception", "requires_manual_login": True}


def _restore_cookies(driver, session_data: Dict[str, Any]) -> bool:
    """
    Best-effort restore cookies from session_data into the browser driver.
    Returns True if at least one cookie was attempted to be added.
    """
    if not session_data:
        return False
    cookies = session_data.get("cookies", [])
    if not cookies:
        return False
    try:
        # Navigate to a high-level domain to set cookies
        try:
            driver.get("https://claude.ai")
        except Exception:
            # Even if navigation fails, attempt to add cookies; many drivers require a current domain.
            pass

        added = 0
        for c in cookies:
            if not isinstance(c, dict):
                continue
            cookie = {
                "name": c.get("name"),
                "value": c.get("value"),
                "domain": c.get("domain"),
                "path": c.get("path", "/"),
            }
            # expiry handling
            if "expiry" in c and isinstance(c.get("expiry"), (int, float)):
                cookie["expiry"] = int(c.get("expiry"))
            try:
                driver.add_cookie(cookie)
                added += 1
            except Exception:
                # best-effort only
                continue
        logger.debug(f"_restore_cookies: attempted to add {added} cookie(s)")
        return added > 0
    except Exception:
        logger.exception("_restore_cookies failed")
        return False


def try_relogin(driver, max_attempts: int = 1) -> bool:
    """
    Deterministic re-login flow. Strategy:
    1) Attempt to restore saved cookies and validate session (non-interactive).
    2) If non-interactive fails and interactive relogin is allowed via scraper/config.json,
       invoke the interactive manual_login flow (calls into ClaudeUsageScraper.manual_login).
    Limits retries to max_attempts and logs outcomes.

    Returns True on success, False otherwise.
    """
    try:
        cfg_path = Path("scraper/config.json")
        allow_interactive = False
        if cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                allow_interactive = bool(cfg.get("allow_interactive_relogin", False))
            except Exception:
                logger.debug("try_relogin: failed to read config.json; proceeding with defaults")

        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            logger.info(f"try_relogin: attempt {attempts}/{max_attempts} - trying non-interactive restore")
            sess = load_session()
            restored = False
            try:
                if sess:
                    restored = _restore_cookies(driver, sess)
            except Exception:
                logger.exception("try_relogin: cookie restore failed")

            if restored:
                # Determine if session was associated with a persistent profile to use lenient validation
                use_profile = bool(sess.get("profile_path")) if sess else bool(getattr(driver, "user_data_dir", None))
                result = validate_session(driver, timeout=60, use_profile=use_profile)
                if result and result.get("valid"):
                    logger.info("try_relogin: non-interactive cookie restore succeeded")
                    # Persist updated metadata timestamp
                    save_session(driver)
                    return True
                else:
                    logger.info(f"try_relogin: cookies restored but session invalid; reason={result.get('reason') if result else 'unknown'} requires_manual={result.get('requires_manual_login') if result else 'unknown'}")

            # If non-interactive failed, consider interactive flow if allowed
            if allow_interactive:
                logger.info("try_relogin: attempting interactive manual_login as configured")
                try:
                    # local import to avoid circular top-level import
                    from .claude_scraper import ClaudeUsageScraper
                    # delegate interactive login; manual_login will save session on success
                    try:
                        ClaudeUsageScraper.manual_login(driver=driver)
                    except Exception as ex:
                        logger.exception(f"try_relogin: interactive manual_login failed: {ex}")
                        # continue to next attempt
                    # Validate after interactive attempt
                    use_profile = bool(getattr(driver, "user_data_dir", None))
                    result = validate_session(driver, timeout=60, use_profile=use_profile)
                    if result and result.get("valid"):
                        logger.info("try_relogin: interactive manual_login succeeded")
                        save_session(driver)
                        return True
                    else:
                        logger.warning(f"try_relogin: interactive manual_login did not produce a valid session; reason={result.get('reason') if result else 'unknown'} requires_manual={result.get('requires_manual_login') if result else 'unknown'}")
                except Exception:
                    logger.exception("try_relogin: failed to import ClaudeUsageScraper for interactive login")
            else:
                logger.debug("try_relogin: interactive relogin not allowed by config; skipping")

            # small backoff between attempts
            time.sleep(1 + attempts)
        logger.warning("try_relogin: exhausted attempts; re-login failed")
        return False
    except Exception:
        logger.exception("try_relogin: unexpected error")
        return False
