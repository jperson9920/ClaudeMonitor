# EPIC-TROUBLE-STOR-05: Remediation tasks for live-run failures

Parent: [EPIC-TROUBLE](./EPIC-TROUBLE.md)  
Priority: P0  
Status: TODO  
Owner: Engineering  
Estimate: 4–8 hours

Summary
- Actionable remediation tasks to fix immediate issues blocking live continuous usage.

Tasks
1. Validate and fix session-check logic
   - Description: Ensure the scraper does not assume a logged-in session when session artifacts are stale. Require visible browser for manual-login flow when session missing/invalid.
   - Acceptance criteria:
     - Unit/integration test that simulates missing/invalid session returns a "requires_manual_login" outcome and leaves the browser visible.
     - PR created with changes and code review comments addressed.
   - Effort: 1–2h

2. Disable or gate pre-create cleanup (P0 mitigation)
   - Description: Turn off aggressive profile cleanup or gate it behind a conservative check/config flag to avoid racing with Chrome startup.
   - Acceptance criteria:
     - Pre-create cleanup is disabled by default in dev or gated behind a config flag.
     - Single poll run after change demonstrates browser remains visible for manual login when session absent.
   - Effort: 0.5–1.5h

3. Fix percentage extraction heuristic
   - Description: Ensure width-to-percent conversion clamps at 100 and fallback to text-based extraction; add defensive parsing for malformed style strings.
   - Acceptance criteria:
     - Parser unit tests for style-width strings (e.g., "50%", "50px", "568px", "calc(50%)") pass.
     - Live-run against stored fixtures returns percent values in 0–100 range.
   - Effort: 1–2h

4. Add logging for early browser close decisions
   - Description: Record why the scraper decided to close the browser (session-check pass/fail and decision trace) to aid post-mortem.
   - Acceptance criteria:
     - scraper.log contains clear lines like: `session_check:passed|failed reason=...` and `browser_close:reason=...`.
     - Logs include timestamps and run IDs to correlate with terminal JSON artifacts.
   - Effort: 0.5–1h

5. Add short-run integration test and UI update validation
   - Description: Add an integration test that runs a single poll against a controlled fixture or browser and verifies the UI update path (usage-update event).
   - Acceptance criteria:
     - Test reproduces manual-login path and asserts the usage-update event is emitted to the Rust/Tauri backend.
     - Test artifacts saved to `artifacts/tests/epic-trouble-stor-05/`.
   - Effort: 1–2h

Acceptance criteria (story-level)
- Each remediation task has an owner, implementation branch, and test or documented manual verification steps.
- Re-run `python -m src.scraper.claude_scraper --poll_once` after fixes:
  - If not logged-in → browser remains open for manual login and session is saved on successful manual login.
  - If logged-in → scraper returns realistic percentages (0–100) and the UI receives a usage-update event.
- Tests or manual verification steps are documented and artifacts saved.

Implementation notes
- Use feature flags / config toggles for mitigations so behavior can be rolled back quickly.
- Reference parser helpers at `src/scraper/parsers.py` and session manager at `src/scraper/session_manager.py` for implementation.

Related
- Parent: [EPIC-TROUBLE](./EPIC-TROUBLE.md)
- Follow-up: [EPIC-TROUBLE-STOR-04](./EPIC-TROUBLE-STOR-04.md)

Links
- EPIC-TROUBLE-STOR-01 (investigation): [`docs/JIRA/EPIC-TROUBLE-STOR-01.md`](docs/JIRA/EPIC-TROUBLE-STOR-01.md)
- EPIC-TROUBLE-STOR-02 (mitigations): [`docs/JIRA/EPIC-TROUBLE-STOR-02.md`](docs/JIRA/EPIC-TROUBLE-STOR-02.md)