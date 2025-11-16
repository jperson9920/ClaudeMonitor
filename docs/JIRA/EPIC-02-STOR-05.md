# EPIC-02-STOR-05

Title: Cloudflare challenge handling and anti-detection tuning in scraper

Epic: [`EPIC-02`](docs/JIRA/EPIC-LIST.md:24)

Status: TODO

## Description
As a developer, I need the scraper to include explicit Cloudflare challenge handling and anti-detection configuration so the headed Chrome runs reliably (85–95% success) and recovers gracefully when challenged.

This story enhances `scraper/claude_scraper.py` to:
- Configure undetected-chromedriver options and flags (already required by create_driver)
- Detect Cloudflare interstitial/challenge pages and wait/retry human-like interactions
- Provide a fallback path (plain-text extraction of visible text) when automated bypass fails

User perspective: "As a user I want the scraper to succeed most of the time and surface clear diagnostics when Cloudflare prevents extraction."

## Acceptance Criteria
- [ ] `create_driver()` includes documented anti-detection options and comments (headless=False, use_subprocess=True, realistic UA/window-size, --disable-blink-features=AutomationControlled). (Reference Research.md lines 281-296)
- [ ] Scraper detects Cloudflare/challenge pages by matching page text patterns (e.g., "Checking your browser", "Just a moment", or presence of known Cloudflare element selectors) and logs `diagnostics['cloudflare_detected']=true`.
- [ ] On challenge detection, scraper will wait up to configurable timeout (default 60s) for challenge resolution, polling every 2s for page change. If unresolved, it attempts exponential-backoff retries (hook into retry_handler.py) and emits error code `navigation_failed` or `extraction_failed` as appropriate.
- [ ] Fallback extraction path returns partial data using plain-text search across page body and sets top-level `status='partial'` with `found_components` count.
- [ ] Detailed logs written to `scraper/scraper.log` including timestamps, detection method, retries, and final outcome.

## Dependencies
- EPIC-02-STOR-01 (driver lifecycle)
- EPIC-02-STOR-02 (extraction helpers)
- EPIC-08 (retry handler integration) — coordinate design but implement local retries here

## Tasks (1-3 hours each)
- [ ] Add Cloudflare detection helper `is_challenge_page(driver) -> bool` in `scraper/claude_scraper.py` (1.0h)
  - Match text patterns: "Checking your browser", "Just a moment", "Please enable JavaScript"
- [ ] Implement wait-for-challenge-resolution logic with configurable timeout and polling interval (0.75h)
  - Use `time.sleep(2)` loops and `driver.current_url` / DOM checks
- [ ] Integrate with `retry_handler.py` or implement local exponential-backoff for navigation attempts (1.0h)
  - Configurable parameters: initial_delay=1s, multiplier=2.0, max_attempts=4
- [ ] Implement plain-text fallback extraction that scans `driver.page_source` for tokens and extracts percentages/reset text (0.75h)
- [ ] Add diagnostic logging and ensure fallback sets `status='partial'` and includes `diagnostics` fields (0.5h)

## Estimate
Total: 4 hours

## Research References
- Research.md: rationale for headed mode and anti-detection (lines 85-90, 81-84) [`docs/Research.md:81-90`]
- Research.md: undetected-chromedriver usage (lines 109-116, 287-296) [`docs/Research.md:109-116`, `docs/Research.md:287-296`]
- EPIC-LIST.md: DOM scraping clarification and partial status behavior (`docs/JIRA/EPIC-LIST.md:127-135`)

## Risks & Open Questions
- Risk: Cloudflare defenses may change rapidly and require manual mitigation steps; include guidance in EPIC-09 tests and troubleshooting doc.
- Open question: Should the scraper attempt to solve CAPTCHAs automatically (NO for v1.0) or always require manual resolution during `--login` flow? Decision: do not attempt CAPTCHA solving; require manual resolution.