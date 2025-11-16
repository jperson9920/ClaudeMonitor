# EPIC-08-STOR-03

Title: Fallback plain-text extraction and partial-result reporting

Epic: [`EPIC-08`](docs/JIRA/EPIC-LIST.md:84)

Status: TODO

## Description
As a developer I need a reliable fallback extraction path that scans raw page text when structured DOM extraction fails so the scraper can return partial but useful data and explicit diagnostics. This reduces total failures visible to the user and enables the UI to show partial information with clear status.

This story implements a plain-text extraction flow in `scraper/claude_scraper.py` and ensures the top-level JSON `status='partial'` and `found_components` reflect available data.

## Acceptance Criteria
- [ ] A fallback function `extract_from_text(page_source: str) -> List[dict]` is implemented and exported in `scraper/claude_scraper.py`.
- [ ] Fallback text extraction uses case-insensitive searches for tokens: "Time until reset", "Resets in", "Resets", and regex `\d{1,3}%\s*used` to find percentage values and nearby reset phrases.
- [ ] When DOM extraction fails, scraper returns JSON with `status='partial'`, includes `found_components` and per-component `raw_reset_text`, and sets `tokens_*` fields to null if not found.
- [ ] Diagnostics include which extraction strategies were attempted in `diagnostics['strategies']` (e.g., `['js', 'xpath', 'text_fallback']`) and any `cloudflare_detected` flag.
- [ ] Unit tests under `scraper/tests/test_fallback.py` validate behavior against `scraper/testdata/cloudflare_challenge.html` and `usage_alt.html`.

## Dependencies
- EPIC-02-STOR-02 (parsing helpers)
- EPIC-02-STOR-04 (fixtures & smoke-tests)
- EPIC-08-STOR-01 (retry handler integration)

## Tasks (1-3 hours)
- [ ] Implement `extract_from_text(page_source: str) -> List[dict]` in `scraper/claude_scraper.py` using regex and proximity heuristics (1.0h)
  - Use `re.findall` for percentages and scan ±200 characters for reset phrases.
- [ ] Integrate fallback into `extract_usage_data()` so it is invoked when primary strategies return no components; ensure `status='partial'` and `found_components` set accordingly (0.75h)
- [ ] Add diagnostics entries when fallback used:
  - `diagnostics['used_fallback'] = True`
  - `diagnostics['fallback_matches'] = <count>` (0.25h)
- [ ] Add unit tests `scraper/tests/test_fallback.py` asserting partial payload shape and values for provided fixtures (1.0h)
- [ ] Document fallback behavior and the policy for when to accept partial results in `scraper/protocol.md` (0.5h)

## Estimate
Total: 3.5 hours

## Research References
- DOM extraction fallback and partial-result behavior: `docs/JIRA/EPIC-LIST.md:133-135`
- Research.md: multi-strategy extraction and JS helper example (`docs/Research.md:463-499`)

## Risks & Open Questions
- Risk: Fallback may produce false positives in unrelated text; tests must be conservative and prioritize high-confidence matches.
- Open question: Threshold for accepting partial data (e.g., require at least 1 component vs. 2) — recommend accept any >0 and mark `status='partial'`.