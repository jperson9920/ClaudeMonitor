# EPIC-09-STOR-02: Fix Misleading Python Error Message

## Description
After successful login the app displays:  
❌ Error: Python is not installed or not found. Please install Python 3.9+ and try again.  
However, terminal logs indicate selenium errors (Chrome session creation failures). The displayed message misleads users and hides the real failure modes.

## Root Cause
- Error handling in scraper integration (likely in scraper.rs or the Python wrapper) conflates any subprocess failure (including Chrome connection errors) with "Python not installed".
- Generic catch-all error mapping causes the UI to display incorrect guidance.

## Acceptance Criteria
- Errors are classified clearly:
  - "Python interpreter not found" when the interpreter is missing
  - "Chrome connection failed" (or similar) when Selenium/ChromeDriver cannot create a session
  - "Scraper runtime error" for other runtime exceptions with the underlying message included
- UI displays actionable, specific messages with links or guidance (e.g., check Chrome installation, ensure ChromeDriver version matches)
- Logging includes structured error codes to allow telemetry/diagnostics
- Tests for error classification and message mapping

## Tasks
- [ ] Inspect scraper integration points: scraper.rs, Python wrapper script, and the Rust->Python IPC
- [ ] Improve detection for Python interpreter absence vs Python runtime error:
  - Check interpreter presence before attempting to run scripts
  - Catch subprocess exit codes and stderr content
- [ ] Map known Selenium/undetected_chromedriver errors to specific error types (e.g., SessionNotCreatedException -> CHROME_CONNECTION_FAILED)
- [ ] Update UI to render specific error messages and suggested remediation
- [ ] Add logging that captures the original exception stack/message (redact sensitive data)
- [ ] Add unit/integration tests for error mapping logic
- [ ] Update docs/JIRA/ with reproduction steps and final verification

## Priority
Critical (part of EPIC-09)

## Validation Steps (QA)
1. Uninstall or temporarily rename Python executable and run the app: UI must show "Python interpreter not found" with install instructions.
2. Simulate Chrome connection failure (e.g., block Chrome or start incompatible ChromeDriver). UI must show "Chrome connection failed" with guidance.
3. Verify logs contain the underlying exception text and a structured error code for later triage.

## Notes
- Avoid leaking full stack traces to end users; use logs for developers and concise, actionable messages for users.
- Provide links to a troubleshooting doc describing common fixes (install Chrome, update ChromeDriver, ensure no port conflicts).