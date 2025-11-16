# EPIC-02-STOR-02

Title: Implement DOM extraction logic for usage components (exactly 3 components)

Epic: [`EPIC-02`](docs/JIRA/EPIC-LIST.md:24)

Status: TODO

## Description
As a developer, I need a deterministic DOM extraction function that locates the three usage component blocks by searching for static strings (e.g. "Time until reset", "Resets in", "Resets Thu") and reliably extracts:
- the percentage value (e.g., "42% used")
- the reset time text (e.g., "Resets in 59 min" or "Resets Thu 4:00 PM")

This story implements `extract_usage_data(self) -> dict` in `scraper/claude_scraper.py` using the multi-strategy approach (JS execution, CSS/XPath fallback, plain-text fallback) described in Research.md.

User perspective: "As a user I want the widget to show the three usage percentages and reset times so I can monitor my Claude quota."

## Acceptance Criteria
- [ ] `extract_usage_data(self) -> dict` exists with documented signature and returns a dict containing:
  - `components`: list of up to 3 objects { id: str, name: str, usage_percent: int, tokens_used: int|null, tokens_limit: int|null, reset_time: ISO8601|null, raw_reset_text: str, last_updated: ISO8601, status: 'ok'|'partial'|'error' }
  - `found_components`: int
  - `status`: 'ok'|'partial'|'error'
  - `diagnostics`: dict with extraction steps taken
- [ ] Primary locator searches page text nodes for case-insensitive tokens: "Time until reset", "Resets in", "Resets Thu", "Resets" and uses the nearest sibling/ancestor block to extract the percentage and reset text. (See Research.md DOM strategy)
- [ ] Percentage extraction uses regex `/\d{1,3}%\s*used/` and converts to integer 0-100.
- [ ] Reset extraction captures human-readable text and attempts to normalize to ISO 8601 using `dateutil.parser.parse()` (or returns `reset_time=null` and sets `raw_reset_text`).
- [ ] If fewer than 3 components found, `status='partial'` and `found_components` reflects actual count.
- [ ] Unit-testable small helper functions exported/defined in the module:
  - `find_usage_blocks(driver) -> List[WebElement|dict]`
  - `parse_percentage(text: str) -> int|null`
  - `parse_reset_time(text: str) -> (iso_ts: str|null, raw: str)`
  Each helper must have a single-responsibility and docstring.

## Dependencies
- EPIC-02-STOR-01 (driver lifecycle available)
- Research.md lines with DOM extraction examples and JS helper snippet: [`docs/Research.md:463-499`], plus EPIC-LIST DOM scraping clarification [`docs/JIRA/EPIC-LIST.md:127-135`]

## Tasks (1-4 hours each)
- [ ] Implement helper `parse_percentage(text: str) -> int|null` in `scraper/claude_scraper.py` (0.5h)
  - Use regex `r'(\d{1,3})\s*%\\s*used'` and return int or None.
- [ ] Implement helper `parse_reset_time(text: str) -> (iso_ts: str|null, raw: str)` (1.0h)
  - Attempt `from dateutil.parser import parse` to normalize; on failure set `iso_ts=None` and return raw text.
  - Add to `scraper/requirements.txt` if dateutil is used (`python-dateutil`).
- [ ] Implement DOM locator `find_usage_blocks(driver) -> list` using primary JS execution (driver.execute_script) snippet from Research.md to find elements containing the static tokens and return minimal context (0.75h)
  - JS should search textContent with `String.prototype.toLowerCase()` and match tokens; return an array of `{name, percentage_text, reset_text, outer_html_snippet}`.
- [ ] Implement Python-side `extract_usage_data` using the helpers and produce the specified JSON-serializable dict (1.5h)
  - Ensure `last_updated` set to current ISO8601 (`datetime.utcnow().isoformat() + 'Z'`).
  - Ensure `components` length capped at 3 and order corresponds to page order.
- [ ] Add unit tests (or parser smoke test script) under `scraper/tests/test_parser.py` that exercise helpers against stored HTML snippets (use `scraper/testdata/*.html`) (1.5h)

## Estimate
Total: 5.25 hours

## Research References
- Research.md: extract_usage_data function and JS helper example (`docs/Research.md:463-499`)
- EPIC-LIST.md: DOM scraping patterns and expected components (`docs/JIRA/EPIC-LIST.md:127-135`)
- Regex guidance for percentages (`docs/JIRA/EPIC-LIST.md:131`)

## Risks & Open Questions
- Technical risk: The live DOM may change class names or structure; rely on static text tokens as primary strategy.
- Open question: Which date parsing library is preferred (`python-dateutil` vs custom heuristics)? Add to dependencies if chosen.
- Ambiguity: Exact component names may vary; story uses ordering and proximity to static tokens rather than fixed labels.