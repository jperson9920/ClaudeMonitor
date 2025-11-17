# EPIC-TROUBLE-STOR-04: Live run — browser not shown, session closed early, erroneous scrape results

Parent: [EPIC-TROUBLE](./EPIC-TROUBLE.md)  
Priority: P0  
Status: IN_PROGRESS  
Owner: TBD (assign to Engineering / QA)

Summary
- Document a live-run where the Chrome browser never stayed open for manual login, the scraper exited early, returned erroneous percentage values (568%) without a login, and the UI did not display updated percentages.

Reproduction steps (exact commands run)
1. Start the frontend / Tauri dev server (observed running; no visible Chrome window opened):
   - npm run tauri dev
2. Run a single scraper poll and capture stdout JSON:
   - python -m src.scraper.claude_scraper --poll_once

Observed behavior
- Tauri dev server reported running, but no Chrome window remained visible for manual login.
- The scraper process exited with code 0 after producing JSON output containing highly implausible percentage values (e.g. 568%).
- UI did not receive usage-update events; dashboard remained at previous values.

Terminal JSON excerpt (captured stdout from python run)
- Run timestamp (UTC): 2025-11-17T20:14:56.516Z
- Exit code: 0

Example JSON excerpt (sanitized):
{
  "timestamp": "2025-11-17T20:14:56.516Z",
  "status": "success",
  "found_components": 3,
  "usage": {
    "total_percent": 568.0,
    "today_percent": 568.0,
    "hour_percent": 568.0
  },
  "notes": "extraction-from-style_width_progress"
}

Notes:
- The JSON shows identical 568% values across components, which are outside valid range (0–100) and indicate extraction/parsing error.
- Scraper process returned code 0 despite producing erroneous values.

Logs / artifacts to gather
- Integrated terminal output for `npm run tauri dev` (full stdout/stderr)
- Terminal output from `python -m src.scraper.claude_scraper --poll_once` (full stdout/stderr)
- scraper/scraper.log (rotated logs if present)
- scraper/chrome-profile/ directory listing, file timestamps and sizes (to verify profile creation/cleanup)
- docs/tauri-dev.log (if relevant / available)
- Last poll JSON (e.g., artifacts/last_scraper_poll.json or similar)
- Any supervisor/poller logs that indicate subprocess lifecycle events

Root-cause hypotheses
1. False-positive session check allowed the scraper to assume a logged-in session and close the browser early
   - The session-validation routine may have returned true on stale or partial artifacts (cookies/session file present but invalid).
2. pre-create or post-quit cleanup raced with Chrome startup and removed/locked profile resources
   - The cleanup routine may kill processes or remove lockfiles while Chrome is starting, leading to failed profile restore and unexpected browser closures.
3. Selector heuristic `style_width_progress` mis-parsed an inline style width and produced a numeric parse that was not clamped → produced 568% (style parsing bug)
   - Width string like "568.0px" or malformed "568%" parsing path or missed unit handling produced an unbounded numeric result.
4. UI update event (usage-update) failed to emit or was dropped due to IPC issue, so frontend never showed updated values even when scraper returned data.

Artifacts/evidence required to validate hypotheses
- scraper.log entries around session-check decision points (time-aligned with run timestamp)
- Any "browser closed" or "session_saved" log lines
- Timestamps showing profile directory writes vs scraper start/stop
- Full stdout JSON for the poll run (above excerpt)
- Any exception traces or warnings in tauri dev server logs indicating IPC emit failures

Artifacts
- artifacts/tests/EPIC-TROUBLE-STOR-04/scraper-log.txt — excerpt (first ~5000 chars) copied from `scraper/scraper.log`; contains error traces showing Chrome/undetected-chromedriver failures and SessionNotCreatedException.
- artifacts/tests/EPIC-TROUBLE-STOR-04/tauri-dev-log.txt — copy of `docs/tauri-dev.log` capturing the Tauri dev server stdout/stderr during the run.
- artifacts/tests/EPIC-TROUBLE-STOR-04/poll_once-output.json — captured stdout JSON from `python -m src.scraper.claude_scraper --poll_once`. Recorded poll timestamp: 2025-11-17T20:14:56.516Z.
- artifacts/tests/EPIC-TROUBLE-STOR-04/chrome-profile-listing.txt — recursive listing of `scraper/chrome-profile/` (dir /s output truncated for brevity).
- artifacts/tests/EPIC-TROUBLE-STOR-04/terminal-timestamp.txt — run timestamp file:
  - UTC: 2025-11-17T20:04:22.666176Z
  - Local (America/Los_Angeles): 2025-11-17T20:04:22

Notes
- Sensitive session files (cookies/session.json) are intentionally NOT attached. If sanitized session artifacts are required, create a sanitized copy and record its path.
- If any artifact exceeded size limits it was truncated to the first 10000 bytes and a truncation note was added to the artifact file.

Suggested next technical tasks (see EPIC-TROUBLE-STOR-05 for remediation task list)
- Add diagnostic logs around session-check decision points (why browser was closed)
- Add defensive clamping and fallback parsing in percentage extraction
- Temporarily disable pre-create cleanup or gate it behind a conservative check and re-run single poll
- Add short integration test recreating the manual-login path and verifying UI update

Acceptance criteria
- Repro steps documented and reproducible locally by Engineering/QA
- Required logs/artifacts (listed above) are attached to this story or available in artifacts/
- Root-cause hypotheses enumerated and linked to evidence when available
- Suggested next technical tasks listed and cross-referenced to EPIC-TROUBLE-STOR-05

References
- Related stories:
  - [EPIC-TROUBLE-STOR-01](./EPIC-TROUBLE-STOR-01.md)
  - [EPIC-TROUBLE-STOR-02](./EPIC-TROUBLE-STOR-02.md)
  - EPIC-TROUBLE parent: [EPIC-TROUBLE](./EPIC-TROUBLE.md)