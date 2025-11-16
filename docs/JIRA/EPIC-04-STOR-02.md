# EPIC-04-STOR-02

Title: Implement ScraperInterface in Rust to spawn Python subprocess and parse JSON

Epic: [`EPIC-04`](docs/JIRA/EPIC-LIST.md:44)

Status: DONE

## Description
As a backend engineer, I need a concrete ScraperInterface in Rust that reliably spawns the Python scraper subprocess, enforces the stdout/stderr protocol, parses JSON output, and returns structured serde_json::Value so the Tauri app can consume usage data.

This story implements `src-tauri/src/scraper.rs` (real implementation, replacing the earlier stub) with robust process invocation, timeouts, and error mapping to ScraperError codes.

## Acceptance Criteria
- [ ] `spawn_scraper(args: Vec<String>, timeout_secs: u64) -> Result<serde_json::Value, ScraperError>` implemented and tested locally.
- [ ] The function uses `tokio::process::Command` (async) or `std::process::Command` with threads to avoid blocking the Tauri main thread; documented choice in comments.
- [ ] `spawn_scraper` enforces a read timeout (default 30s); if JSON not received within timeout, returns `ScraperError::Timeout`.
- [ ] `parse_scraper_output(raw: &str) -> Result<serde_json::Value, ScraperError>` validates schema (components array, status) and returns descriptive errors for malformed JSON.
- [ ] Errors map to frontend-friendly strings and the error codes defined in `scraper/protocol.md` (EPIC-02-STOR-03).
- [ ] Unit tests `src-tauri/tests/test_scraper_integration.rs` simulate subprocess stdout/stderr (use a small test helper binary or mock) and validate error handling.

## Dependencies
- EPIC-02-STOR-03 (scraper/protocol.md)
- EPIC-04-STOR-01 (Rust project skeleton)
- EPIC-01 (toolchain)

## Tasks (1-3 hours)
- [ ] Implement `spawn_scraper` using `tokio::process::Command` (or sync + thread) in `src-tauri/src/scraper.rs` (1.5h)
  - Example invocation:
    - python path: `"python"`
    - args: `["scraper/claude_scraper.py", "--check_session"]` or `["--poll_once"]`
    - Use resource_dir resolution for bundled app (documented)
- [ ] Implement `parse_scraper_output(raw: &str) -> Result<serde_json::Value, ScraperError>` validating expected keys and value types (0.75h)
- [ ] Add `ScraperError` enum variants: `Io`, `Timeout`, `JsonParse`, `Protocol`, `Execution` with `Display` impl and conversion from `std` errors (0.5h)
- [ ] Add integration-style tests under `src-tauri/tests/` to mock subprocess output using a local helper script/binary (1.0h)
- [ ] Document `cd src-tauri && cargo test -q` test command in `docs/JIRA/EPIC-04-DEVNOTES.md` (0.25h)

## Estimate
Total: 4 hours

## Research References
- JSON/stdout contract: `scraper/protocol.md` (EPIC-02-STOR-03) and Research.md data flow lines 69-74 [`docs/Research.md:69-74`]
- EPIC-LIST expectations for Rust->Python IPC (EPIC-04 lines 45-51) [`docs/JIRA/EPIC-LIST.md:45-51`]

## Risks & Open Questions
- Risk: Blocking the main Tauri thread when spawning a long-running process — prefer async tokio approach.
- Open question: During bundling, Python path resolution differs; document resource_dir resolution and PyInstaller options in EPIC-06.