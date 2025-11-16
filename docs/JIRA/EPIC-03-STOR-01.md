# EPIC-03-STOR-01

Title: Implement session manager: save/load session and profile directory

Epic: [`EPIC-03`](docs/JIRA/EPIC-LIST.md:34)

Status: TODO

## Description
As a developer, I need a deterministic session manager that saves browser cookies and metadata to disk, validates session age, and exposes programmatic checks so the Rust backend can decide whether to trigger manual login. This implements persistent profile storage under `scraper/chrome-profile/` and functions used by the scraper and Rust integrations.

User story: "As a user I want a one-time manual login and automatic reuse of saved session so I don't need to re-authenticate every poll."

## Acceptance Criteria
- [ ] `scraper/session_manager.py` exists and exports:
  - `save_session(driver, session_file: str = './chrome-profile/session.json') -> None`
  - `load_session(session_file: str = './chrome-profile/session.json') -> dict | None`
  - `is_session_expired(session_data: dict, max_age_days: int = 7) -> bool`
- [ ] Saved session includes `cookies`, `timestamp` (epoch seconds), `user_agent` and `profile_path`.
- [ ] `load_session()` validates timestamp and returns None for expired/invalid sessions; default expiry 7 days (configurable). (See Research.md lines 389-395)
- [ ] `scraper/claude_scraper.py` calls `load_session()` at startup and falls back to `manual_login()` when load returns None.
- [ ] Unit tests under `scraper/tests/test_session_manager.py` covering save/load/expiry behavior.

## Dependencies
- EPIC-02-STOR-01 (scraper driver methods)
- EPIC-01 (scraper directory present)
- Research.md lines on session persistence and 7-day expiry (`docs/Research.md:91-96`, `docs/Research.md:389-396`)

## Tasks (1-3 hours each)
- [ ] Create `scraper/session_manager.py` and implement `save_session`, `load_session`, and `is_session_expired` (2.0h)
  - Use `json` and `pathlib.Path`; ensure atomic write (write to `.tmp` then rename).
  - Example signature:
    - def save_session(driver, session_file: str = './chrome-profile/session.json') -> None
    - def load_session(session_file: str = './chrome-profile/session.json') -> Optional[dict]
    - def is_session_expired(session_data: dict, max_age_days: int = 7) -> bool
- [ ] Update `scraper/claude_scraper.py` to import and call `session_manager.load_session()` on startup and `session_manager.save_session()` after manual login (0.75h)
  - Add code: `from scraper.session_manager import load_session, save_session`
- [ ] Create tests: `scraper/tests/test_session_manager.py` using temporary filesystem (pytest tmp_path) asserting expiry logic (1.0h)
- [ ] Document file paths and behavior in `scraper/README.md` (0.5h)

## Estimate
Total: 4.25 hours

## Research References
- Session persistence rationale and 7-day expiry: Research.md lines 91-96, 389-396 [`docs/Research.md:91-96`, `docs/Research.md:389-396`]
- File layout guidance: Research.md lines 202-211 [`docs/Research.md:202-211`]
- EPIC-LIST session requirements: `docs/JIRA/EPIC-LIST.md:34-42`

## Risks & Open Questions
- Risk: Different OS paths or permission issues when writing profile directory; ensure owner-only permissions on session file and document secure storage in EPIC-10.
- Open question: Should session encryption be applied at rest (decision deferred to EPIC-10).