#!/usr/bin/env python3
"""
Playwright-based scraper for Claude usage page.

Behavior:
- Uses a Playwright persistent context stored in `browser-data/`.
- If no authenticated session exists, opens a browser window and waits for manual login.
- Polls the usage page every 5 minutes (configurable) and writes `data/usage-data.json`
  atomically with the required schema and appended historical point.
- Attempts best-effort extraction by scanning page text; selectors may need tuning.
- Integrates projections using `src.overlay.projection_algorithms.integrate_projections_into_data`
  if available.

Requirements:
- playwright
- Python 3.8+
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is on path for local imports
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

try:
    from src.overlay.projection_algorithms import integrate_projections_into_data  # type: ignore
except Exception:
    integrate_projections_into_data = None  # optional

# Config
BROWSER_DATA_DIR = ROOT / "browser-data"
USAGE_URL = "https://claude.ai/usage"
DATA_FILE = ROOT / "data" / "usage-data.json"
POLL_INTERVAL_SECONDS = 5 * 60  # 5 minutes


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """
    Atomically write JSON to file using temporary file + replace.
    """
    tmp = path.with_suffix(".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    # Use os.replace for atomic rename on Windows
    os.replace(str(tmp), str(path))


def parse_number(s: str) -> Optional[float]:
    """Parse a number from string, return float or None."""
    try:
        s_clean = s.replace(",", "").strip()
        return float(s_clean)
    except Exception:
        return None


def extract_metrics_from_text(text: str) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Heuristically extract metrics from page text.

    Looks for patterns like:
      - "22 / 50" or "387 / 1000"
      - "<number>%"
    Prefers explicit "4-hour", "week", "opus" nearby, otherwise picks the first three matches.

    Added diagnostic output to help debug mis-matches between historical data and
    newly-extracted metrics (writes a debug JSON to data/ for post-mortem).
    """
    # Normalize whitespace
    txt = re.sub(r"\s+", " ", text)

    # Patterns for "used / limit"
    slash_pattern = re.compile(r"(\d{1,6})\s*/\s*(\d{1,6})")
    percent_pattern = re.compile(r"(\d{1,3}(?:\.\d)?)\s*%")

    candidates = []
    for m in slash_pattern.finditer(txt):
        used = parse_number(m.group(1))
        limit = parse_number(m.group(2))
        if used is not None and limit is not None and limit > 0:
            pct = round((used / limit) * 100, 1)
            start = max(0, m.start() - 80)
            window = txt[start : m.end() + 80].lower()
            candidates.append({"used": used, "limit": limit, "percentage": pct, "context": window, "match_span": [m.start(), m.end()]})

    # Try to map by keywords
    four = next((c for c in candidates if "4-hour" in c["context"] or "4 hour" in c["context"] or "4‑hour" in c["context"]), None)
    week = next((c for c in candidates if "week" in c["context"] and "opus" not in c["context"]), None)
    opus = next((c for c in candidates if "opus" in c["context"]), None)

    # Fallback: first three distinct candidates
    if not four or not week or not opus:
        distinct = []
        seen = set()
        for c in candidates:
            key = (int(c["used"]), int(c["limit"]))
            if key in seen:
                continue
            seen.add(key)
            distinct.append(c)
            if len(distinct) >= 3:
                break
        # assign if mapping missing
        if not four and len(distinct) >= 1:
            four = distinct[0]
        if not week and len(distinct) >= 2:
            week = distinct[1]
        if not opus and len(distinct) >= 3:
            opus = distinct[2]

    if not four or not week or not opus:
        # Best-effort: try percent matches (less reliable)
        perc_matches = [m for m in percent_pattern.finditer(txt)]
        if len(perc_matches) >= 3:
            # Not enough context to map used/limit though
            return None
        return None

    # Build metrics in expected schema: fourHourCap, weekCap, opusWeekCap
    def normalize(c: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "used": int(c["used"]),
            "limit": int(c["limit"]),
            "percentage": float(round(c["percentage"], 1)),
        }

    metrics = {
        "fourHourCap": normalize(four),
        "weekCap": normalize(week),
        "opusWeekCap": normalize(opus),
    }

    # Diagnostic dump to help root-cause extraction mismatches.
    try:
        debug = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "candidates": candidates,
            "mapped": {
                "four": {"used": four["used"], "limit": four["limit"], "percentage": four["percentage"], "context": four["context"]},
                "week": {"used": week["used"], "limit": week["limit"], "percentage": week["percentage"], "context": week["context"]},
                "opus": {"used": opus["used"], "limit": opus["limit"], "percentage": opus["percentage"], "context": opus["context"]},
            },
            # include a short snapshot of the surrounding text window for the first candidate (if any)
            "sample_text_window": txt[:1000]
        }
        dbg_path = ROOT / "data" / f"extraction_debug_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        dbg_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dbg_path, "w", encoding="utf-8") as df:
            json.dump(debug, df, indent=2)
        print(f"Extraction debug written to {dbg_path}")
    except Exception:
        # Non-fatal: don't interrupt scraping if diagnostics fail
        pass

    return metrics


