# EPIC-05-STOR-03

Title: Wire frontend to Rust backend commands and system tray events

Epic: [`EPIC-05`](docs/JIRA/EPIC-LIST.md:54)

Status: TODO

## Description
As a frontend developer I need the React UI wired to the Rust backend commands and system tray events so users can trigger manual refresh, manual login, start/stop polling, and receive `usage-update` and `usage-error` events from the backend.

This story implements the integration points in:
- `src/App.tsx` (or `src/hooks/useUsage.ts`)
- `src/components/UsageDisplay.tsx` event handlers
- Documentation/examples in `docs/JIRA/EPIC-05-FRONTEND.md`

## Acceptance Criteria
- [ ] Frontend invokes backend commands via Tauri:
  - `invoke('poll_usage_once')` to force-refresh
  - `invoke('manual_login')` to open manual login flow
  - `invoke('start_polling', { interval_secs })` and `invoke('stop_polling')`
  Example invocation documented in `docs/JIRA/EPIC-05-FRONTEND.md` with code sample.
- [ ] Frontend subscribes to Tauri events `usage-update` and `usage-error` and updates UI state accordingly.
- [ ] Manual refresh button in `UsageDisplay` calls `onRefresh()` which invokes `poll_usage_once` and shows loading state for the duration of the call (~5-10s).
- [ ] Errors returned by backend are surfaced to the UI with user-friendly messages and a "Details" button that shows diagnostics (from `diagnostics` field).
- [ ] All file paths and function calls are present in the story and documented so a developer with zero context can implement them.

## Dependencies
- EPIC-04 (backend commands implemented)
- EPIC-05-STOR-01 (UsageDisplay component)
- EPIC-05-STOR-02 (ProgressBar/ResetTimer components)
- Research.md lines on IPC and events (`docs/Research.md:42-44`, `docs/Research.md:69-74`)

## Tasks (each 1-3 hours)
- [ ] Add `src/hooks/useUsage.ts`:
  - Exported hooks:
    - `useUsage()` returns `{ payload: UsagePayload | null, loading: boolean, error: Error | null, refresh: () => Promise<void>, login: () => Promise<void> }`
  - Implementation uses `window.__TAURI__.invoke` and `window.__TAURI__.event.listen` to subscribe to `usage-update`/`usage-error`. (1.5h)
  - Example: `await window.__TAURI__.invoke('poll_usage_once')`
- [ ] Update `src/App.tsx` to initialize listener on mount and pass `payload` to `UsageDisplay` (1.0h)
  - Ensure unsubscribe on unmount: `unlisten()` pattern
- [ ] Update `src/components/UsageDisplay.tsx`:
  - Implement `onRefresh` to call `useUsage().refresh()`
  - Implement `onLogin` to call `useUsage().login()`
  - Show loading indicator while refresh is in progress and show error toast when `error` is set (1.0h)
- [ ] Document exact Tauri invocation signatures and expected return payloads in `docs/JIRA/EPIC-05-FRONTEND.md` with examples and expected JSON schema references to `scraper/protocol.md` (0.5h)
- [ ] Add end-to-end manual test checklist in `docs/JIRA/EPIC-05-FRONTEND.md`:
  - Start app (`npm run tauri dev`), confirm `usage-update` events received every 300s, click Refresh, click Login, and verify UI updates. (0.25h)

## Estimate
Total: 4.25 hours

## Research References
- Tauri event & IPC usage and JSON flow: Research.md lines 42-44, 69-74 [`docs/Research.md:42-44`, `docs/Research.md:69-74`]
- EPIC-LIST frontend/backend wiring expectations: `docs/JIRA/EPIC-LIST.md:56-61`

## Risks & Open Questions
- Risk: UI calling `manual_login` will open a browser window and require user interaction; ensure UI warns the user not to close the browser window used by the scraper (EPIC-01/EPIC-03 notes).
- Open question: Should frontend retry failed `poll_usage_once` calls automatically or surface to user first? Defer policy to EPIC-08 retry rules.