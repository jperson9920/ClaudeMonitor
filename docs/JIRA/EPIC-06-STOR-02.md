# EPIC-06-STOR-02

Title: Implement Rust bundling support for scraper resources and launcher

Epic: [`EPIC-06`](docs/JIRA/EPIC-LIST.md:64)

Status: DONE

## Implementation notes
- Implemented `src-tauri/src/resource.rs` exposing `pub fn resolve_scraper_path() -> Result<PathBuf, String>` (see [`src-tauri/src/resource.rs`](src-tauri/src/resource.rs:1)).
- Updated launcher in [`src-tauri/src/scraper.rs`](src-tauri/src/scraper.rs:1) to:
  - Resolve scraper path and validate UTF-8
  - Launch `python <path>` when `.py` script is detected
  - Launch bundled executable directly otherwise
  - Set working directory to scraper parent directory
  - Return `ScraperError::Execution` with helpful messages on failure
- Added tests in [`src-tauri/tests/test_resource_resolution.rs`](src-tauri/tests/test_resource_resolution.rs:1) using `TAURI_RESOURCE_DIR_MOCK` to simulate bundle layout and `CLAUDE_SCRAPER_PATH` override.
- Documented env override and troubleshooting in [`docs/JIRA/BUNDLING.md`](docs/JIRA/BUNDLING.md:1).

## Description
As a release engineer, I need the Rust backend to locate and invoke the scraper whether it's a source `.py` script during development or a bundled executable in production. This story implements resource resolution and launcher logic in `src-tauri/src/scraper.rs` and `src-tauri/src/resource.rs` and documents the runtime behavior.

User perspective: "The app runs the scraper correctly both in dev and when packaged as a Tauri bundle."

## Acceptance Criteria
- [ ] `src-tauri/src/resource.rs` exposes:
  - `pub fn resolve_scraper_path() -> Result<PathBuf, String>` which:
    - In dev returns project-relative `../scraper/claude_scraper.py`
    - In bundle returns `tauri::api::path::resource_dir().join("scraper/claude_scraper{.exe}")` (OS-aware)
- [ ] `src-tauri/src/scraper.rs` uses `resolve_scraper_path()` and:
  - If the resolved path ends with `.py` launches `python <path> <args>`
  - If resolved path is executable launches the exe directly with `<args>`
  - Uses `Command` with explicit working directory set to resource_dir where applicable
- [ ] Path resolution and launcher accept an environment override `CLAUDE_SCRAPER_PATH` to allow manual testing.
- [ ] Errors when path not found or not executable map to `ScraperError::Execution` with helpful message and appear in `docs/JIRA/BUNDLING.md` troubleshooting section.

## Dependencies
- EPIC-06-STOR-01 (bundling strategy docs)
- EPIC-04-STOR-02 (Rust ScraperInterface)

## Tasks (1-3 hours each)
- [ ] Implement `src-tauri/src/resource.rs` with `resolve_scraper_path()` including OS-specific extensions and `CLAUDE_SCRAPER_PATH` env override (1.0h)
  - Use `tauri::api::path::resource_dir()` for bundle path resolution; fallback to dev path `../../scraper/claude_scraper.py` if resource_dir is None.
- [ ] Update `src-tauri/src/scraper.rs` to call `resolve_scraper_path()` and implement launcher branch for `.py` vs executable; include timeout handling (1.5h)
  - Example spawn: `Command::new("python").arg(scraper_path).arg("--poll_once")...`
- [ ] Add unit tests `src-tauri/tests/test_resource_resolution.rs` mocking `resource_dir()` to validate dev vs bundle behavior (1.0h)
- [ ] Document the env override and troubleshooting steps in `docs/JIRA/BUNDLING.md` (0.5h)

## Estimate
Total: 4 hours

## Research References
- EPIC-LIST bundling notes and resource_dir behavior: `docs/JIRA/EPIC-LIST.md:64-71`
- Research.md notes on bundling strategies and PyInstaller considerations: `docs/Research.md:200-206`, `docs/Research.md:70-76`

## Risks & Open Questions
- Risk: Bundled exe naming/extension differs by OS; tests must cover Windows `.exe`, macOS bundle layout, and Linux executable permission.
- Open question: Default to system Python for dev — confirm CI builders have Python available or include minimal runtime in devcontainer (see EPIC-01-STOR-02).