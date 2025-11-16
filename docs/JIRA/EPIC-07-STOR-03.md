# EPIC-07-STOR-03

Title: Polling configuration, persistence and startup behavior

Epic: [`EPIC-07`](docs/JIRA/EPIC-LIST.md:74)

Status: TODO

## Description
As a user and operator I need configurable polling interval, persisted settings, and clear startup behavior so the widget resumes the expected polling state across restarts and obeys the 5-minute default polling frequency described in Research.md.

This story implements a small config subsystem (read/write JSON) used by the Rust backend and documents startup semantics.

## Acceptance Criteria
- [ ] `src-tauri/config.rs` (or `src-tauri/src/config.rs`) exists and exposes:
  - `pub struct AppConfig { pub polling_interval_secs: u64, pub start_on_login: bool }`
  - `pub fn load_config() -> AppConfig` (reads `~/.config/claude-usage-monitor/config.json` on Linux/macOS or `%APPDATA%\\ClaudeUsageMonitor\\config.json` on Windows)
  - `pub fn save_config(cfg: &AppConfig) -> Result<(), String>`
- [ ] Default polling interval is 300 seconds (5 minutes) if no config file present. (Reference Research.md lines 67-71 and EPIC-LIST.md:50)
- [ ] The Poller (EPIC-04-STOR-03) reads config at start and uses persisted interval; `start_polling()` accepts an override argument to temporarily force a different interval.
- [ ] `docs/JIRA/EPIC-07-TRAY.md` updated with instructions on how to change polling interval from UI and CLI (example `invoke('start_polling', { interval_secs: 600 })`) and how settings persist between restarts.
- [ ] Config read/write paths and permissions documented; ensure config file is created with owner-only permissions where possible.

## Dependencies
- EPIC-04-STOR-03 (Poller implementation)
- EPIC-06 (resource/bundle behavior for locating config if bundled)
- Research.md: polling interval and 5-minute default (`docs/Research.md:67-71`)

## Tasks (1-2 hours each)
- [ ] Implement `src-tauri/src/config.rs` with load/save functions and OS-aware config path resolution (1.25h)
  - Use `dirs` crate or Tauri API to locate platform config directories.
  - Ensure atomic write: write to temp file then rename.
- [ ] Modify polling code (`src-tauri/src/polling.rs`) so `Poller::start` accepts optional `interval_secs` and persists chosen interval via `save_config()` (0.75h)
- [ ] Add a simple CLI helper in Rust to print current config and to set polling interval for debug: `claude-usage-monitor --print-config` (0.5h)
- [ ] Update documentation `docs/JIRA/EPIC-07-TRAY.md` with examples for changing polling interval and description of defaults/behavior (0.5h)

## Estimate
Total: 3 hours

## Research References
- Polling frequency and 300s default: `docs/JIRA/EPIC-LIST.md:50` and Research.md polling notes `docs/Research.md:67-71`
- Poller responsibilities and visibility window: Research.md (`docs/Research.md:69-76`)

## Risks & Open Questions
- Risk: Platform differences in config path and permission handling; tests should verify Windows and POSIX paths.
- Open question: Should `start_on_login` be implemented for v1.0 or deferred to EPIC-10 (packaging/autostart)? Recommend document only and defer implementation unless requested.