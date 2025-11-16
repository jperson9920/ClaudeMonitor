# EPIC-07-STOR-02

Title: Implement force-refresh command and visibility window policy for scraper runs

Epic: [`EPIC-07`](docs/JIRA/EPIC-LIST.md:74)

Status: DONE

## Description
As a user I need a force-refresh mechanism that triggers an immediate poll outside the regular schedule and a clear visibility-window policy so the headed browser is only visible briefly (5–10s) during automated polls or when manual login is active.

This story implements the Rust command `poll_usage_once()` behavior, documents the visibility window policy, and ensures the Python scraper respects a single-run execution mode.

## Acceptance Criteria
- [ ] `poll_usage_once()` Rust command exists and launches the scraper with argument `--poll_once` (or equivalent) and returns the parsed JSON payload to the caller.
- [ ] `poll_usage_once()` enforces a subprocess timeout (default 30s) and returns a structured error if timeout occurs.
- [ ] Python scraper accepts `--poll_once` CLI flag to run one navigation + extraction then exit; any browser visibility is limited to the duration of that run (~5–10s typical).
- [ ] Visibility policy documented in `docs/JIRA/EPIC-07-TRAY.md` and `docs/JIRA/BEHAVIOR.md`: browser visible only during manual login and during brief poll windows; do not close other Chrome windows or interfere with user's primary browser.
- [ ] Tests or instructions provided for developers to simulate a force-refresh (`window.__TAURI__.invoke('poll_usage_once')`) and to observe the transient browser behavior.

## Dependencies
- EPIC-04 (Rust poller and commands)
- EPIC-02 (scraper CLI and single-run mode)
- EPIC-06 (resource resolution for invoking scraper)

## Tasks
- [ ] Add `--poll_once` handling to `scraper/claude_scraper.py` CLI that runs `navigate_to_usage_page()` -> `extract_usage_data()` -> print JSON -> exit (0.75h)
- [ ] Update Rust `spawn_scraper` invocation to accept `--poll_once` and a `timeout_secs` parameter (0.75h)
- [ ] Document visibility/window policy in `docs/JIRA/EPIC-07-TRAY.md` and `docs/JIRA/BEHAVIOR.md` (0.5h)
- [ ] Add a dev checklist in `docs/JIRA/EPIC-07-TRAY.md` describing how to manually test force-refresh via Tauri dev console (0.5h)

## Estimate
Total: 2.5 hours

## Research References
- Polling frequency and visibility rationale (Research.md lines 67-76, 85-90) [`docs/Research.md:67-76`, `docs/Research.md:85-90`]
- EPIC-LIST system tray and polling requirements (`docs/JIRA/EPIC-LIST.md:74-81`)

## Risks & Open Questions
- Risk: Frequent force-refreshes may trigger Cloudflare more often; UI should rate-limit repeated manual refreshes (consider debounce in frontend).
- Open question: Maximum allowed concurrent run attempts when user clicks Refresh rapidly — recommend single-run lock in backend.