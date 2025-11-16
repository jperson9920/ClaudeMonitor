# JIRA Index — Claude Usage Monitor

This index lists EPICs and the implementation-ready stories created for each epic. Each story file is a self-contained specification including file paths, commands, acceptance criteria, estimates, and references to Research.md.

Notes:
- Story status defaults to TODO unless otherwise indicated in the file.
- Filenames are clickable links to the story files.

## EPIC-01: Project Setup & Environment
- [`EPIC-01-STOR-01`](docs/JIRA/EPIC-01-STOR-01.md:1) — Initialize repository, toolchain docs and Tauri scaffold — Status: TODO — Estimate: 4h — Depends: none
- [`EPIC-01-STOR-02`](docs/JIRA/EPIC-01-STOR-02.md:1) — Pin toolchain (.nvmrc, rust-toolchain) and add devcontainer — Status: TODO — Estimate: 3h — Depends: EPIC-01-STOR-01
- [`EPIC-01-STOR-03`](docs/JIRA/EPIC-01-STOR-03.md:1) — Add scraper venv template, requirements, and sample run script — Status: TODO — Estimate: 2h — Depends: EPIC-01-STOR-01

## EPIC-02: Python Scraper Core Engine
- [`EPIC-02-STOR-01`](docs/JIRA/EPIC-02-STOR-01.md:1) — Implement ClaudeUsageScraper core and driver lifecycle — Status: TODO — Estimate: 6h — Depends: EPIC-01
- [`EPIC-02-STOR-02`](docs/JIRA/EPIC-02-STOR-02.md:1) — Implement DOM extraction logic for usage components (exactly 3 components) — Status: TODO — Estimate: 5.25h — Depends: EPIC-02-STOR-01
- [`EPIC-02-STOR-03`](docs/JIRA/EPIC-02-STOR-03.md:1) — JSON output schema and stdout protocol for Rust IPC — Status: TODO — Estimate: 2h — Depends: EPIC-02-STOR-01
- [`EPIC-02-STOR-04`](docs/JIRA/EPIC-02-STOR-04.md:1) — Add parser smoke-tests and stored HTML fixtures — Status: TODO — Estimate: 3.5h — Depends: EPIC-02-STOR-02
- [`EPIC-02-STOR-05`](docs/JIRA/EPIC-02-STOR-05.md:1) — Cloudflare challenge handling and anti-detection tuning in scraper — Status: TODO — Estimate: 4h — Depends: EPIC-02-STOR-01, EPIC-08

## EPIC-03: Session Management & Authentication
- [`EPIC-03-STOR-01`](docs/JIRA/EPIC-03-STOR-01.md:1) — Implement session manager: save/load session and profile directory — Status: TODO — Estimate: 4.25h — Depends: EPIC-02-STOR-01
- [`EPIC-03-STOR-02`](docs/JIRA/EPIC-03-STOR-02.md:1) — Expose check_session and manual_login commands for Rust IPC — Status: TODO — Estimate: 4h — Depends: EPIC-03-STOR-01
- [`EPIC-03-STOR-03`](docs/JIRA/EPIC-03-STOR-03.md:1) — Document re-login procedure and safe storage recommendations — Status: TODO — Estimate: 2.25h — Depends: EPIC-03-STOR-01

## EPIC-04: Tauri Desktop Widget Foundation (Rust backend)
- [`EPIC-04-STOR-01`](docs/JIRA/EPIC-04-STOR-01.md:1) — Create src-tauri Rust project skeleton and command stubs — Status: TODO — Estimate: 4.25h — Depends: EPIC-01
- [`EPIC-04-STOR-02`](docs/JIRA/EPIC-04-STOR-02.md:1) — Implement ScraperInterface in Rust to spawn Python subprocess and parse JSON — Status: TODO — Estimate: 4h — Depends: EPIC-02-STOR-03
- [`EPIC-04-STOR-03`](docs/JIRA/EPIC-04-STOR-03.md:1) — Implement polling manager and IPC events (start_polling/stop_polling, usage-update events) — Status: TODO — Estimate: 5h — Depends: EPIC-04-STOR-02

