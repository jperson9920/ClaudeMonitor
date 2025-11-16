# EPIC-01-STOR-03

Title: Add scraper venv template, requirements, and sample run script

Epic: [`EPIC-01`](docs/JIRA/EPIC-LIST.md:14)

Status: TODO

## Description
As a developer, I need a reproducible Python environment and runnable sample script to validate the scraper dependencies (undetected-chromedriver, selenium) and the manual login flow described in Research.md.

## Acceptance Criteria
- [ ] `scraper/requirements.txt` includes `undetected-chromedriver>=3.5` and `selenium`.
- [ ] `scraper/setup.sh` and `scraper/setup.ps1` create/activate venv and install requirements. Example commands are present in the scripts.
- [ ] `scraper/run_manual_login.sh` and `scraper/run_manual_login.ps1` execute `python claude_scraper.py --login` and print clear instructions about manual interaction and that Chrome windows must not be closed.
- [ ] `docs/README-SETUP.md` references these scripts and Chrome requirement (Research.md lines 174-179) [`docs/Research.md:174-179`].

## Dependencies
- EPIC-01-STOR-01

## Tasks
- [ ] Create `scraper/requirements.txt` with `undetected-chromedriver>=3.5` and `selenium`. (0.25h)
- [ ] Create `scraper/setup.sh` (Unix) with example content:
  - `python3 -m venv scraper-env && source scraper-env/bin/activate && pip install -r requirements.txt`
- [ ] Create `scraper/setup.ps1` (Windows PowerShell) with example content:
  - `python -m venv scraper-env; .\scraper-env\Scripts\Activate.ps1; pip install -r requirements.txt`
- [ ] Create `scraper/run_manual_login.sh` and `scraper/run_manual_login.ps1` which run:
  - `python claude_scraper.py --login`
  - and print the manual-login checklist (open browser, complete CAPTCHA/2FA, press Enter in terminal).
- [ ] Add `scraper/README.md` describing expected log files (`scraper/scraper.log`), session file location (`scraper/chrome-profile/session.json`), and the no-Chrome-window-closing constraint. (0.5h)

## Estimate
Total: 2 hours
- requirements: 0.25h
- scripts: 0.75h
- README & QA: 1.0h

## Research References
- Research.md lines 198-201 (pip install undetected-chromedriver selenium) [`docs/Research.md:198-201`]
- Research.md lines 174-179 (Chrome requirement and notes) [`docs/Research.md:174-179`]
- EPIC-LIST.md line 124 (do not close Chrome windows) [`docs/JIRA/EPIC-LIST.md:124`]

## Risks & Open Questions
- Risk: undetected-chromedriver may auto-download drivers; corporate networks may block downloads — document offline driver fallback.
- Open question: Place venv at project root (`scraper-env`) or inside `scraper/`? Recommend root per Research.md examples (lines 195-197).
- Scripts must explicitly warn operators not to perform authentication actions automatically; manual login only.