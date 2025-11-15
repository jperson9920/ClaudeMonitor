# EPIC-09-STOR-03: Fix Chrome Session Creation Errors

## Description
Selenium fails with "session not created: cannot connect to chrome" when the scraper attempts to launch or connect to Chrome. This blocks scraping and leads to follow-on misleading errors in the UI.

## Root Cause (From logs)
- undetected_chromedriver cannot connect to a Chrome instance; logs show:
  - selenium.common.exceptions.SessionNotCreatedException: Message: session not created: cannot connect to chrome
- Potential causes:
  - Chrome/Chromium not installed or not in PATH
  - Version mismatch between ChromeDriver/undetected_chromedriver and installed Chrome
  - Port conflicts on 127.0.0.1 or inability to bind to the local loopback
  - Profile directory permission issues or corrupted chrome-profile
  - Sandbox/antivirus interfering with headless launches

## Acceptance Criteria
- Scraper can reliably create Chrome sessions and complete scraping tasks under normal conditions
- If Chrome is not installed, the UI shows "Chrome not found" with remediation steps
- Automatic ChromeDriver/undetected_chromedriver version detection and download if needed
- Robust retry logic for transient connection failures with exponential backoff (configurable retries)
- Clear, actionable log messages for failures and a troubleshooting guide entry
- Unit or integration tests that simulate session creation failures and verify retry + error reporting

## Tasks
- [ ] Add preflight checks for Chrome/Chromium presence and version detection
- [ ] Implement automatic download/installation of matching ChromeDriver/undetected_chromedriver where feasible
- [ ] Add retry logic around session creation:
  - Retry up to N times with exponential backoff
  - Detect transient errors vs deterministic failures
- [ ] Validate chrome-profile creation/permission handling; ensure profile dir is cleaned and recreated when corrupted
- [ ] Add explicit detection for port binding failures and attempt alternate ephemeral ports
- [ ] Harden environment cleanup steps (remove stale user-data-dir)
- [ ] Add instrumentation to capture Chrome/ChromeDriver versions in logs
- [ ] Update UI and troubleshooting docs with clear messages and next steps

## Priority
Critical (PRIORITY: CRITICAL BLOCKER)

## Validation Steps (QA)
1. On a healthy machine with Chrome installed: scraper should create a session and complete a sample scraping run.
2. On a machine without Chrome: UI must present "Chrome not found" with install suggestions.
3. Simulate version mismatch: verify automatic detection/download behavior or show clear guidance to the user.
4. Simulate transient connection failure: verify retry logic attempts reconnects and ultimately reports an accurate error if persistent.

## Implementation Notes
- Consider leveraging undetected_chromedriver's built-in version matching or bundling a small helper that auto-resolves versions.
- Use temporary, per-run user-data-dir directories and remove them on failure to avoid stale profiles.
- Log Chrome/ChromeDriver versions, environment PATH, and subprocess stderr for post-mortem (redact tokens/credentials).
- Keep retry counts conservative initially (e.g., 3 attempts with 500ms -> 2s backoff).

## Tasks Owner / Suggested Changes
- Backend: scraper integration (Python) and Rust IPC (scraper.rs)
- QA: create reproducible test harness for session failures

## Notes
- This is the highest priority blocking story in EPIC-09. Implement minimal reliable fixes first, then iterate for robustness.
- Document troubleshooting steps in docs/JIRA/troubleshooting-chrome.md (optional follow-up)