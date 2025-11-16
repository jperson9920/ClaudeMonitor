# EPIC-04-STOR-03

Title: Implement polling manager and IPC events (start_polling/stop_polling, usage-update events)

Epic: [`EPIC-04`](docs/JIRA/EPIC-LIST.md:44)

Status: DONE

## Description
As a backend engineer, I need the Rust polling manager to start/stop a background task that invokes the scraper at a configurable interval (default 300s) and emits Tauri events (`usage-update`, `usage-error`) with parsed JSON so the frontend and system tray can react in real time.

This story implements the polling lifecycle, configuration, and event emission in `src-tauri/src/polling.rs` and wires commands in `main.rs`.

## Acceptance Criteria
- [ ] `start_polling(interval_secs: u64)` command starts a background async task that:
  - Spawns scraper via `spawn_scraper` every `interval_secs`
  - Emits `usage-update` with serde_json payload on success
  - Emits `usage-error` with structured error on failure
- [ ] `stop_polling()` stops the background task cleanly (no orphan threads/processes)
- [ ] Default polling interval is 300 seconds (read from config if present)
- [ ] Polling task runs scraper in headed mode only briefly (~5-10s per invocation) by invoking Python scraper with single-run argument (e.g., `--poll_once`) and respecting scraper timeout
- [ ] Concurrency: starting polling when already running returns a clear error and does not spawn duplicate pollers
- [ ] Unit/integration tests under `src-tauri/tests/` assert start -> emits events -> stop semantics using mocked `spawn_scraper` that returns a known JSON payload

## Dependencies
- EPIC-04-STOR-01 (Rust skeleton)
- EPIC-04-STOR-02 (ScraperInterface)
- EPIC-02-STOR-03 (protocol for emitted JSON)

## Tasks (1-3 hours each)
- [ ] Implement Poller in `src-tauri/src/polling.rs` using `tokio::spawn` and `tokio::time::interval` (1.5h)
  - Struct: `pub struct Poller { interval_secs: u64, handle: Option<JoinHandle<()>>, running: AtomicBool }`
  - Methods: `start(&mut self, app_handle: tauri::AppHandle) -> Result<(), String>`, `stop(&mut self) -> Result<(), String>`
- [ ] Wire Tauri commands in `main.rs` to call `Poller::start` / `stop` and return immediate success/failure (0.75h)
  - Register commands with `#[tauri::command]`
- [ ] Ensure `spawn_scraper` is invoked with `["--poll_once"]` and timeout; handle returned serde_json as event payload (1.0h)
- [ ] Add tests `src-tauri/tests/test_poller.rs` that mock `spawn_scraper` to return a deterministic serde_json value and assert events captured by a test app instance (1.5h)
- [ ] Document commands and default interval in `docs/JIRA/EPIC-04-DEVNOTES.md` (0.25h)

## Estimate
Total: 5 hours

## Research References
- EPIC-LIST polling requirements and 300s default: `docs/JIRA/EPIC-LIST.md:46-51` and `docs/JIRA/EPIC-LIST.md:50`  
- Research.md backend polling responsibilities and data flow: `docs/Research.md:36-39`, `docs/Research.md:69-74`

## Risks & Open Questions
- Risk: Blocking or long-running subprocesses may block the poller; ensure subprocess timeouts and proper process termination.
- Open question: Should the poller use exponential backoff on repeated failures or continue at interval? Coordinate with EPIC-08 for retry policy.