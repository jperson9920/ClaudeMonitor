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

## Phase 2: DOM Selector Extraction

### Phase 2A: Automated Puppeteer Inspection (FAILED)
**Date:** 2025-11-15
**Approach:** Attempted automated puppeteer navigation to `https://claude.ai/settings/usage`
**Result:** BLOCKED by Cloudflare challenge
**Details:**
- Cloudflare Ray ID: `99f3b35e1d6a9450`
- Error: "Checking if the site connection is secure" challenge page
- Root cause: Cloudflare bot detection blocks headless/automated browsers

### Phase 2B: Manual DOM Inspection (CURRENT)
**Date:** 2025-11-15
**Approach:** User performs manual browser inspection to extract selectors
**Status:** BLOCKED - awaiting user manual inspection

**Created artifacts:**
- [`docs/DOM-INSPECTION-GUIDE.md`](../DOM-INSPECTION-GUIDE.md) - Step-by-step manual inspection instructions
- [`docs/selectors-template.yaml`](../selectors-template.yaml) - Template for user to fill with extracted selectors

**Required selectors (3 components):**
1. **Current session** - Session usage component (percentage, reset time)
2. **Weekly limits — All models** - Weekly all-models usage (percentage, reset time)
3. **Weekly limits — Opus only** - Weekly Opus-only usage (percentage, reset time)

**Each component needs:**
- Parent container CSS selector
- XPath fallback selector
- Percentage text selector (e.g., "75% used")
- Reset time selector (e.g., "Resets in 59 min")
- Screenshot and sample HTML

**User action required:**
1. Follow [`docs/DOM-INSPECTION-GUIDE.md`](../DOM-INSPECTION-GUIDE.md)
2. Fill [`docs/selectors-template.yaml`](../selectors-template.yaml) with extracted values
3. Validate selectors in browser DevTools console
4. Rename `selectors-template.yaml` → `selectors.yaml`
5. Update this story status to COMPLETED

## Risks & Open Questions
- Risk: Developers may have different system package managers; docs must include both macOS/Linux/Windows variants (Research.md provides examples lines 139-156).
- Open question: Should the repo include a pinned Node and Rust toolchain config files (.nvmrc, rust-toolchain)? Recommend adding; decision deferred to EPIC-01-STOR-02.
- **NEW - Cloudflare bypass strategy:** How to bypass Cloudflare challenge in automated scraper?
  - **Proposed solution:** Use `undetected-chromedriver` in headed mode with persistent session (as documented in [`Research.md`](../Research.md))
  - **Implementation:** EPIC-02-STOR-01 (scraper core) will implement session persistence and Cloudflare bypass
  - **Reference:** Research.md emphasizes using headed browser with manual authentication, then persistent cookies for subsequent automated runs
  - **Owner:** To be addressed in EPIC-02 implementation phase
  - **Workaround:** Manual selector extraction (Phase 2B) unblocks project setup while scraper implementation is pending