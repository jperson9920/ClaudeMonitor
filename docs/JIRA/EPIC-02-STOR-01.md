# EPIC-02-STOR-01

Title: Implement ClaudeUsageScraper core and driver lifecycle

Epic: [`EPIC-02`](docs/JIRA/EPIC-LIST.md:24)

Status: TODO

## Description
As a developer, I need a tested implementation of the core scraper lifecycle so the system can create a headed Chrome driver, preserve a persistent profile, and navigate to the usage page reliably.

This story implements `scraper/claude_scraper.py` methods:
- `create_driver(profile_dir: str = './chrome-profile') -> WebDriver`
- `manual_login(self) -> bool`
- `load_session(self) -> bool`
- `navigate_to_usage_page(self) -> bool`
and wiring for driver initialization and teardown.

Context: See Research.md discussion of headed mode, use_subprocess and persistent profile (Research.md lines 287-296, 288-295, 86-94).

## Acceptance Criteria
- [ ] `scraper/claude_scraper.py` contains a `ClaudeUsageScraper` class with methods:
  - `create_driver(profile_dir: str = './chrome-profile')`
  - `manual_login(self) -> bool`
  - `load_session(self) -> bool`
  - `navigate_to_usage_page(self) -> bool`
- [ ] `create_driver` sets `headless=False`, `use_subprocess=True`, adds `--user-data-dir` and `--profile-directory=Default`, and configures realistic window size and anti-detection flags. (Verify options and comments)
- [ ] `manual_login` opens `https://claude.ai`, prints interaction instructions to stderr, waits for Enter, and saves session via `save_session()` on success.
- [ ] `load_session` checks `scraper/chrome-profile/session.json` exists and validates age (default 7 days), returning True only for valid sessions.
- [ ] Unit-testable helper functions exist with signatures: `save_session(self)`, `check_session_valid(self)`, and use logging to `scraper/scraper.log`.

## Dependencies
- EPIC-01 (project scaffold and `scraper/` directory)
- Research.md: headed mode & undetected-chromedriver usage (lines 85-96, 287-296) [`docs/Research.md:85-96`]

## Tasks (1-4 hours each)
- [ ] Add/modify file: `scraper/claude_scraper.py` — implement class skeleton and imports (file path: `scraper/claude_scraper.py`) (1.5h)
  - Required imports: `undetected_chromedriver as uc`, `selenium.webdriver.common.by.By`, `WebDriverWait`, `expected_conditions as EC`, `logging`, `json`, `time`, `Path`
  - Function signatures must match acceptance criteria.
- [ ] Implement `create_driver` body with options and try/except logging and return driver (2.0h)
  - Include options: `--user-data-dir={profile_dir}`, `--profile-directory=Default`, `--disable-blink-features=AutomationControlled`, `--window-size=1920,1080`
  - Ensure `headless=False` and `use_subprocess=True`
- [ ] Implement `manual_login` that instructs user via stderr and calls `save_session()` (1.0h)
  - Print instructions exactly as documented in Research.md (lines 329-338)
- [ ] Implement `load_session` to validate session file timestamp and return boolean (1.0h)
- [ ] Add logging to `scraper/scraper.log` and ensure errors go to stderr (0.5h)

## Estimate
Total: 6 hours
- Skeleton & imports: 1.5h
- create_driver implementation: 2.0h
- manual_login: 1.0h
- load_session + logging: 1.5h

## Research References
- Headed mode rationale and settings: Research.md lines 85-90, 287-296 [`docs/Research.md:85-90`, `docs/Research.md:287-296`]
- Session persistence expectation (7 days): Research.md lines 91-96, 389-395 [`docs/Research.md:91-96`, `docs/Research.md:389-395`]
- File layout guidance: Research.md lines 202-211 (scraper folder layout) [`docs/Research.md:202-211`]

## Risks & Open Questions
- Risk: undetected-chromedriver auto-download may fail on restricted networks; document offline driver fallback in EPIC-01.
- Open question: Should `profile_dir` be shared across OS users or per-OS path normalization required? Document in session manager story.