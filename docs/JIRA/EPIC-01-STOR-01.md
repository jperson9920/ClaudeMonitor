# EPIC-01-STOR-01

Title: Initialize repository, toolchain docs and Tauri scaffold

Epic: [`EPIC-01`](docs/JIRA/EPIC-LIST.md:14)

Status: DONE

## Description
As a developer, I need a reproducible project skeleton and clear environment setup so I can build and run the Tauri desktop widget and Python scraper locally without onboarding friction.

This story creates the initial project scaffold, documents required toolchain versions, and provides step-by-step setup instructions for Node, Rust, and Python venv. Context and rationale come from the Research guide which mandates Tauri + Rust backend and Python 3.9+ for the scraper (see Research.md).

## Acceptance Criteria
- [x] Repository contains an initialized Tauri scaffold with top-level directories: `src-tauri/`, `src/` and `scraper/` (as a minimal scaffold) and `scraper-env/` venv placeholder. (Verify file tree)
- [x] `docs/README-SETUP.md` or `README.md` includes explicit installation steps for Node 18+, Rust 1.70+, Python 3.9+ and Chrome. Refer to Research.md lines 121-126 and 157-166 for exact versions. (Verify docs file)
- [x] `scraper/requirements.txt` added with `undetected-chromedriver` and `selenium` and `scraper/claude_scraper.py` placeholder file exists with header docstring. (Verify files & content)
- [x] A short local CI checklist is added to `docs/JIRA/EPIC-LIST.md` or `README.md` describing manual validation steps (create venv, install, run scraper in --login) referencing Research.md lines 181-201. (Verify checklist)

## Dependencies
- None (first story of EPIC-01)
- External: Node.js 18+, Rust 1.70+, Python 3.9+, Chrome/Chromium (Research.md references lines 121-126, 157-166, 174-179)

## Tasks (each task ~1-3 hours)
- [x] Create directories and minimal files:
  - Create `src-tauri/`, `src/`, `scraper/`
  - Files: `scraper/claude_scraper.py` (header only), `scraper/requirements.txt`
  - Command: `mkdir src-tauri src scraper && echo "# scraper requirements" > scraper/requirements.txt`
- [x] Add setup instructions:
  - File: `docs/README-SETUP.md` or top-level `README.md`
  - Content: exact commands from Research.md for Node/Rust/Python (see references below)
  - Example commands to include (copy verbatim):
    - `npm create tauri-app@latest`
    - `python3 -m venv scraper-env` (Windows: `scraper-env\Scripts\activate`)
- [x] Commit files (dry-run guidance only; DO NOT run git commands here). Add instructions for RooWrapper git helper DryRun workflow in `docs/JIRA/README-GIT-WORKFLOW.md`.
- [x] Add lint/checklist to `docs/JIRA/EPIC-LIST.md` under EPIC-01 referencing version checks.

## Estimate
Total: 4 hours
- Directory & scaffold creation: 1h
- Writing setup docs and commands: 2h
- QA review and checklist: 1h

## Research References
- Research.md lines 121-126 (Node, Rust, Python versions) [`docs/Research.md:121`]
- Research.md lines 181-201 (project initialization + venv & dependencies) [`docs/Research.md:181-201`]
- EPIC-LIST.md lines 14-22 (EPIC-01 goal & acceptance criteria) [`docs/JIRA/EPIC-LIST.md:14-22`]

## Phase 2: DOM Selector Extraction

### Phase 2A: Automated Puppeteer Inspection (FAILED)
**Date:** 2025-11-15
**Approach:** Attempted automated puppeteer navigation to `https://claude.ai/settings/usage`
**Result:** BLOCKED by Cloudflare challenge
**Details:**
- Cloudflare Ray ID: `99f3b35e1d6a9450`
- Error: "Checking if the site connection is secure" challenge page
- Root cause: Cloudflare bot detection blocks headless/automated browsers

### Phase 2B: Manual DOM Inspection (COMPLETED)
**Date:** 2025-11-16
**Approach:** User provided HTML sample and manual browser inspection results
**Status:** COMPLETED - User provided HTML sample (2025-11-16)

**Outcome:**
- Manual inspection results captured in [`docs/manual-inspection-results.md`](docs/manual-inspection-results.md:1)

**Decision:**
- Sufficient HTML provided; detailed selector extraction and validation deferred to [`EPIC-02-STOR-01`](docs/JIRA/EPIC-02-STOR-01.md:1) (scraper implementation)

**Rationale:**
- HTML structure analysis confirms the 3 usage components are present (Current session, Weekly all models, Weekly Opus). Precise CSS selectors and runtime validation will be performed during scraper implementation using `undetected-chromedriver` in headed mode with a persistent profile.

**Created artifacts:**
- [`docs/manual-inspection-results.md`](docs/manual-inspection-results.md:1) - User-provided HTML sample and inspector notes
- [`docs/DOM-INSPECTION-GUIDE.md`](docs/DOM-INSPECTION-GUIDE.md:1) - Manual inspection instructions (reference)
- [`docs/selectors-template.yaml`](docs/selectors-template.yaml:1) - Template remains available if needed

## Risks & Open Questions
- Risk: Developers may have different system package managers; docs must include both macOS/Linux/Windows variants (Research.md provides examples lines 139-156).

### Resolved / Recorded Decisions
- **Question:** Toolchain config files (.nvmrc, rust-toolchain)?
  - **Decision:** DEFERRED to [`EPIC-01-STOR-02`](docs/JIRA/EPIC-01-STOR-02.md:1)
  - **Rationale:** Basic project setup is complete; toolchain pinning is a separate configuration concern and will be handled by the next story.
  - **Owner:** EPIC-01-STOR-02
  - **Follow-up:** Implement pinned toolchain files and optional devcontainer in EPIC-01-STOR-02.
  - **Resolved:** 2025-11-15

- **Question:** How to bypass Cloudflare challenge in automated scraper?
  - **Decision:** Use `undetected-chromedriver` with persistent session and headed mode; implement session persistence and anti-detection tuning in scraper core.
  - **Rationale:** Research and manual testing indicate Cloudflare blocks headless/naive automation; headed mode with persistent profile and undetected-chromedriver provides the best practical approach.
  - **Owner:** [`EPIC-02-STOR-01`](docs/JIRA/EPIC-02-STOR-01.md:1) (scraper core implementation)
  - **Follow-up:** EPIC-02 will implement create_driver, manual_login, load_session, and Cloudflare bypass strategies; store guidance and sample profile under `scraper/chrome-profile`.
  - **Temporary workaround:** Manual DOM inspection guide created for initial selector discovery; selectors must be populated by the user into `docs/selectors-template.yaml` → `selectors.yaml`.
  - **Resolved:** 2025-11-15

## Completion Summary
**Date:** 2025-11-16
**Status:** DONE - All acceptance criteria met, manual inspection completed

### Manual Inspection Results
- User provided HTML from `https://claude.ai/settings/usage` in [`docs/manual-inspection-results.md`](docs/manual-inspection-results.md:1)
- Confirmed 3 usage components present: Current session (3%), Weekly all models (36%), Weekly Opus (19%)
- Detailed selector extraction deferred to EPIC-02-STOR-01 (scraper implementation phase)
- HTML structure sufficient for proceeding with toolchain setup (EPIC-01-STOR-02)

### Next Story
Proceed to [`EPIC-01-STOR-02`](docs/JIRA/EPIC-01-STOR-02.md:1) - Pin toolchain versions (.nvmrc, rust-toolchain, devcontainer)