## EPIC-05: React Frontend UI & Visualization
- [`EPIC-05-STOR-01`](docs/JIRA/EPIC-05-STOR-01.md:1) — Implement frontend UsageDisplay component and data model — Status: TODO — Estimate: 3.5h — Depends: EPIC-04, EPIC-02
- [`EPIC-05-STOR-02`](docs/JIRA/EPIC-05-STOR-02.md:1) — Implement ProgressBar and ResetTimer UI components — Status: TODO — Estimate: 4.25h — Depends: EPIC-05-STOR-01
- [`EPIC-05-STOR-03`](docs/JIRA/EPIC-05-STOR-03.md:1) — Wire frontend to Rust backend commands and system tray events — Status: TODO — Estimate: 4.25h — Depends: EPIC-04

## EPIC-06: Rust–Python IPC Integration & Bundling
- [`EPIC-06-STOR-01`](docs/JIRA/EPIC-06-STOR-01.md:1) — Define bundling strategy and resource resolution for Python scraper — Status: TODO — Estimate: 3h — Depends: EPIC-04, EPIC-02
- [`EPIC-06-STOR-02`](docs/JIRA/EPIC-06-STOR-02.md:1) — Implement Rust bundling support for scraper resources and launcher — Status: TODO — Estimate: 4h — Depends: EPIC-06-STOR-01

## EPIC-07: System Tray, Background Polling & Scheduling
- [`EPIC-07-STOR-01`](docs/JIRA/EPIC-07-STOR-01.md:1) — Implement system tray menu and basic UI actions — Status: TODO — Estimate: 3.25h — Depends: EPIC-04
- [`EPIC-07-STOR-02`](docs/JIRA/EPIC-07-STOR-02.md:1) — Implement force-refresh command and visibility window policy for scraper runs — Status: TODO — Estimate: 2.5h — Depends: EPIC-04, EPIC-02
- [`EPIC-07-STOR-03`](docs/JIRA/EPIC-07-STOR-03.md:1) — Polling configuration, persistence and startup behavior — Status: TODO — Estimate: 3h — Depends: EPIC-04

## EPIC-08: Error Handling, Retries & Resilience
- [`EPIC-08-STOR-01`](docs/JIRA/EPIC-08-STOR-01.md:1) — Implement exponential backoff retry handler and integration points — Status: TODO — Estimate: 5.25h — Depends: EPIC-02, EPIC-04
- [`EPIC-08-STOR-02`](docs/JIRA/EPIC-08-STOR-02.md:1) — Define structured error codes, diagnostics schema and logging format — Status: TODO — Estimate: 3.25h — Depends: EPIC-08-STOR-01
- [`EPIC-08-STOR-03`](docs/JIRA/EPIC-08-STOR-03.md:1) — Fallback plain-text extraction and partial-result reporting — Status: TODO — Estimate: 3.5h — Depends: EPIC-02-STOR-02

## EPIC-09: End-to-End Testing & Validation
- [`EPIC-09-STOR-01`](docs/JIRA/EPIC-09-STOR-01.md:1) — Create integration test plan and CI smoke tests — Status: TODO — Estimate: 4h — Depends: EPIC-02..EPIC-08
- [`EPIC-09-STOR-02`](docs/JIRA/EPIC-09-STOR-02.md:1) — Cloudflare simulation & performance measurement — Status: TODO — Estimate: 9h — Depends: EPIC-02..EPIC-08
- [`EPIC-09-STOR-03`](docs/JIRA/EPIC-09-STOR-03.md:1) — Automated CI test jobs and thresholds — Status: TODO — Estimate: 5.5h — Depends: EPIC-09-STOR-01, EPIC-09-STOR-02

## EPIC-10: Distribution, Packaging & Security
- [`EPIC-10-STOR-01`](docs/JIRA/EPIC-10-STOR-01.md:1) — Build targets and Tauri packaging recipe — Status: TODO — Estimate: 7.5h — Depends: EPIC-06, EPIC-04
- [`EPIC-10-STOR-02`](docs/JIRA/EPIC-10-STOR-02.md:1) — Security guidance: chrome-profile storage, file permissions, and optional encryption — Status: TODO — Estimate: 6h — Depends: EPIC-03, EPIC-06, EPIC-10-STOR-01

---

Summary (current snapshot):
- Epics processed: 10/10 (complete)
- Stories created: 30 files
- Remaining stories: none
- Next steps:
  - Finalize index and run quality pass to ensure each story contains required sections
  - Hand off to Orchestrator for git operations (follow RooWrapper DryRun → Validate → Apply)
