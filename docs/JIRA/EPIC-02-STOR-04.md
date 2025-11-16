# EPIC-02-STOR-04

Title: Add parser smoke-tests and stored HTML fixtures

Epic: [`EPIC-02`](docs/JIRA/EPIC-LIST.md:24)

Status: TODO

## Description
As a developer, I need regression tests that validate the parser against saved HTML snapshots of the usage page so extraction changes don't break silently. This enables verifying the multi-strategy extraction (JS -> DOM -> plain-text) and Cloudflare/fallback behavior described in Research.md.

## Acceptance Criteria
- [ ] `scraper/testdata/` contains at least 3 HTML snapshots (examples: normal usage page, alternate layout, Cloudflare challenge page).
- [ ] `scraper/tests/test_parser.py` imports parser helpers from `scraper/claude_scraper.py` and asserts expected values for each fixture (percentages, reset text presence, found_components count).
- [ ] Test runner `scraper/run_parser_tests.sh` / `scraper/run_parser_tests.ps1` exists and runs tests in venv, printing PASS/FAIL and exit code.
- [ ] CI-friendly output: tests use pytest and exit non-zero on failures.

## Dependencies
- EPIC-02-STOR-02 (parsing helpers available)
- EPIC-01 (test venv & requirements)

## Tasks (1-3 hours each)
- [ ] Add directory `scraper/testdata/` and include at least 3 saved HTML files:
  - `usage_normal.html` (representative successful DOM)
  - `usage_alt.html` (alternate DOM layout)
  - `cloudflare_challenge.html` (challenge page snapshot)
  - Guidance: Save from browser "Save page as" and sanitize PII before check-in. (0.75h)
- [ ] Create `scraper/tests/test_parser.py`:
  - Test functions:
    - `test_parse_percentage()`: unit tests for `parse_percentage()` with multiple inputs
    - `test_parse_reset_time()` with various human-readable strings
    - `test_extract_usage_from_fixture()` loads fixture, mocks `driver.execute_script` or uses a minimal HTML parser to emulate DOM and asserts `found_components == 3` or expected partial state. (1.0h)
  - Use pytest and include instructions for running in README. (1.0h)
- [ ] Add `scraper/run_parser_tests.sh` and PowerShell equivalent to activate venv and run `pytest -q scraper/tests` (0.25h)
- [ ] Document test approach in `scraper/TESTS.md` including how to update fixtures and expected outputs (0.5h)

## Estimate
Total: 3.5 hours

## Research References
- Research.md: DOM extraction strategy and JS helper example (`docs/Research.md:463-499`)
- EPIC-LIST.md: DOM scraping clarification and requirement for returning partials (`docs/JIRA/EPIC-LIST.md:127-135`)

## Risks & Open Questions
- Risk: Fixtures may contain dynamic tokens or timestamps that make assertions brittle; tests should assert normalized numeric values and presence of reset text, not exact timestamps.
- Open question: Should fixtures be included in the repository or stored externally? Recommend including sanitized fixtures for reproducible CI.