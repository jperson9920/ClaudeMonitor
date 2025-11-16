# EPIC-09-STOR-01

Title: Create integration test plan and CI smoke tests

Epic: [`EPIC-09`](docs/JIRA/EPIC-LIST.md:94)

Status: TODO

## Description
As a QA engineer I need an integration test plan and a set of CI-friendly smoke tests that validate the end-to-end flows: fresh install → manual_login → polling → UI update. These tests must be runnable locally and in CI (when Python and Chrome are available) and use stored fixtures where live scraping is impractical.

## Acceptance Criteria
- [ ] `docs/JIRA/TEST_PLAN.md` exists with step-by-step manual and automated test plans covering happy path and failure scenarios.
- [ ] `tests/integration/` contains:
  - `test_manual_login_flow.md` (manual step checklist)
  - `test_polling_smoke.py` (pytest) that mocks Rust scraper invoker or uses stored fixture to simulate `poll_usage_once` response.
- [ ] `scraper/tests/smoke_parser.py` exists to run parser against fixtures and exit 0 on success.
- [ ] CI guidance added to `docs/JIRA/TEST_PLAN.md` including required environment (Python 3.9+, Chrome) and commands:
  - `python -m venv .venv && .venv/Scripts/activate && pip install -r scraper/requirements.txt && pytest -q`

## Dependencies
- EPIC-02 (parser & fixtures)
- EPIC-04 (Rust commands mocked for CI)
- EPIC-09-STOR-02 (Cloudflare simulation fixtures)

## Tasks (1-3 hours)
- [ ] Draft `docs/JIRA/TEST_PLAN.md` with manual and automated test cases, expected pass criteria, and CI setup instructions (1.5h)
- [ ] Add `tests/integration/test_polling_smoke.py` with a mocked `spawn_scraper` response asserting frontend/state update contract (1.5h)
- [ ] Add `scraper/tests/smoke_parser.py` that runs parser helpers against `scraper/testdata/*.html` and prints PASS/FAIL (1.0h)

## Estimate
Total: 4 hours

## Research References
- EPIC-LIST testing acceptance criteria: `docs/JIRA/EPIC-LIST.md:94-101`
- Research.md: integration flow and manual login requirements (`docs/Research.md:64-74`, `docs/Research.md:308-348`)

## Risks & Open Questions
- Risk: CI environments without Chrome will fail live tests; provide fixture-based alternatives and mark live tests as optional.
- Open question: Acceptable CI pass threshold for Cloudflare bypass simulation (EPIC-09 success rate goal 85-95%).