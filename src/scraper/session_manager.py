from pathlib import Path
import json
import time
from typing import Optional, Dict, Any

SESSION_FILE_DEFAULT = Path("./scraper/chrome-profile/session.json")


def _ensure_profile_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_session(driver, session_file: str = str(SESSION_FILE_DEFAULT)) -> None:
    """
    Save driver cookies and minimal metadata to session_file atomically.
    Best-effort: does not fail on non-critical errors.
    """
    sf = Path(session_file)
    _ensure_profile_dir(sf)

    session: Dict[str, Any] = {
        "timestamp": int(time.time()),
        "cookies": [],
        "user_agent": None,
        "profile_path": None,
    }

    try:
        session["cookies"] = driver.get_cookies() or []
    except Exception:
        # best-effort capture
        pass

    try:
        ua = driver.execute_script("return navigator.userAgent")
        session["user_agent"] = ua
    except Exception:
        pass

    # Try to capture profile path if driver exposes it
    try:
        profile_path = getattr(driver, "user_data_dir", None)
        if profile_path:
            session["profile_path"] = str(profile_path)
    except Exception:
        pass

    tmp = sf.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(session, fh, indent=2, ensure_ascii=False)
    tmp.replace(sf)


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