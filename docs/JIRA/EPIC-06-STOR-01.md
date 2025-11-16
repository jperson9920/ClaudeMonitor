# EPIC-06-STOR-01

Title: Define bundling strategy and resource resolution for Python scraper

Epic: [`EPIC-06`](docs/JIRA/EPIC-LIST.md:64)

Status: TODO

## Description
As a release engineer, I need a clear bundling strategy so the Tauri/Rust app can locate and invoke the Python scraper in both development and bundled distributions. This story documents options (bundle Python via PyInstaller or require system Python), defines resource resolution code paths, and implements a Rust helper that resolves scraper executable path at runtime.

User perspective: "As a user I can run the packaged app without manual extra steps if packaging includes Python, or the app clearly documents the system-Python requirement."

## Acceptance Criteria
- [ ] `docs/JIRA/BUNDLING.md` created describing two supported approaches:
  - Bundled Python: PyInstaller-built scraper binary shipped inside Tauri resources
  - System Python: require user Python 3.9+ and call `python scraper/claude_scraper.py`
- [ ] `src-tauri/src/resource.rs` (or `scraper.rs`) includes function:
  - `fn resolve_scraper_path(resource_dir: &Path) -> PathBuf` with documented behavior for dev vs bundle (use `tauri::api::path::resource_dir()` in runtime)
- [ ] `docs/JIRA/BUNDLING.md` includes sample PyInstaller command and notes about native dependencies (ChromeDriver auto-download) and size/security tradeoffs.
- [ ] Decision and recommended default recorded (recommend: support both; default to system-Python for development and provide PyInstaller recipe for users who want a self-contained build).

## Dependencies
- EPIC-04 (Rust backend must call scraper)
- EPIC-02 (scraper protocol)
- EPIC-10 (security notes about storing bundled Python and profiles)

## Tasks
- [ ] Draft `docs/JIRA/BUNDLING.md` with pros/cons, example PyInstaller command:
  - `pyinstaller --onefile --add-data "chrome-profile;chrome-profile" claude_scraper.py` and notes about platform differences (1.5h)
- [ ] Implement `src-tauri/src/resource.rs` with `resolve_scraper_path(resource_dir: &Path) -> PathBuf` and document usage (0.75h)
  - Example behavior:
    - In dev: return project-root `scraper/claude_scraper.py`
    - In bundle: return `resource_dir.join("scraper/claude_scraper.exe" or OS equivalent)`
- [ ] Add example code in `src-tauri/src/scraper.rs` showing how to call `resolve_scraper_path` and launch either `python <script>` or bundled exe (0.5h)
- [ ] Update `docs/JIRA/EPIC-LIST.md` pointer to `docs/JIRA/BUNDLING.md` (0.25h)

## Estimate
Total: 3 hours

## Research References
- EPIC-LIST bundling notes and requirement to include scraper in bundled app (`docs/JIRA/EPIC-LIST.md:64-71`)
- Research.md notes about PyInstaller and distribution options (`docs/Research.md:70-76`, `docs/Research.md:200-206`)

## Risks & Open Questions
- Risk: Bundling Python increases installer size and may conflict with ChromeDriver auto-download. Document driver handling and offline installation steps.
- Open question: Default strategy for v1.0 — recommend system-Python for developer builds and provide PyInstaller recipe for user-packaged releases.