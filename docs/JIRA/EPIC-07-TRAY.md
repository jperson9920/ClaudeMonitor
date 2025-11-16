# EPIC-07 — System Tray & Force-Refresh (TRAY doc)

This document describes the system tray behavior, developer testing checklist, and examples for invoking tray-related behavior.

Tray menu
- Show Dashboard — brings the main window to the front (Tauri: app.get_window("main").show()).
- Refresh Now — triggers a single-run poll. This calls the Rust scraper bridge which runs the Python scraper with `--poll_once` and emits `usage-update` or `usage-error` events. Also emits `usage-notification` for transient UX notifications.
- Quit — stops background polling (best-effort) and exits the app.

Visibility / timed runs
- Automated and forced polls run the scraper in single-run mode (`--poll_once`) and are expected to have a short visibility window for the headed browser (approx. 5–10s typical). The headed browser is used only for:
  - Manual login flows (`--login`) where the user interacts with the opened browser.
  - Brief automation during poll runs to allow Cloudflare challenge resolution.
- The scraper is invoked with a 30s timeout for the subprocess; if it fails to produce output within that time the Rust backend returns a timeout error (ScraperError::Timeout).

Developer testing checklist
1. Build & run Tauri app:
   - cd src-tauri && cargo run
2. Verify tray appears and menu items are present.
3. Force-refresh from tray:
   - Click "Refresh Now" and observe:
     - Frontend receives `usage-update` on success (payload is JSON).
     - Frontend receives `usage-error` and `usage-notification` on failure.
4. Force-refresh via Dev Console:
   - In the frontend dev console run:
     window.__TAURI__.invoke('poll_usage_once').then(console.log).catch(console.error)
5. Show Dashboard:
   - Click "Show Dashboard" — main window should appear and receive focus.
6. Quit:
   - Click "Quit" — app should stop polling and exit.

How the tray maps to backend
- Tray handler implemented in: src-tauri/src/tray.rs
  - `create_system_tray()` -> constructs menu with ids: `show_dashboard`, `refresh_now`, `quit`.
  - `handle_tray_event()` -> maps ids to actions which emit events or call scraper/poller APIs.
- Polling and scraper invocation:
  - `refresh_now` calls `crate::scraper::spawn_scraper(vec!["--poll_once"], 30).await`
  - On success emits `usage-update` and `usage-notification` events.
  - On error emits `usage-error` and `usage-notification` events.

Notes & caveats
- Rate-limit manual refreshes in the frontend if desired; rapid repeated refreshes can trigger Cloudflare.
- Platform variations (Linux DEs) may change tray availability/behavior; test on target platforms.
- The tray handler uses the same scraper invocation path as Tauri commands for consistent behavior.