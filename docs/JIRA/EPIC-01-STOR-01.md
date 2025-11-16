# EPIC-01-STOR-01

Title: Initialize repository, toolchain docs and Tauri scaffold

Epic: [`EPIC-01`](docs/JIRA/EPIC-LIST.md:14)

Status: TODO

## Description
As a developer, I need a reproducible project skeleton and clear environment setup so I can build and run the Tauri desktop widget and Python scraper locally without onboarding friction.

This story creates the initial project scaffold, documents required toolchain versions, and provides step-by-step setup instructions for Node, Rust, and Python venv. Context and rationale come from the Research guide which mandates Tauri + Rust backend and Python 3.9+ for the scraper (see Research.md).

## Acceptance Criteria
- [ ] Repository contains an initialized Tauri scaffold with top-level directories: `src-tauri/`, `src/` and `scraper/` (as a minimal scaffold) and `scraper-env/` venv placeholder. (Verify file tree)
- [ ] `docs/README-SETUP.md` or `README.md` includes explicit installation steps for Node 18+, Rust 1.70+, Python 3.9+ and Chrome. Refer to Research.md lines 121-126 and 157-166 for exact versions. (Verify docs file)
- [ ] `scraper/requirements.txt` added with `undetected-chromedriver` and `selenium` and `scraper/claude_scraper.py` placeholder file exists with header docstring. (Verify files & content)
- [ ] A short local CI checklist is added to `docs/JIRA/EPIC-LIST.md` or `README.md` describing manual validation steps (create venv, install, run scraper in --login) referencing Research.md lines 181-201. (Verify checklist)

## Dependencies
- None (first story of EPIC-01)
- External: Node.js 18+, Rust 1.70+, Python 3.9+, Chrome/Chromium (Research.md references lines 121-126, 157-166, 174-179)

## Tasks (each task ~1-3 hours)
- [ ] Create directories and minimal files:
  - Create `src-tauri/`, `src/`, `scraper/`
  - Files: `scraper/claude_scraper.py` (header only), `scraper/requirements.txt`
  - Command: `mkdir src-tauri src scraper && echo "# scraper requirements" > scraper/requirements.txt`
- [ ] Add setup instructions:
  - File: `docs/README-SETUP.md`
  - Content: exact commands from Research.md for Node/Rust/Python (see references below)
  - Example commands to include (copy verbatim):
    - `npm create tauri-app@latest`
    - `python3 -m venv scraper-env` (Windows: `scraper-env\Scripts\activate`)
- [ ] Commit files (dry-run guidance only; DO NOT run git commands here). Add instructions for RooWrapper git helper DryRun workflow in `docs/JIRA/README-GIT-WORKFLOW.md`.
- [ ] Add lint/checklist to `docs/JIRA/EPIC-LIST.md` under EPIC-01 referencing version checks.

## Estimate
Total: 4 hours
- Directory & scaffold creation: 1h
- Writing setup docs and commands: 2h
- QA review and checklist: 1h

## Research References
- Research.md lines 121-126 (Node, Rust, Python versions) [`docs/Research.md:121`]
- Research.md lines 181-201 (project initialization + venv & dependencies) [`docs/Research.md:181-201`]
- EPIC-LIST.md lines 14-22 (EPIC-01 goal & acceptance criteria) [`docs/JIRA/EPIC-LIST.md:14-22`]

## Risks & Open Questions
- Risk: Developers may have different system package managers; docs must include both macOS/Linux/Windows variants (Research.md provides examples lines 139-156).
- Open question: Should the repo include a pinned Node and Rust toolchain config files (.nvmrc, rust-toolchain)? Recommend adding; decision deferred to EPIC-01-STOR-02.