# EPIC-10-STOR-01

Title: Build targets and Tauri packaging recipe

Epic: [`EPIC-10`](docs/JIRA/EPIC-LIST.md:104)

Status: TODO

## Description
Provide a reproducible, developer-friendly build and packaging recipe that creates platform installers for Windows, macOS and Linux using Tauri. The recipe covers:

- Tauri configuration snippets (`tauri.conf.json`) tuned for desktop bundles.
- Options for bundling the Python scraper: PyInstaller one-file executable, embeddable Python, or requiring system Python.
- Commands to produce build artifacts in `dist/` and `src-tauri/target/`.
- Guidance for signing (optional) and minimizing bundle size to align with expected Tauri bundle characteristics.

This enables a developer to run a local build (or CI build) and produce platform-specific installers that include the Rust/React app and either a bundled Python scraper binary or instructions to install Python.

## Acceptance Criteria
- [ ] `docs/JIRA/BUILD_PACKAGING.md` exists and contains:
  - Exact `tauri.conf.json` snippet showing `bundle.identifier`, `windows`, `macOS`, and `linux` sections and example `resources` entries referencing the bundled scraper.
  - Step-by-step build commands for each platform (Windows, macOS, Linux) with required environment prerequisites.
  - PyInstaller recipe example for creating a bundled `scraper.exe` / `scraper` binary and how to include it in the Tauri bundle.
- [ ] `docs/JIRA/BUILD_PACKAGING.md` shows exact commands to:
  - install requirements for scraper: `python -m venv .venv && .venv/Scripts/activate && pip install -r scraper/requirements.txt`
  - build PyInstaller bundle: `pyinstaller --onefile --name claude_scraper scraper/claude_scraper.py --distpath src-tauri/bundled_scraper/`
  - run Tauri build (example): `cd src-tauri && cargo build --release && cd ../ && npm run build && cd src-tauri && tauri build`
  - resulting artifacts location: `src-tauri/target/release/bundle/` and `dist/`
- [ ] `docs/JIRA/BUILD_PACKAGING.md` documents both options:
  - Bundled Python via PyInstaller (recommended for ease of end-user install)
  - Requiring system Python and installing via platform package managers (notes and commands)
- [ ] Research reference included for expected Tauri bundle size guidance: `docs/Research.md:101-106`
- [ ] Example `tauri.conf.json` snippet included in the docs (exact JSON block) with `resources` referencing `src-tauri/bundled_scraper/claude_scraper{.exe,}`

## Dependencies
- EPIC-06 (bundling strategy & resource resolution)
- EPIC-04 (Tauri backend build must succeed)
- EPIC-09 (test packaging artifacts in CI)

## Tasks (1–4 hours each)
- [ ] Draft `docs/JIRA/BUILD_PACKAGING.md` skeleton and include prerequisites section (1.0h)
  - File path: `docs/JIRA/BUILD_PACKAGING.md`
- [ ] Add `tauri.conf.json` example block and explain fields to edit (1.5h)
  - Show exact JSON snippet, include `bundle.identifier`, `resources`, `macOS.entitlements`, and `windows.signing` placeholders
- [ ] Add PyInstaller recipe and exact commands to produce `src-tauri/bundled_scraper/claude_scraper{.exe,}` (2.0h)
  - Commands:
    - `python -m venv .venv`
    - `.venv/Scripts/activate` (Windows) or `source .venv/bin/activate` (macOS/Linux)
    - `pip install -r scraper/requirements.txt pyinstaller`
    - `pyinstaller --onefile --name claude_scraper scraper/claude_scraper.py --distpath src-tauri/bundled_scraper/`
- [ ] Add platform build steps and commands:
  - Windows (NSIS): `cd src-tauri && tauri build --target x86_64-pc-windows-msvc` (1.5h)
  - macOS (.dmg): `cd src-tauri && tauri build --target x86_64-apple-darwin` (1.5h)
  - Linux (AppImage/deb): `cd src-tauri && tauri build --target x86_64-unknown-linux-gnu` (1.5h)
- [ ] Add verification steps to validate bundled scraper included in final installer and small smoke-test commands to run installers locally (1.0h)

## Estimate
Total: 7.5 hours

## Research References
- Tauri bundle size guidance and expectations: `docs/Research.md:101-106`
- Bundling strategy notes and Python embeddable options: `docs/JIRA/EPIC-06-STOR-01.md` and `docs/Research.md:202-211`

## Risks & Open Questions
- Risk: PyInstaller-produced binaries may increase artifact size significantly; need to evaluate Tauri expected sizes (`docs/Research.md:101-106`) and trade-offs between user convenience and download size.
- Risk: Code signing requirements (macOS notarization, Windows signing) may be required for production distribution; this is optional but noted.
- Open question: Preferred default for distribution — bundle Python (easier UX) or require system Python (smaller bundle)? Flag for Orchestrator decision.
- Open question: Which installer formats are priority for v1.0 (NSIS vs MSI for Windows)? Developer preference may drive final choice.