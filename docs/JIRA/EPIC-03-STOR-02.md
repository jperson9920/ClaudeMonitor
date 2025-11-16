# EPIC-03-STOR-02

Title: Expose check_session and manual_login commands for Rust IPC

Epic: [`EPIC-03`](docs/JIRA/EPIC-LIST.md:34)

Status: TODO

## Description
As a developer, I need the Python scraper to expose command-line entrypoints that Rust can invoke to check session validity and trigger manual login flows. These will be used by the Rust Tauri backend to orchestrate polling without embedding authentication logic in Rust.

Required CLI commands:
- `python claude_scraper.py --check_session` -> returns exit code 0 and prints `{"session_valid": true}` to stdout if valid, else prints `{"session_valid": false}` and exit code 2.
- `python claude_scraper.py --login` -> opens headed browser, waits for manual login, saves session, prints `{"login": "success"}` or error JSON to stderr and non-zero exit code.

## Acceptance Criteria
- [ ] `claude_scraper.py` supports `--check_session` and `--login` CLI flags using `argparse`.
- [ ] `--check_session` performs `load_session()` and a lightweight `check_session_valid()` (without opening a new browser) if possible; returns deterministic JSON to stdout.
- [ ] `--login` performs manual login flow described in `EPIC-02-STOR-01` and saves session file on success; prints JSON success to stdout.
- [ ] Commands return appropriate exit codes (0 success, 2 session invalid, 3 login failed, 4 fatal) and stderr logs errors.

## Dependencies
- EPIC-03-STOR-01 (session manager)
- EPIC-02-STOR-01 (driver methods)

## Tasks
- [ ] Add `if __name__ == "__main__":` CLI parsing with `argparse` in `scraper/claude_scraper.py` (0.5h)
- [ ] Implement `--check_session` behavior: load session, optionally create a short-lived driver to verify if needed (config flag) (1.0h)
- [ ] Implement `--login` behavior that calls `manual_login()` and saves session; ensure instructions printed to stderr per Research.md (1.5h)
- [ ] Add unit tests or script demonstrating CLI outputs for both flags (`scraper/tests/test_cli.py`) (1.0h)

## Estimate
Total: 4 hours

## Research References
- Manual login flow and CLI guidance: Research.md lines 308-348 (manual login instructions) [`docs/Research.md:308-348`]
- Session rules and storage: Research.md lines 356-370, 389-396 [`docs/Research.md:356-370`, `docs/Research.md:389-396`]
- EPIC-LIST CLI requirements: `docs/JIRA/EPIC-LIST.md:36-40`

## Risks & Open Questions
- Risk: Performing a live `check_session` by starting a driver may open browser windows; provide option to configure `--check-session --no-verify` to only check local session file.
- Open question: Should CLI print human-readable instructions or machine-only JSON? Implement both: JSON to stdout, human instructions to stderr.