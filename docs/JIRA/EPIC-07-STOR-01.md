# EPIC-07-STOR-01

Title: Implement system tray menu and basic UI actions

Epic: [`EPIC-07`](docs/JIRA/EPIC-LIST.md:74)

Status: TODO

## Description
As a user I need a system tray menu to control the widget without the main window. The tray must provide Show Dashboard, Refresh Now, and Quit actions and wire these to Rust backend commands so users can quickly force-refresh or open the UI.

This story implements Tauri system tray integration and wires tray menu items to Rust commands already defined in EPIC-04.

## Acceptance Criteria
- [ ] System tray menu created using Tauri plugin with menu items: "Show Dashboard", "Refresh Now", "Quit".
- [ ] "Refresh Now" invokes `poll_usage_once()` command and shows a transient notification on success/failure.
- [ ] "Show Dashboard" brings the main window to front (Tauri `app.get_window("main").show()`).
- [ ] "Quit" gracefully stops polling (if running) and exits the application.
- [ ] Tray-related commands and event handlers are documented in `src-tauri/src/tray.rs` and `docs/JIRA/EPIC-07-TRAY.md`.

## Dependencies
- EPIC-04 (Rust backend commands: poll_usage_once, stop_polling)
- EPIC-05 (frontend should react to Show Dashboard)

## Tasks (1-2 hours each)
- [ ] Add `src-tauri/src/tray.rs` implementing tray setup using `tauri::SystemTray` and menu creation. Include handler that maps menu item ids to actions:
  - `show_dashboard` -> bring window to front
  - `refresh_now` -> call `spawn_scraper`/`poll_usage_once`
  - `quit` -> call `stop_polling` and exit app (1.5h)
- [ ] Wire tray initialization into `main.rs` with `tauri::Builder::system_tray()` and event listener to handle `tauri::SystemTrayEvent::MenuItemClick` (0.75h)
- [ ] Implement transient notification display (use Tauri notification or emit frontend event `usage-notification`) on refresh result (0.5h)
- [ ] Add `docs/JIRA/EPIC-07-TRAY.md` documenting menu labels, expected behavior, and how to test the tray actions (`cd src-tauri && cargo run`) (0.5h)

## Estimate
Total: 3.25 hours

## Research References
- EPIC-LIST system tray and background polling requirements: `docs/JIRA/EPIC-LIST.md:74-82`
- Tauri system tray capability reference: Research.md lines about Tauri and system tray (see `docs/Research.md:101-106`)

## Risks & Open Questions
- Risk: On some platforms (Linux with certain DEs), system tray behavior differs; document platform differences and test on Windows/macOS/Linux.
- Open question: Should the tray show last-known usage metrics in a submenu or tooltip? Defer to UX; can be added in follow-up story.