# EPIC-09-STOR-02

Title: Cloudflare simulation & performance measurement

Epic: [`EPIC-09`](docs/JIRA/EPIC-LIST.md:94)

Status: TODO

## Description
Create a reproducible test harness that simulates Cloudflare challenge interactions and measures the scraper's ability to bypass or recover from them in headed (real browser) mode. The harness will provide mock challenge pages and scripted challenge interactions (JS challenge, interstitial, CAPTCHA placeholder) so the scraper can be exercised deterministically. Test runs must collect performance metrics (time-to-solution, retries, failure reason) and compute a success-rate metric for bypass attempts. This story implements fixtures, a pytest-based runner, and a simple results aggregator.

From a QA perspective: I can run `pytest tests/cloudflare/` locally or in CI, feed in different challenge fixtures, and assert the observed bypass success rate meets the project's target (configurable target: 85–95%).

## Acceptance Criteria
- [ ] `tests/cloudflare/test_cf_sim.py` (pytest) exists and implements end-to-end scenarios that:
  - instantiate a real Chrome webdriver with `chrome-profile` pointing to `scraper/chrome-profile-test/`
  - navigate to local mock challenge pages and invoke `scraper.create_driver()` / `scraper.navigate_to_usage_page()` or call `simulate_cloudflare_challenge(...)` helpers
- [ ] `tests/cloudflare/fixtures/` contains three challenge fixtures:
  - `js_challenge.html`, `interstitial_challenge.html`, `captcha_placeholder.html`
  - Fixtures referenced in `tests/cloudflare/test_cf_sim.py` using relative paths
- [ ] A metrics aggregator `tests/cloudflare/aggregate_results.py` produces a JSON report with fields: `runs`, `success_count`, `failure_modes` (map), `avg_time_s`, `success_rate_percent`. Example output file: `artifacts/cloudflare_report.json`
- [ ] Test harness computes and asserts success rate is within target: configurable in `tests/cloudflare/config.yaml` (default min: 85, max: 95). The pytest run fails if `success_rate_percent < config.min_success_percent`.
- [ ] Research reference included: `docs/Research.md:81-96` (anti-detection success rates) and the test harness cites these lines in the file's "Research References" section.

## Dependencies
- EPIC-09-STOR-01 (integration test plan)
- EPIC-02-STOR-05 (Cloudflare handling docs & scraper anti-detection tuning)
- Local test runner requires Chrome available in CI or headless-capable environment (or use stored fixture-only runs).
- Optional: `chromedriver` or matching webdriver for system Chrome.

## Tasks (1-4 hours each)
- [ ] Add fixtures: create `tests/cloudflare/fixtures/js_challenge.html`, `interstitial_challenge.html`, `captcha_placeholder.html` and verify they open in a regular browser (1.5h)
  - File paths: `tests/cloudflare/fixtures/js_challenge.html`
  - Quick check: Open locally: `start tests/cloudflare/fixtures/js_challenge.html` (Windows) or `python -m http.server --directory tests/cloudflare/fixtures 8000` and browse to `http://localhost:8000/js_challenge.html` (1.0h)
- [ ] Implement simulator helpers: `tests/cloudflare/helpers.py` with function signatures:
  - `def simulate_cloudflare_challenge(driver: selenium.webdriver.Chrome, fixture_path: str) -> Tuple[bool, dict]:`
  - `def wait_for_challenge_solved(driver: selenium.webdriver.Chrome, timeout_s: int = 30) -> bool` (2.0h)
  - Save to: `tests/cloudflare/helpers.py` (use explicit import lines in test file)
- [ ] Implement pytest suite: `tests/cloudflare/test_cf_sim.py` to run N iterations (configurable in `tests/cloudflare/config.yaml`), record result per-run, and call the aggregator (2.5h)
  - Example run command (local): `python -m venv .venv && .venv/Scripts/activate && pip install -r scraper/requirements.txt && pytest tests/cloudflare -q`
- [ ] Implement aggregator: `tests/cloudflare/aggregate_results.py` that writes `artifacts/cloudflare_report.json` and returns non-zero on failure if success_rate < threshold (1.5h)
- [ ] Add docs: Append "Cloudflare simulation" section to `docs/JIRA/TEST_PLAN.md` describing how to run, configs, and interpretation of `artifacts/cloudflare_report.json` (1.0h)
- [ ] Add example configuration: `tests/cloudflare/config.yaml` with keys:
  - `iterations: 20`
  - `min_success_percent: 85`
  - `max_success_percent: 95` (0.5h)

## Estimate
Total: 9 hours (spread across the tasks above)

## Research References
- Anti-detection & empirical success-rate guidance: `docs/Research.md:81-96`
- Session persistence & profile location guidance (used for test profile): `docs/Research.md:248-259`
- Notes on running headed vs headless and CI environment constraints: `docs/Research.md:64-74`

## Risks & Open Questions
- Risk: CI runners without a visible Chrome or an appropriate chromedriver will not be able to run headed tests; the harness must support fixture-only "parser-only" runs that do not require live Chrome.
- Risk: Simulated fixtures cannot perfectly emulate Cloudflare's live behavior; measured success rates are indicative, not exact.
- Open question: Should the CI run use the real Chrome in headed mode for a percentage of runs, or rely solely on fixture-driven metrics? (Flag for Orchestrator / Dev team)
- Open question: Which artifact retention policy for `artifacts/cloudflare_report.json` is desired in CI? (S3/Artifacts vs local only)