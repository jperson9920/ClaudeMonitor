# EPIC-04-STOR-01

Title: Create src-tauri Rust project skeleton and command stubs

Epic: [`EPIC-04`](docs/JIRA/EPIC-LIST.md:44)

Status: TODO

## Description
As a developer I need a Tauri Rust backend skeleton with command stubs so the frontend can call backend commands and the Rust project compiles. This establishes the IPC surface and provides placeholders for scraper process management and polling logic.

This story creates:
- `src-tauri/Cargo.toml`
- `src-tauri/src/main.rs`
- `src-tauri/src/scraper.rs`
- `src-tauri/src/polling.rs`

Stubbed functions (signatures included) will compile and return mocked values; full implementations are covered by later stories.

## Acceptance Criteria
- [ ] `src-tauri` is a valid Cargo project and `cargo build` succeeds (with the stubs).
- [ ] `main.rs` registers the Tauri commands:
  - `#[tauri::command] fn start_polling(interval_secs: u64) -> Result<(), String>`
  - `#[tauri::command] fn stop_polling() -> Result<(), String>`
  - `#[tauri::command] fn manual_login() -> Result<serde_json::Value, String>`
  - `#[tauri::command] fn check_session() -> Result<serde_json::Value, String>`
  - `#[tauri::command] fn poll_usage_once() -> Result<serde_json::Value, String>`
- [ ] `scraper.rs` exposes:
  - `pub fn spawn_scraper(args: Vec<String>) -> Result<serde_json::Value, ScraperError>`
  - `pub fn parse_scraper_output(raw: &str) -> Result<serde_json::Value, ScraperError>`
- [ ] `polling.rs` contains a minimal background task controller interface:
  - `pub struct Poller { interval_secs: u64, running: AtomicBool }`
  - `impl Poller { pub fn start(&self) -> Result<(), String>; pub fn stop(&self) -> Result<(), String>; }`
- [ ] `Cargo.toml` includes `tauri`, `serde`, `serde_json`, `tokio` (for async tasks), and builds successfully.

## Dependencies
- EPIC-01 (toolchain, Rust)
- EPIC-02 (scraper protocol) for future integration
- Research.md lines about Rust backend responsibilities and IPC (`docs/Research.md:34-51`, `docs/Research.md:69-74`)

## Tasks (1-3 hours each)
- [ ] Create `src-tauri/Cargo.toml` with dependencies and package metadata. Example dependencies to include:
  - tauri = { version = "1", features = ["api-all"] }
  - serde = { version = "1", features = ["derive"] }
  - serde_json = "1"
  - tokio = { version = "1", features = ["rt-multi-thread", "macros"] }
  (0.5h)
- [ ] Add `src-tauri/src/main.rs` that:
  - Initializes Tauri app
  - Registers the commands above using `tauri::Builder::invoke_handler`
  - Returns mocked JSON objects for `manual_login`, `check_session`, and `poll_usage_once` to allow frontend to exercise flow without scraper. (1.0h)
  - Example stub: `Ok(serde_json::json!({"status":"ok","components":[]}))`
- [ ] Add `src-tauri/src/scraper.rs` implementing `spawn_scraper` and `parse_scraper_output`:
  - `spawn_scraper` should demonstrate `std::process::Command::new("python").arg("scraper/claude_scraper.py").arg("--check_session")...` but return mocked value for now. (1.0h)
  - Include `ScraperError` enum with Display/From conversions. (0.5h)
- [ ] Add `src-tauri/src/polling.rs` with `Poller` struct and stubbed `start`/`stop` returning Ok. Use `std::sync::atomic::AtomicBool` and `std::sync::Arc`. (1.0h)
- [ ] `cargo build` instructions documented in `docs/JIRA/EPIC-04-DEVNOTES.md` including `cd src-tauri && cargo build` (0.25h)

## Estimate
Total: 4.25 hours

## Research References
- Rust backend responsibilities, spawn subprocess and parse JSON: Research.md lines 34-39, 69-74 [`docs/Research.md:34-39`, `docs/Research.md:69-74`]
- EPIC-LIST expectations for commands and polling interval (300s default): `docs/JIRA/EPIC-LIST.md:44-51`

## Risks & Open Questions
- Risk: Tauri CLI version mismatches may require feature adjustments; pinning in `Cargo.toml` recommended.
- Open question: Use synchronous process spawning vs. async `tokio::process::Command` for subprocess IO; recommend async for production but stubs use sync for simplicity until EPIC-06.