async def ensure_authenticated(page) -> None:
    """
    If the usage page shows a login prompt, let the user login manually in the persistent context.
    Checks for a likely login indicator and waits until the usage text appears.
    """
    # Quick check: if page contains "Log in" or "Sign in" near main content, wait for manual login
    content = await page.content()
    if re.search(r"\b(Log[\s-]?in|Sign[\s-]?in|Continue with Google)\b", content, re.IGNORECASE):
        print("No active session detected. Please log in in the opened browser window. Waiting...")
        # Wait until the usage page contains text that looks like numbers " / " or "%", or timeout after 5 minutes
        for _ in range(60):
            await asyncio.sleep(5)
            content = await page.content()
            if "/" in content and re.search(r"\d\s*/\s*\d", content):
                print("Login detected, proceeding.")
                return
        print("Timeout waiting for manual login; continuing best-effort extraction.")


async def scrape_once(playwright, headless: bool = False, confirm_login: bool = False) -> Optional[Dict[str, Any]]:
    """
    Open persistent context, navigate to usage page, extract metrics, and return data dict ready to write.

    If confirm_login is True, the function will pause after opening the browser and
    wait for an explicit terminal confirmation (press Enter) before proceeding with
    authentication detection and extraction. This helps avoid false-positive login
    detection during interactive runs.
    """
    browser_type = playwright.chromium
    # Use existing Chrome profile (browser-data/Default) and system Chrome to preserve login sessions.
    # Playwright will use the 'chrome' channel to launch installed Chrome executable.
    user_data_dir = str(BROWSER_DATA_DIR / "Default")
    launch_args = [
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-sandbox",
    ]
    print(f"Launching Chrome with user data dir: {user_data_dir}")
    context = await browser_type.launch_persistent_context(
        user_data_dir,
        headless=headless,
        channel="chrome",
        args=launch_args,
    )
    try:
        page = await context.new_page()
        await page.goto(USAGE_URL, timeout=60_000)
        # If requested, pause and wait for explicit user confirmation (press Enter)
        # This avoids false-positive login detection during interactive troubleshooting.
        if confirm_login:
            print("Please complete login in the opened browser window, then press Enter in this terminal to continue.")
            loop = asyncio.get_event_loop()
            # run input() in executor to avoid blocking the event loop
            await loop.run_in_executor(None, lambda: input())
        await ensure_authenticated(page)

        # Give the page some time to render dynamic content
        await asyncio.sleep(2)
        text = await page.inner_text("body")
        metrics = extract_metrics_from_text(text)
        if metrics is None:
            # fallback: try full HTML
            html = await page.content()
            metrics = extract_metrics_from_text(html)

        if metrics is None:
            print("Failed to reliably extract metrics from page. Page content snapshot saved to debug file.")
            debug_file = ROOT / "data" / f"debug_page_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(await page.content())
            return None

        # Build data structure
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data: Dict[str, Any] = {
            "lastUpdated": now_iso,
            "metrics": metrics,
            "historicalData": [],
        }

        # Append a historical point using raw used numbers
        hd_point = {
            "timestamp": now_iso,
            "fourHourUsed": metrics["fourHourCap"]["used"],
            "weekUsed": metrics["weekCap"]["used"],
            "opusWeekUsed": metrics["opusWeekCap"]["used"],
        }
        # Try to load existing file and append
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                # Keep previous historicalData if present
                historical = existing.get("historicalData", [])
                # Append and trim to 2016 points max
                historical.append(hd_point)
                historical = historical[-2016:]
                data["historicalData"] = historical
            except Exception:
                # If reading fails, start fresh
                data["historicalData"] = [hd_point]
        else:
            data["historicalData"] = [hd_point]

        # Optionally integrate projections if available
        if integrate_projections_into_data:
            try:
                data = integrate_projections_into_data(data)
            except Exception as e:
                print(f"Projection integration failed: {e}")

        return data

    finally:
        await context.close()


async def run_loop(headless: bool = False, run_once: bool = False, confirm_login: bool = False) -> None:
    """
    Main loop: start Playwright, scrape periodically, and write atomic JSON.

    confirm_login: if True, each scrape will pause after opening the browser and wait
    for explicit terminal confirmation before proceeding.
    """
    try:
        from playwright.async_api import async_playwright  # type: ignore
    except Exception as e:
        print("Playwright is not installed. Install with: pip install playwright")
        print("Then run: playwright install chromium")
        raise e

    async with async_playwright() as p:
        # Ensure browser-data dir exists
        BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)

        while True:
            print(f"[{datetime.now(timezone.utc).isoformat()}] Starting scrape...")
            try:
                data = await scrape_once(p, headless=headless, confirm_login=confirm_login)
                if data:
                    atomic_write_json(DATA_FILE, data)
                    print(f"[{datetime.now(timezone.utc).isoformat()}] Wrote data to {DATA_FILE}")
                else:
                    print("Scrape returned no data.")
            except Exception as e:
                print(f"Error during scrape: {e}")

            if run_once:
                break
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Claude usage scraper (Playwright persistent).")
    parser.add_argument("--headless", action="store_true", help="Run browser headless (not recommended for initial login).")
    parser.add_argument("--once", action="store_true", help="Run a single scrape and exit.")
    parser.add_argument("--confirm-login", action="store_true", help="Pause after opening the browser and wait for explicit terminal confirmation before proceeding (press Enter).")
    args = parser.parse_args()

    try:
        asyncio.run(run_loop(headless=args.headless, run_once=args.once, confirm_login=args.confirm_login))
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting.")


if __name__ == "__main__":
    main()