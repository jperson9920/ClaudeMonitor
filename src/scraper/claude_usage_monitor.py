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
USAGE_URL = "https://claude.ai/settings/usage"
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

    Strategy:
    - Prefer locating "used/limit" or "<number>%" that appear near explicit
      keywords for each metric (4-hour, week, opus).
    - Use narrow keyword-scoped regexes first to avoid matching arbitrary
      "x/y" fragments from classnames, ids or JSON keys.
    - Fall back to a safer global slash pattern that enforces non-alphanumeric
      boundaries to avoid matching parts of identifiers like "snb9x9/7m6".
    - Emit diagnostics showing both the targeted matches (if found) and any
      fallback candidates for post-mortem analysis.
    """
    # Normalize whitespace to make context-snippets readable
    txt = re.sub(r"\s+", " ", text)

    def build_ctx(m):
        start = max(0, m.start() - 80)
        return txt[start : m.end() + 80].lower()

    # Try targeted keyword-scoped extraction first
    found: Dict[str, Dict[str, Any]] = {}

    # helper to try slash and percent forms for a keyword set
    def try_keyword_patterns(keyword_regex: str, name: str) -> None:
        # Try several proximity patterns (keyword before value, keyword after value)
        # 1) "keyword ... used/limit"
        pat_slash_after = re.compile(rf"{keyword_regex}[^\d]{{0,120}}?(\d{{1,6}})\s*/\s*(\d{{1,6}})", re.IGNORECASE)
        m = pat_slash_after.search(txt)

        # 2) "used/limit ... keyword" (value appears before the keyword)
        if not m:
            pat_slash_before = re.compile(rf"(?<![A-Za-z0-9])(\d{{1,6}})\s*/\s*(\d{{1,6}})[^\d]{{0,120}}?{keyword_regex}", re.IGNORECASE)
            m = pat_slash_before.search(txt)

        if m:
            used = parse_number(m.group(1))
            limit = parse_number(m.group(2))
            if used is not None and limit and limit > 0:
                pct = round((used / limit) * 100, 1)
                found[name] = {"used": int(used), "limit": int(limit), "percentage": pct, "context": build_ctx(m), "match_span": [m.start(), m.end()]}
                return

        # 3) "keyword ... XX%" (percent after keyword)
        pat_pct_after = re.compile(rf"{keyword_regex}[^\d]{{0,120}}?(\d{{1,3}}(?:\.\d)?)\s*%", re.IGNORECASE)
        m2 = pat_pct_after.search(txt)

        # 4) "XX% ... keyword" (percent before keyword)
        if not m2:
            pat_pct_before = re.compile(rf"(?<![A-Za-z0-9])(\d{{1,3}}(?:\.\d)?)\s*%[^\d]{{0,120}}?{keyword_regex}", re.IGNORECASE)
            m2 = pat_pct_before.search(txt)

        if m2:
            val = parse_number(m2.group(1))
            if val is not None:
                # represent percent as used/limit with limit=100 so schema remains consistent
                found[name] = {"used": int(round(val)), "limit": 100, "percentage": float(round(val, 1)), "context": build_ctx(m2), "match_span": [m2.start(), m2.end()]}

    # candidate keyword variants
    try_keyword_patterns(r"(?:4[-\s]?hour|last 4 hours|4h|4‑hour)", "four")
    try_keyword_patterns(r"(?:week|weekly|past 7 days|7[-\s]?day|week to date)", "week")
    try_keyword_patterns(r"(?:opus)", "opus")

    # If all three metrics were found by keyword-scoped extraction, use them.
    if all(k in found for k in ("four", "week", "opus")):
        def normalize(c: Dict[str, Any]) -> Dict[str, Any]:
            return {"used": int(c["used"]), "limit": int(c["limit"]), "percentage": float(round(c["percentage"], 1))}

        metrics = {
            "fourHourCap": normalize(found["four"]),
            "weekCap": normalize(found["week"]),
            "opusWeekCap": normalize(found["opus"]),
        }

        # Diagnostic: write both the found items and an empty candidate list (no global scan needed)
        try:
            debug = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "candidates": [],
                "mapped": {
                    "four": found["four"],
                    "week": found["week"],
                    "opus": found["opus"],
                },
                "sample_text_window": txt[:1000],
            }
            dbg_path = ROOT / "data" / f"extraction_debug_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
            dbg_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dbg_path, "w", encoding="utf-8") as df:
                json.dump(debug, df, indent=2)
            print(f"Extraction debug written to {dbg_path}")
        except Exception:
            pass

        return metrics

    # Fallback: perform a global scan but with safer boundaries to avoid matching
    # parts of identifiers or CSS classes. Require non-alphanumeric boundaries.
    slash_pattern = re.compile(r"(?<![A-Za-z0-9])(\d{1,6})\s*/\s*(\d{1,6})(?![A-Za-z0-9])")
    percent_pattern = re.compile(r"(?<![A-Za-z0-9])(\d{1,3}(?:\.\d)?)\s*%(?![A-Za-z0-9])")
 
    candidates: list = []
    # Heuristic filters: only accept slash matches that appear in visible/usage-related contexts.
    usage_keywords = (
        "used",
        "% used",
        "current session",
        "all models",
        "opus",
        "week",
        "weekly",
        "last 4",
        "4h",
        "4-hour",
        "resets",
        "resets in",
    )
    exclusion_tokens = ("class=", "bg-", "data-", "snb", "<svg", "http", "href=", "nonce=")
 
    for m in slash_pattern.finditer(txt):
        used = parse_number(m.group(1))
        limit = parse_number(m.group(2))
        if used is not None and limit is not None and limit > 0:
            pct = round((used / limit) * 100, 1)
            start = max(0, m.start() - 80)
            window = txt[start : m.end() + 80].lower()
            # Skip matches that are clearly part of markup, CSS classes, identifiers, or JSON keys
            if any(tok in window for tok in exclusion_tokens):
                continue
            # Require at least one usage-related keyword near the match to reduce false positives
            if not any(k in window for k in usage_keywords):
                continue
            candidates.append({"used": used, "limit": limit, "percentage": pct, "context": window, "match_span": [m.start(), m.end()]})

    # Try to map by keywords inside candidate contexts
    four = next((c for c in candidates if "4-hour" in c["context"] or "4 hour" in c["context"] or "4h" in c["context"]), None)
    week = next((c for c in candidates if "week" in c["context"] and "opus" not in c["context"]), None)
    opus = next((c for c in candidates if "opus" in c["context"]), None)

    # Fallback: first three distinct candidates (as before), but with reduced chance of noise
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
        if not four and len(distinct) >= 1:
            four = distinct[0]
        if not week and len(distinct) >= 2:
            week = distinct[1]
        if not opus and len(distinct) >= 3:
            opus = distinct[2]

    # As a last resort, attempt to use percent matches (less reliable) but only if we have
    # good keyword proximity.
    if not four or not week or not opus:
        # try percent matches near keywords if present
        def try_pct_keyword(keyword_regex: str):
            pat = re.compile(rf"{keyword_regex}[^\d]{{0,120}}?(\d{{1,3}}(?:\.\d)?)\s*%", re.IGNORECASE)
            m = pat.search(txt)
            if m:
                val = parse_number(m.group(1))
                if val is not None:
                    return {"used": int(round(val)), "limit": 100, "percentage": float(round(val, 1)), "context": build_ctx(m), "match_span": [m.start(), m.end()]}
            return None

        if not four:
            four = try_pct_keyword(r"(?:4[-\s]?hour|last 4 hours|4h|4‑hour)")
        if not week:
            week = try_pct_keyword(r"(?:week|weekly|past 7 days|7[-\s]?day|week to date)")
        if not opus:
            opus = try_pct_keyword(r"(?:opus)")

    if not four or not week or not opus:
        # Couldn't find reliable mapping
        # Write diagnostics and return None
        try:
            debug = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "candidates": candidates,
                "mapped": {
                    "four": found.get("four") or (four if four else None),
                    "week": found.get("week") or (week if week else None),
                    "opus": found.get("opus") or (opus if opus else None),
                },
                "sample_text_window": txt[:1000],
            }
            dbg_path = ROOT / "data" / f"extraction_debug_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
            dbg_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dbg_path, "w", encoding="utf-8") as df:
                json.dump(debug, df, indent=2)
            print(f"Extraction debug written to {dbg_path}")
        except Exception:
            pass

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

    # Final diagnostic dump
    try:
        debug = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "candidates": candidates,
            "mapped": {
                "four": {"used": metrics["fourHourCap"]["used"], "limit": metrics["fourHourCap"]["limit"], "percentage": metrics["fourHourCap"]["percentage"], "context": (four["context"] if isinstance(four, dict) else "")},
                "week": {"used": metrics["weekCap"]["used"], "limit": metrics["weekCap"]["limit"], "percentage": metrics["weekCap"]["percentage"], "context": (week["context"] if isinstance(week, dict) else "")},
                "opus": {"used": metrics["opusWeekCap"]["used"], "limit": metrics["opusWeekCap"]["limit"], "percentage": metrics["opusWeekCap"]["percentage"], "context": (opus["context"] if isinstance(opus, dict) else "")},
            },
            "sample_text_window": txt[:1000],
        }
        dbg_path = ROOT / "data" / f"extraction_debug_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        dbg_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dbg_path, "w", encoding="utf-8") as df:
            json.dump(debug, df, indent=2)
        print(f"Extraction debug written to {dbg_path}")
    except Exception:
        pass

    return metrics


async def ensure_authenticated(page) -> None:
    """
    Improved authentication detection:

    - Prefer checking for session/auth cookies in the browser context (common stable indicator).
    - Fallback to detecting rendered usage numbers on the page.
    - Require two consecutive polls that show numeric usage to avoid transient pages causing false positives.
    - Timeout after ~5 minutes and continue best-effort.
    """
    # Quick cookie-based check for likely session indicators
    try:
        cookies = await page.context.cookies()
        for c in cookies:
            name = c.get("name", "")
            val = c.get("value", "")
            if val and re.search(r"(session|auth|token|jwt)", name, re.IGNORECASE):
                print("Active session cookie detected. Proceeding.")
                return
    except Exception:
        # Non-fatal: if cookies can't be read, continue to content-based checks
        pass

    content = await page.content()

    # If page clearly shows login prompts, instruct the user to login.
    if re.search(r"\b(Log[\s-]?in|Sign[\s-]?in|Continue with Google)\b", content, re.IGNORECASE):
        print("No active session detected. Please log in in the opened browser window. Waiting...")
    else:
        # If no obvious login prompt and usage numbers are present, assume logged in.
        if re.search(r"\d\s*/\s*\d", content):
            print("Usage numbers present; assuming logged in.")
            return
        # Otherwise fall through to polling loop.

    # Poll for stable post-login indicators:
    stable_count = 0
    for _ in range(60):
        await asyncio.sleep(5)
        try:
            # Re-check cookies first (fast, reliable)
            cookies = await page.context.cookies()
            for c in cookies:
                name = c.get("name", "")
                val = c.get("value", "")
                if val and re.search(r"(session|auth|token|jwt)", name, re.IGNORECASE):
                    print("Active session cookie detected. Proceeding.")
                    return
        except Exception:
            pass

        content = await page.content()
        if re.search(r"\d\s*/\s*\d", content):
            stable_count += 1
            # require two consecutive positive polls to avoid transient pages
            if stable_count >= 2:
                print("Login detected, proceeding.")
                return
        else:
            stable_count = 0

    print("Timeout waiting for manual login; continuing best-effort extraction.")


async def scrape_once(playwright, headless: bool = False, confirm_login: bool = False) -> Optional[Dict[str, Any]]:
    """
    Open persistent context, navigate to usage page, extract metrics, and return data dict ready to write.

    Extraction strategy:
    - Try DOM selector extraction (prioritized selectors from docs/JIRA) for stability.
    - If DOM extraction fails, fall back to existing text-based heuristics.
    """
    browser_type = playwright.chromium
    # Use Playwright-managed browser + storage_state to persist auth without relying on system Chrome profile.
    STORAGE_STATE_FILE = BROWSER_DATA_DIR / "storage_state.json"
    launch_args = [
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-sandbox",
    ]
    print(f"Launching Playwright browser (bundled chromium). storage_state={STORAGE_STATE_FILE}")
    browser = await browser_type.launch(headless=headless, args=launch_args)
    if STORAGE_STATE_FILE.exists():
        context = await browser.new_context(storage_state=str(STORAGE_STATE_FILE))
    else:
        context = await browser.new_context()
    # browser/context cleanup handled in finally
    try:
        page = await context.new_page()
        await page.goto(USAGE_URL, timeout=60_000)
        # Detect Cloudflare/turnstile challenge pages and handle them proactively.
        async def _is_cf_challenge():
            try:
                content = await page.content()
                if "Just a moment..." in content or "cf-turnstile" in content or "challenge-platform" in content:
                    return True
            except Exception:
                return False
            return False

        if await _is_cf_challenge():
            print("Detected Cloudflare/turnstile challenge on the usage page.")
            # If interactive mode, ask the user to complete the verification manually.
            if confirm_login:
                print("Please complete the Cloudflare verification in the opened browser window, then press Enter in this terminal to continue.")
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: input())
            else:
                # Non-interactive mode: poll for the challenge to clear (best-effort).
                max_wait = 120  # seconds
                poll_interval = 5
                waited = 0
                cleared = False
                while waited < max_wait:
                    await asyncio.sleep(poll_interval)
                    waited += poll_interval
                    if not await _is_cf_challenge():
                        print("Cloudflare challenge cleared; proceeding.")
                        cleared = True
                        break
                    # Occasionally reload to prompt any server-side resolution
                    if waited % 30 == 0:
                        try:
                            await page.reload()
                        except Exception:
                            pass
                if not cleared:
                    print("Cloudflare challenge still present after wait window; saving debug snapshot and continuing best-effort.")
                    debug_file = ROOT / "data" / f"debug_page_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.html"
                    debug_file.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        with open(debug_file, "w", encoding="utf-8") as f:
                            f.write(await page.content())
                        print(f"Saved challenge snapshot to {debug_file}")
                    except Exception:
                        pass

        # Proceed with normal authentication checks (this may still detect login via cookies or page content)
        await ensure_authenticated(page)
    
        # If the run was an interactive confirm-login, save storage_state so future runs can reuse the session.
        try:
            if confirm_login:
                try:
                    await page.context.storage_state(path=str(STORAGE_STATE_FILE))
                    print(f"Saved storage_state to {STORAGE_STATE_FILE}")
                except Exception as e:
                    print(f"Warning: failed to save storage_state: {e}")
        except Exception:
            pass
    
        # Give the page some time to render dynamic content
        await asyncio.sleep(2)

        async def extract_metrics_from_dom(page) -> Optional[Dict[str, Dict[str, Any]]]:
                """
                DOM-first extraction that targets metric containers.
        
                Steps:
                1) Try an explicit label-based DOM lookup (most robust): find the
                   visible label nodes for "Current session", "All models", and "Opus only"
                   and look for percent strings nearby (same container, sibling, or parent).
                2) If label-based fails, fall back to existing container-based heuristics
                   (data-testid/.usage-metric and attribute mapping).
                3) Return normalized metrics (limit=100 for percent-based extraction).
                """
                percent_re = re.compile(r"(\d{1,3}(?:\.\d)?)\s*%")
        
                # 1) Fast, robust label-scoped JS search: directly query the DOM for labels
                try:
                    js = r"""
                    (() => {
                      const out = {};
                      const debug = {};
                      // Support multiple label variants and fallback to progress-like elements.
                      const labelVariants = {
                        // Removed ambiguous "current session" from the 4-hour variants because
                        // the UI shows a "Current session" bar that is not the same as the
                        // 4-hour usage metric. Prefer explicit "4h/4-hour/last 4 hours" forms.
                        four: ['4-hour', '4 hour', 'last 4 hours', '4h', '4 hr'],
                        week: ['all models', 'week', 'weekly', 'past 7 days', '7 day', '1 week', 'week to date'],
                        opus: ['opus', 'opus only', 'opus model']
                      };
        
                      const pctMatch = s => {
                        if (!s) return null;
                        const m = s.match(/(\d{1,3}(?:\.\d)?)\s*%/);
                        return m ? m[1] : null;
                      };
        
                      const styleWidthMatch = el => {
                        try {
                          const s = el.getAttribute && el.getAttribute('style');
                          if (s) {
                            const mm = s.match(/width\s*:\s*(\d{1,3}(?:\.\d)?)%/);
                            if (mm) return mm[1];
                          }
                        } catch {}
                        return null;
                      };
        
                      const findProgressInNode = (node) => {
                        if (!node) return null;
                        // prefer explicit progress-like elements inside node
                        const sel = '[role=\"progressbar\"], [aria-valuenow], .progress, .progress-bar, .usage-percent, .percentage';
                        const els = Array.from(node.querySelectorAll(sel));
                        for (const e of els) {
                          try {
                            if (e.getAttribute && e.getAttribute('data-claude-monitor-matched') === '1') continue;
                            const v = e.getAttribute && e.getAttribute('aria-valuenow') || styleWidthMatch(e) || pctMatch(e.innerText || '');
                            if (v) return {el: e, val: v};
                          } catch {}
                        }
                        // check children text/style
                        for (const c of node.querySelectorAll('*')) {
                          try {
                            if (c.getAttribute && c.getAttribute('data-claude-monitor-matched') === '1') continue;
                            const v = styleWidthMatch(c) || pctMatch(c.innerText || '');
                            if (v) return {el: c, val: v};
                          } catch {}
                        }
                        return null;
                      };
        
                      const findNearby = (el) => {
                        // 1) Check the element itself for a progress-like child/value
                        const direct = findProgressInNode(el);
                        if (direct) return direct;
                        // 2) Check siblings
                        let s = el.nextElementSibling;
                        let steps = 0;
                        while (s && steps < 8) {
                          const r = findProgressInNode(s);
                          if (r) return r;
                          s = s.nextElementSibling; steps++;
                        }
                        // check previous siblings
                        s = el.previousElementSibling;
                        steps = 0;
                        while (s && steps < 8) {
                          const r = findProgressInNode(s);
                          if (r) return r;
                          s = s.previousElementSibling; steps++;
                        }
                        // 3) Walk up parents and check their children
                        let p = el.parentElement;
                        steps = 0;
                        while (p && steps < 6) {
                          const r = findProgressInNode(p);
                          if (r) return r;
                          p = p.parentElement; steps++;
                        }
                        return null;
                      };
        
                      // Try label-based lookup with variants; mark matched progress elements to avoid reuse.
                      for (const [key, variants] of Object.entries(labelVariants)) {
                        try {
                          // Limit node candidates to likely label elements and avoid huge container nodes.
                          const nodes = Array.from(document.querySelectorAll('p,div,span,label,li,h3,h4'));
                          for (const n of nodes) {
                            try {
                              const txtRaw = (n.innerText || '').trim();
                              if (!txtRaw) continue;
                              const txt = txtRaw.toLowerCase();
                              // Skip very large text nodes or those with many lines (likely a container)
                              if (txt.length > 120) continue;
                              const lineCount = (txtRaw.match(/\n/g) || []).length;
                              if (lineCount > 2) continue;
                              const wordCount = txt.split(/\s+/).length;
                              if (wordCount > 12) continue;
                              // Require the variant to appear as a (rough) standalone token to reduce false matches
                              const matchesVariant = variants.some(v => {
                                const pattern = v.replace(/[-\s]+/g, '\\s+'); // flexible spacing/hyphen
                                try {
                                  return new RegExp('\\b' + pattern + '\\b', 'i').test(txtRaw);
                                } catch (e) {
                                  return txt.includes(v);
                                }
                              });
                              if (!matchesVariant) continue;
                              const found = findNearby(n);
                              if (found && found.val) {
                                // mark matched element so it's not reused for another metric
                                try { found.el.setAttribute && found.el.setAttribute('data-claude-monitor-matched', '1'); } catch {}
                                out[key] = found.val;
                                debug[key] = {labelHTML: n.outerHTML, progressHTML: (found.el && found.el.outerHTML) || null};
                                break; // stop searching other nodes for this key
                              } else {
                                // fallback: if label text itself contains a percent
                                const selfPct = pctMatch(n.innerText || '');
                                if (selfPct) {
                                  out[key] = selfPct;
                                  debug[key] = {labelHTML: n.outerHTML, progressHTML: null};
                                  break;
                                }
                              }
                            } catch {}
                          }
                        } catch {}
                      }
        
                      // If any metric still missing, scan explicit progress elements and map by nearby label text
                      try {
                        const progressEls = Array.from(document.querySelectorAll('[role=\"progressbar\"], [aria-valuenow], .progress, .progress-bar, .usage-percent, .percentage'));
                        for (const pel of progressEls) {
                          try {
                            if (pel.getAttribute && pel.getAttribute('data-claude-monitor-matched') === '1') continue;
                            const v = pel.getAttribute && pel.getAttribute('aria-valuenow') || styleWidthMatch(pel) || pctMatch(pel.innerText || '');
                            if (!v) continue;
                            // find label by walking up parents
                            let p = pel.parentElement;
                            let labelFound = null;
                            let steps = 0;
                            while (p && steps < 6) {
                              try {
                                const pt = (p.innerText || '').toLowerCase();
                                for (const [key, variants] of Object.entries(labelVariants)) {
                                  if (variants.some(vv => pt.includes(vv)) && !(key in out)) {
                                    labelFound = key;
                                    break;
                                  }
                                }
                                if (labelFound) break;
                              } catch {}
                              p = p.parentElement; steps++;
                            }
                            if (labelFound) {
                              try { pel.setAttribute && pel.setAttribute('data-claude-monitor-matched', '1'); } catch {}
                              out[labelFound] = v;
                              debug[labelFound] = {labelHTML: (p && p.outerHTML) || null, progressHTML: pel.outerHTML};
                            }
                          } catch {}
                        }
                      } catch {}
        
                      // Return whatever we found; include debug under __debug key
                      out.__debug = debug;
                      return out;
                    })()
                    """
                    label_matches = await page.evaluate(js)
                    # Save JS-provided label extraction debug for inspection (if present)
                    try:
                        if isinstance(label_matches, dict) and "__debug" in label_matches:
                            dbg = label_matches.get("__debug")
                            dbg_path = ROOT / "data" / f"extraction_debug_label_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
                            dbg_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(dbg_path, "w", encoding="utf-8") as df:
                                json.dump({"timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00','Z'), "js_debug": dbg, "label_matches": label_matches}, df, indent=2)
                            print(f"Label extraction debug written to {dbg_path}")
                    except Exception:
                        pass
                except Exception:
                    label_matches = {}
        
                found = {}
                try:
                    if isinstance(label_matches, dict):
                        # If JS returned percent strings for all three metrics, accept them.
                        if all(k in label_matches for k in ("four", "week", "opus")):
                            for k, v in label_matches.items():
                                val = parse_number(v)
                                if val is not None:
                                    found[k] = {"used": int(round(val)), "limit": 100, "percentage": float(round(val, 1)), "context": f"label-scoped:{k}:{v}"}
                                    continue
                            if all(k in found for k in ("four", "week", "opus")):
                                def normalize(c: Dict[str, Any]) -> Dict[str, Any]:
                                    return {"used": int(c["used"]), "limit": int(c["limit"]), "percentage": float(round(c["percentage"], 1))}
                                return {
                                    "fourHourCap": normalize(found["four"]),
                                    "weekCap": normalize(found["week"]),
                                    "opusWeekCap": normalize(found["opus"]),
                                }
                except Exception:
                    # If label-based extraction failed for any reason, fall through to container logic
                    pass
        
                # 2) Fallback: existing container-based heuristics (tries attributes, selectors, and label text inside containers)
                try:
                    containers = await page.query_selector_all('[data-testid="usage-metric"], .usage-metric')
                except Exception:
                    containers = []
        
                async def extract_from_container(el):
                    # get identifying attributes and inner text snippets
                    try:
                        attrs = await el.evaluate("el => ({cap: el.getAttribute('data-cap'), period: el.getAttribute('data-period'), model: el.getAttribute('data-model'), testid: el.getAttribute('data-testid')})")
                    except Exception:
                        attrs = {"cap": None, "period": None, "model": None, "testid": None}
                    try:
                        # try known child selectors first
                        child = await el.query_selector('.percentage, .usage-percent, .usage-percent-value')
                        if child:
                            txt = (await child.inner_text()).strip()
                        else:
                            txt = (await el.inner_text()).strip()
                    except Exception:
                        txt = ""
                    return attrs, txt
        
                for el in containers:
                    attrs, txt = await extract_from_container(el)
                    if not txt:
                        continue
                    m = percent_re.search(txt)
                    if not m:
                        continue
                    val = parse_number(m.group(1))
                    if val is None:
                        continue
                    ctx = txt
                    pct_obj = {"used": int(round(val)), "limit": 100, "percentage": float(round(val, 1)), "context": ctx}
        
                    # Mapping heuristics using attributes first
                    cap = (attrs.get("cap") or "") if isinstance(attrs, dict) else ""
                    period = (attrs.get("period") or "") if isinstance(attrs, dict) else ""
                    model = (attrs.get("model") or "") if isinstance(attrs, dict) else ""
                    testid = (attrs.get("testid") or "") if isinstance(attrs, dict) else ""
        
                    low_attrs = " ".join([cap or "", period or "", model or "", testid or ""]).lower()
        
                    if "opus" in low_attrs or "opus" in ctx.lower() or model == "opus":
                        if "opus" not in found:
                            found["opus"] = pct_obj
                            continue
        
                    if "4" in period or "4h" in period or "4-hour" in low_attrs or "4 hour" in low_attrs or "4h" in low_attrs or "4-hour" in ctx.lower():
                        if "four" not in found:
                            found["four"] = pct_obj
                            continue
        
                    if "week" in low_attrs or "1w" in period or "1week" in cap or "week" in ctx.lower() or "7" in period:
                        if "week" not in found:
                            found["week"] = pct_obj
                            continue
        
                    # Label fallback: inspect container text for keywords
                    low = ctx.lower()
                    if "opus" in low and "opus" not in found:
                        found["opus"] = pct_obj
                        continue
                    if ("4-hour" in low or "4 hour" in low or "4h" in low or "last 4" in low) and "four" not in found:
                        found["four"] = pct_obj
                        continue
                    if ("week" in low or "7 day" in low or "1 week" in low or "one week" in low) and "week" not in found:
                        found["week"] = pct_obj
                        continue
        
                # Additional fast-path: try data-testid specific selectors (explicit percent elements)
                if "four" not in found:
                    for s in ['[data-testid="usage-4hour-percent"]', '.usage-metric[data-period="4h"] .percentage', '[data-cap="4hour"] .usage-percent']:
                        try:
                            el = await page.query_selector(s)
                            if el:
                                txt = (await el.inner_text()).strip()
                                m = percent_re.search(txt)
                                if m:
                                    val = parse_number(m.group(1))
                                    if val is not None:
                                        found["four"] = {"used": int(round(val)), "limit": 100, "percentage": float(round(val,1)), "context": txt}
                                        break
                        except Exception:
                            continue
        
                if "week" not in found:
                    for s in ['[data-testid="usage-1week-percent"]', '.usage-metric[data-period="1w"] .percentage', '[data-cap="1week"] .usage-percent', '[data-cap="week"] .usage-percent']:
                        try:
                            el = await page.query_selector(s)
                            if el:
                                txt = (await el.inner_text()).strip()
                                m = percent_re.search(txt)
                                if m:
                                    val = parse_number(m.group(1))
                                    if val is not None:
                                        found["week"] = {"used": int(round(val)), "limit": 100, "percentage": float(round(val,1)), "context": txt}
                                        break
                        except Exception:
                            continue
        
                if "opus" not in found:
                    for s in ['[data-testid="usage-opus-percent"]', '.usage-metric[data-model="opus"] .percentage', '[data-cap="opus"] .usage-percent']:
                        try:
                            el = await page.query_selector(s)
                            if el:
                                txt = (await el.inner_text()).strip()
                                m = percent_re.search(txt)
                                if m:
                                    val = parse_number(m.group(1))
                                    if val is not None:
                                        found["opus"] = {"used": int(round(val)), "limit": 100, "percentage": float(round(val,1)), "context": txt}
                                        break
                        except Exception:
                            continue
        
                if all(k in found for k in ("four", "week", "opus")):
                    def normalize(c: Dict[str, Any]) -> Dict[str, Any]:
                        return {"used": int(c["used"]), "limit": int(c["limit"]), "percentage": float(round(c["percentage"], 1))}
                    return {
                        "fourHourCap": normalize(found["four"]),
                        "weekCap": normalize(found["week"]),
                        "opusWeekCap": normalize(found["opus"]),
                    }
        
                # Not enough DOM confidence — return None to let text heuristics run
                return None

        # Primary: try DOM-based extraction
        metrics = await extract_metrics_from_dom(page)
        if metrics is None:
            # Secondary: try visible body text
            try:
                text = await page.inner_text("body")
            except Exception:
                text = ""
            metrics = extract_metrics_from_text(text)
        if metrics is None:
            # Tertiary: try full HTML snapshot with previous heuristics
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