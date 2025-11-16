# EPIC-09-STOR-03

Title: Automated CI test jobs and thresholds

Epic: [`EPIC-09`](docs/JIRA/EPIC-LIST.md:94)

Status: TODO

## Description
Configure CI pipeline jobs that run the integration and Cloudflare simulation test suites, enforce pass/fail thresholds, and emit structured artifacts and alerts. This story defines GitHub Actions workflows, job matrix for platform variations (Windows, Ubuntu), and failure handling (notify via repo checks and upload artifacts). Tests include fixture-only parser checks (fast), integration smoke tests (requires Chrome), and Cloudflare simulation iterations. Thresholds (e.g., minimum success_rate_percent) are enforced and cause job failure when not met.

From a CI engineer perspective: I can review `.github/workflows/ci-tests.yml` and see distinct jobs for lint, unit, parser-smoke, integration-headed (optional), and cloudflare-sim. The cloudflare-sim job should upload `artifacts/cloudflare_report.json` and fail if success_rate_percent < configured threshold.

## Acceptance Criteria
- [ ] `.github/workflows/ci-tests.yml` created with jobs:
  - `lint` — runs markdownlint or flake8 for scraper code where applicable.
  - `parser-smoke` — runs `scraper/tests/smoke_parser.py` using Python 3.9 on ubuntu-latest.
  - `cloudflare-sim` — runs `pytest tests/cloudflare` with `tests/cloudflare/config.yaml` and uploads `artifacts/cloudflare_report.json` as workflow artifact.
  - `integration-headed` (optional/conditional) — runs only when `runs-on: windows-latest` and `matrix.include.integration_headed: true` is set; documents that this job requires a hosted runner with Chrome and matching driver.
- [ ] CI enforces thresholds: cloudflare job fails if `success_rate_percent < tests/cloudflare/config.yaml:min_success_percent`. This is implemented using a post-run script step that parses `artifacts/cloudflare_report.json` and exits non-zero on threshold breach.
- [ ] Workflow uploads artifacts to the run and sets annotation on failure with a short summary: success_rate_percent and failure_modes top 3.
- [ ] Docs updated in `docs/JIRA/TEST_PLAN.md` with CI job names, trigger conditions, and recommended schedule (daily/nightly for cloudflare-sim) and a sample GitHub Actions YAML snippet.

## Dependencies
- EPIC-09-STOR-01 (integration test plan)
- EPIC-09-STOR-02 (cloudflare simulation harness)
- `.github/workflows/` must be present in repo root or will be created by this story.

## Tasks (1-3 hours each)
- [ ] Add workflow file `.github/workflows/ci-tests.yml` with defined jobs and environment matrix (2.0h)
  - Include steps to install Python, create venv, install `scraper/requirements.txt`, and run pytest.
- [ ] Add step in `cloudflare-sim` job to upload `artifacts/cloudflare_report.json` and parse it:
  - Script example path: `.github/scripts/check_cloudflare_threshold.py` accepting `--report artifacts/cloudflare_report.json --min 85` (1.5h)
  - Make sure script exits non-zero if below threshold.
- [ ] Update `docs/JIRA/TEST_PLAN.md` with CI guidance and required secrets/permissions (1.0h)
- [ ] Add example GitHub Actions annotations and artifact upload steps in the YAML (1.0h)

## Estimate
Total: 5.5 hours

## Research References
- EPIC-09 acceptance criteria and success-rate target: `docs/JIRA/EPIC-LIST.md:96-101`
- Research notes on CI and headless/headed behavior: `docs/Research.md:64-74`, `docs/Research.md:81-96`

## Risks & Open Questions
- Risk: GitHub Actions hosted runners may not allow running GUI Chrome in headed mode; `integration-headed` may require self-hosted runners. Document this clearly and gate the job with `if: matrix.include.integration_headed == 'true'`.
- Risk: Artifact retention and storage quotas—large artifact uploads could exceed limits if report sizes grow. Consider compressing artifacts.
- Open question: Which notification channel should be used for failing thresholds (email, Slack, or GitHub checks)? Flag for Orchestrator.
- Open question: Should the CI use a Docker image with Chrome preinstalled or rely on the runner's environment? Provide both options in docs.