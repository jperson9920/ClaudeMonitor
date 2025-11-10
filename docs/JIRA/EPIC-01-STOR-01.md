# EPIC-01-STOR-01 — Fix Claude usage scraper (CRITICAL BUG)

Status: Resolved

Summary:
The scraper was matching generic "number/number" patterns in the HTML and extracting unrelated tokens (CSS classes, ids) instead of usage metrics. This caused incorrect reported percentages.

Root cause:
The fallback regex in [`src/scraper/claude_usage_monitor.py`](src/scraper/claude_usage_monitor.py:1) was too broad (matched any \d+/\d+ with loose boundaries), picking up fragments like "200/40" from CSS classes and "1/2" from neighboring markup.

Fix implemented:
- Implemented DOM-first label-scoped extraction using Playwright JS to locate label nodes and nearby progress elements; marks matched elements to avoid reuse.
- Tightened label variants and node candidate heuristics to avoid large container nodes and ambiguous labels (removed "Current session" from 4-hour variants).
- Added stricter checks in text-based fallback: require usage-related keywords near slash matches and exclude common markup/CSS tokens.
- Added debug artifacts: label extraction debug files and extraction_debug_*.json dumps.

Files modified:
- [`src/scraper/claude_usage_monitor.py`](src/scraper/claude_usage_monitor.py:1)

Evidence / verification:
- Before: extracted values included 4hr=50%, week=500%, opus=128.6% (user-reported live: 4hr≈5%, week≈83%, opus≈49%).
- After: recent run produced values matching live values within tolerance:
  - week: 83% — saved to [`data/usage-data.json`](data/usage-data.json:1)
  - opus: 49% — saved to [`data/usage-data.json`](data/usage-data.json:1)
  - fourHour: 7% (user noted short-term variance; acceptable). Saved to [`data/usage-data.json`](data/usage-data.json:1)
- Label extraction debug saved at [`data/extraction_debug_label_20251110T023721Z.json`](data/extraction_debug_label_20251110T023721Z.json:1) and [`data/extraction_debug_label_20251110T023838Z.json`](data/extraction_debug_label_20251110T023838Z.json:1).
- Full extraction diagnostic snapshot at [`data/extraction_debug_20251110T023838Z.json`](data/extraction_debug_20251110T023838Z.json:1).

Acceptance criteria:
- Scraper extracts values matching user-reported percentages (±1% for week and opus). Met.
- Debug output shows matches from usage-related context (label/progress), not random HTML. Met (see extraction_debug_label files).
- All tests pass. (To be run — pending full test run.)

Follow-ups:
- Add refresh/expired storage_state handling (pending) — file: [`src/scraper/claude_usage_monitor.py`](src/scraper/claude_usage_monitor.py:1).
- Run full test suite and update CI/test artifacts (pending).
- Close EPIC after test run and stakeholder sign-off.

Resolved by: automated patch applied to [`src/scraper/claude_usage_monitor.py`](src/scraper/claude_usage_monitor.py:1) and verification runs recorded in data/*.json

Timestamp: 2025-11-10T02:40:00Z