# EPIC-09-STOR-01: Fix Window Size on Launch

## Description
The application window opens much larger than the configured 450x650px. Users report the widget appears oversized on first launch and sometimes on subsequent launches.

## Root Cause (Hypothesis)
- Initial window size enforcement may be missing or executed after the window is shown.
- Settings persistence may be corrupted or not read on first-run causing fallback to default large size.
- Platform-specific DPI/scaling handling could be misinterpreting pixel dimensions.
- Tauri/webview or frontend code may be resizing the window on mount.

## Acceptance Criteria
- Window opens at exactly 450x650px on first launch (no visible resize flash)
- Window size is saved on close and restored on subsequent launches
- Settings.json contains the correct window width and height values after saving
- DPI/scaling aware on Windows (handles Display Scaling without oversizing)
- Unit or integration test(s) that validate window size initialization behavior

## Tasks
- [ ] Audit window creation code (frontend & src-tauri) to locate initial size logic
- [ ] Add enforced initial window size prior to showing the window
- [ ] Add or fix persistence logic to save window size into settings.json
- [ ] Add restore logic to read settings.json before window creation
- [ ] Add handling for Windows display scaling (verify 100%, 125%, 150% cases)
- [ ] Add automated test (or manual verification steps) for first-launch size
- [ ] Update docs/JIRA/EPIC-09-STOR-01.md with final verification results

## Priority
Critical (part of EPIC-09)

## Validation Steps (QA)
1. Remove settings.json (simulate first launch). Launch app: window must be 450x650px.
2. Resize window to 500x700px, close app. Reopen: window must restore to 500x700px.
3. Test on machine with display scaling ≠ 100% and verify logical size equals expected physical size.
4. Check settings.json for "window.width" and "window.height" keys and numeric values.

## Notes
- If platform APIs return logical vs physical pixels, document the conversion and store logical pixels consistently.
- Keep changes minimal and reversible to avoid regressions.