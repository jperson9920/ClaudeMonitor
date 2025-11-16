# EPIC LIST — Claude Usage Monitor

Summary:
This file contains 10 high-level epics covering the end-to-end implementation of the Claude Usage Monitor desktop widget (v1.0 single-user).

Key constraints considered: Python subprocess (undetected-chromedriver), headed browser mode, session persistence, 5‑minute polling.

Scraping strategy (v1.0):
- Target the three usage components by locating the static text "Time until reset" and extracting the adjacent percentage ("NN% used") and duration strings.
- Single user only; no multi-account or cloud sync for v1.0.

---

## EPIC-01: Project Setup & Environment
Goal: Establish reproducible development environment and project skeleton.
Acceptance Criteria:
- Repo contains initial Tauri project scaffold (src-tauri, src) and scraper/ directory.
- Development toolchain documented (Node 18+, Rust 1.70+, Python 3.9+).
- README includes setup steps for creating Python venv and installing dependencies.
- Basic CI/local checklist added to docs/JIRA/EPIC-LIST.md (or README).
Effort: Small (1–3 days)
Dependencies: None

## EPIC-02: Python Scraper Core Engine
Goal: Implement ClaudeUsageScraper to reliably extract the three usage percentages and reset times.
Acceptance Criteria:
- claude_scraper.py implements create_driver, manual_login, load_session, navigate_to_usage_page, extract_usage_data, poll_usage.
- extract_usage_data locates DOM blocks by searching for static text "Time until reset" and extracts exactly three percentage values and three reset durations.
- JSON output includes structured fields for each component: id/name, usage_percent, tokens_used (optional), tokens_limit (optional), reset_time (ISO 8601 or human-readable), last_updated, status.
- Headed, use_subprocess, and persistent profile are enabled; script logs actions to scraper/scraper.log.
Effort: Large (8–14 days)
Dependencies: EPIC-01

## EPIC-03: Session Management & Authentication
Goal: Provide one-time manual login flow and robust session persistence.
Acceptance Criteria:
- Manual login mode (--login) opens headed browser and instructs user to authenticate.
- Cookies/profile saved under scraper/chrome-profile and load_session validates age (configurable default 7 days).
- check_session and manual_login commands available to Rust backend and return deterministic results.
- Document safe storage recommendations and a clear re-login procedure.
Effort: Medium (4–7 days)
Dependencies: EPIC-02

## EPIC-04: Tauri Desktop Widget Foundation (Rust backend)
Goal: Implement Rust backend to manage scraper subprocess, polling state, and IPC.
Acceptance Criteria:
- src-tauri Rust project with main.rs, scraper.rs, polling.rs compiles and runs.
- ScraperInterface spawns Python process, reads JSON stdout, returns parsed serde_json::Value.
- start_polling/stop_polling, manual_login, check_session, and poll_usage tauri commands implemented and tested locally.
- Polling interval configurable and defaulted to 300 seconds.
Effort: Medium (4–7 days)
Dependencies: EPIC-01, EPIC-02, EPIC-03 (for validation)

## EPIC-05: React Frontend UI & Visualization
Goal: Build the dashboard UI showing three usage components, progress bars, timers, and alerts.
Acceptance Criteria:
- App.tsx and components (UsageDisplay, ProgressBar, ResetTimer) render three components with percentage and reset value per component.
- Alerts shown at >80% (warning) and ≥100% (critical); last_updated displayed.
- Manual refresh and login flows wired to backend commands.
- Responsive styling and accessible labels for screen readers.
Effort: Medium (4–7 days)
Dependencies: EPIC-04

## EPIC-06: Rust–Python IPC Integration & Bundling
Goal: Make scraper available to bundled app and ensure robust IPC between Rust and Python.
Acceptance Criteria:
- Tauri bundle includes scraper resources and Rust resolves resource_dir correctly.
- Rust handles Python invocation errors, non-JSON stdout, and returns structured errors to frontend.
- End-to-end manual test: manual_login → poll_usage returns valid JSON and frontend displays data.
- Document bundling and distribution notes for Python dependency handling (PyInstaller or bundled Python).
Effort: Large (8–14 days)
Dependencies: EPIC-02, EPIC-04, EPIC-05

