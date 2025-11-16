# EPIC-05 Frontend Integration Notes

Purpose:
- Describe Tauri command signatures, event payload schemas, example frontend usage, and a manual test checklist for the React frontend integration.

## Tauri Commands (from Rust backend)
- invoke('poll_usage_once') -> returns UsagePayload
- invoke('manual_login') -> returns { status: "ok", message: string }
- invoke('check_session') -> returns { status: "ok" | "invalid", ... }
- invoke('start_polling', { interval_secs: number }) -> returns {}
- invoke('stop_polling') -> returns {}

Example:
```typescript
// TypeScript example
const payload = await window.__TAURI.invoke('poll_usage_once') as UsagePayload;
```

## Tauri Events
- usage-update
  - Emitted on successful scrape/update.
  - Payload: UsagePayload (see schema below)
- usage-error
  - Emitted on error.
  - Payload: { error_code: string, message: string, diagnostics?: any }

Frontend listen example:
```typescript
// listen for events
const unlisten = await window.__TAURI.event.listen('usage-update', (evt) => {
  const payload = evt.payload as UsagePayload;
  // update UI
});
```

## Expected UsagePayload schema (from scraper)
- status: 'ok' | 'partial' | 'error'
- components: Array of component objects
- found_components: number
- diagnostics?: any
- scraped_at?: string

Component object:
- id: string (e.g. "current_session")
- name: string (label)
- usage_percent: number (0-100)
- tokens_used?: number | null
- tokens_limit?: number | null
- reset_time?: string | null (ISO8601)
- raw_reset_text?: string | null
- last_updated: string (ISO8601)
- status: 'ok'|'partial'|'error'

Example:
```json
{
  "status": "ok",
  "components": [
    {
      "id": "current_session",
      "name": "Current session",
      "usage_percent": 3,
      "tokens_used": null,
      "tokens_limit": null,
      "reset_time": "2025-11-16T09:28:00Z",
      "raw_reset_text": "Resets in 4 hr 16 min",
      "last_updated": "2025-11-16T05:12:00Z",
      "status": "ok"
    }
  ],
  "found_components": 3,
  "scraped_at": "2025-11-16T05:12:00Z"
}
```

## Frontend integration notes
- Hook: `src/hooks/useUsage.ts` provides:
  - payload: UsagePayload | null
  - loading: boolean
  - error: Error | null (may include .diagnostics)
  - refresh(): Promise<void>
  - login(): Promise<void>
  - startPolling(intervalSecs?: number): Promise<void>
  - stopPolling(): Promise<void>

- Component: `src/components/UsageDisplay.tsx`
  - Props: payload, loading, error, onRefresh, onLogin
  - Renders up to three component rows with:
    - ProgressBar (aria attrs)
    - Percentage label
    - ResetTimer (ISO -> relative countdown; fallback to raw text)
    - Last updated time

- Accessibility:
  - Progress elements include: role="progressbar", aria-valuenow, aria-valuemin="0", aria-valuemax="100"
  - ResetTimer uses aria-live="polite" for updates
  - Buttons have descriptive aria-label attributes

## Manual test checklist
1. Start app: `npm run tauri dev` (or platform-specific dev command).
2. Confirm initial UI loads and shows "No usage data available" if backend hasn't emitted yet.
3. Click "Refresh" button:
   - Frontend calls `poll_usage_once`.
   - UI shows loading state "Refreshing…" on the button.
   - On success, UI receives `usage-update` payload and updates rows.
4. Click "Login" button:
   - Frontend calls `manual_login`.
   - Backend opens login flow; UI should show loading while the command executes.
5. Verify events:
   - When backend emits `usage-update`, frontend updates automatically.
   - When backend emits `usage-error`, frontend shows an alert with message and "Details" (diagnostics).
6. Start/Stop polling:
   - Click "Start Polling" in header to issue `start_polling` (300s default).
   - Click "Stop Polling" to stop background polling.
7. Accessibility checks:
   - Verify progress bars expose aria attributes to screen readers.
   - Verify ResetTimer announcements are announced (aria-live).
8. Edge cases:
   - If `reset_time` is not parseable, UI shows `raw_reset_text`.
   - If fewer than 3 components are returned, UI shows only those present.

## Dev notes
- Files created/modified during EPIC:
  - src/types/usage.ts
  - src/components/ProgressBar.tsx
  - src/components/ResetTimer.tsx
  - src/components/UsageDisplay.tsx
  - src/hooks/useUsage.ts
  - src/App.tsx
  - src/main.ts (renders React App)
- Unit tests should be added under `src/components/__tests__/` for ProgressBar, ResetTimer, UsageDisplay using React Testing Library / Jest.

## Troubleshooting
- If `window.__TAURI` is undefined during web dev (non-Tauri environment), mock the API in tests or use feature guards.
- If events do not arrive, confirm Rust backend is emitting `usage-update` and `usage-error` via Tauri event API.