## EPIC-07: System Tray, Background Polling & Scheduling
Goal: Implement background polling, system tray controls, and force-refresh functionality.
Acceptance Criteria:
- System tray menu with Show Dashboard, Refresh Now, Quit implemented.
- start_polling triggers a background task running every configured interval; emits usage-update and usage-error events.
- Force-refresh from tray triggers immediate poll and updates UI.
- Browser is only visible during manual login and brief poll windows (~5–10s).
Effort: Medium (4–7 days)
Dependencies: EPIC-04, EPIC-06, EPIC-05

## EPIC-08: Error Handling, Retries & Resilience
Goal: Implement robust retry logic, fallbacks, and clear error surfaces.
Acceptance Criteria:
- Exponential backoff retry handler for transient failures with configurable max attempts.
- Fallback plain-text extraction path returns partial data and sets status 'partial'.
- Clear error codes for session_required, navigation_failed, session_expired, extraction_failed, fatal.
- Logs include enough context for debugging (timestamps, stderr capture).
Effort: Medium (4–7 days)
Dependencies: EPIC-02, EPIC-04, EPIC-06

## EPIC-09: End-to-End Testing & Validation
Goal: Validate system behavior with manual and automated tests.
Acceptance Criteria:
- Integration test: Fresh install → manual_login → polling runs → three components populated correctly.
- Simulated Cloudflare/challenge scenarios documented and manual mitigation steps verified.
- Logging/monitoring checks in place (scraper.log); automated smoke tests for parser against stored HTML samples.
- Success rate measured: validate 85–95% bypass success in headed mode during test runs.
Effort: Medium (4–7 days)
Dependencies: EPIC-02..EPIC-08

## EPIC-10: Distribution, Packaging & Security
Goal: Produce a v1.0 single-user distributable and document security practices.
Acceptance Criteria:
- Platform builds created (macOS, Windows, Linux) using Tauri build producing installers/artifacts.
- Guidance included for bundling or requiring Python installation; optional PyInstaller recipe documented.
- Security guidance added: secure chrome-profile storage, file permissions, not syncing profile to cloud.
- Optional: Code signing instructions documented (macOS/Windows).
Effort: Small (1–3 days)
Dependencies: EPIC-06, EPIC-09

---

Open Questions / Ambiguities (to resolve during implementation):
- Exact DOM selectors cannot be finalized until the live claude.ai/settings/usage HTML is inspected; EPIC-02 includes discovery via searching for "Time until reset".
- Distribution strategy for Python runtime (bundle Python vs. require system Python) needs decision; EPIC-06 notes both approaches.
- Handling of non-Max plans: default token_limit is 88,000; decide whether to auto-detect plan or provide manual config.
- Retry/backoff parameters (initial delay, multiplier, max attempts) to be set in configuration (suggest defaults in EPIC-08).

Notes for handoff:
- This EPIC list is scoped for a single end-user (the requester) for v1.0. Multi-account, historical DB, and auto-updates are out-of-scope unless requested later.
- Implementation must preserve local browser windows (do not close or interfere with user Chrome sessions beyond the chrome-profile used by the scraper).

End of file.
## Clarification: DOM scraping patterns

- Goal: capture the three "% used" values and their corresponding "Resets" values from the live usage page.
- Locator strategy: search the page for static strings such as "Resets in", "Resets Thu", "Resets" or "Time until reset" (case-insensitive) to find each usage component block.
- Percentage extraction: match patterns like /\d{1,3}%\s*used/ and parse the numeric value to produce usage_percent.
- Reset extraction: accept phrases like "Resets in 59 min", "Resets Thu 4:00 PM", etc. Normalize to ISO 8601 when possible; if not possible, include raw_reset_text alongside reset_time=null.
- Expected v1.0 components (single-user): "Current session", "Weekly limits — All models", "Weekly limits — Opus only". Return an array `components[]` with one entry per component.
- If fewer than three components are found, return available components and set top-level status to "partial" with a diagnostic field `found_components`.
- Update EPIC-02 to reference this scraping clarification and use the patterns above when implementing extract_usage_data().