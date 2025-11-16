# EPIC-01-STOR-02

Title: Pin toolchain (rust-toolchain, .nvmrc) and add devcontainer

Epic: [`EPIC-01`](docs/JIRA/EPIC-LIST.md:14)

Status: DONE

## Description
As a developer, I need pinned toolchain files (.nvmrc, rust-toolchain) and an optional VS Code devcontainer so contributors get a reproducible environment matching Research.md.

## Acceptance Criteria
- [x] `.nvmrc` sets Node 18 (verify with `node -v`)
- [x] `rust-toolchain` file pins 1.70 (verify with `rustup show`)
- [x] `.devcontainer/devcontainer.json` present and builds a container with node 18, rust 1.70, python3.9
- [x] `docs/JIRA/EPIC-LIST.md` updated to reference devcontainer usage (see Research.md lines 121-126)

## Dependencies
- EPIC-01-STOR-01

## Tasks
- [x] Create `.nvmrc` with content `18` (file: `.nvmrc`) — command: `echo "18" > .nvmrc` (0.25h)
- [x] Create `rust-toolchain` with content `1.70.0` (file: `rust-toolchain`) — command: `echo "1.70.0" > rust-toolchain` (0.25h)
- [x] Add `.devcontainer/devcontainer.json` and supporting `Dockerfile` (path: `.devcontainer/`) — include node 18, rust 1.70, python3.9 (2.0h)
- [x] Add README note `docs/README-SETUP.md` describing how to use devcontainer and alternatives (0.5h)

## Estimate
Total: 3 hours

## Research References
- Research.md lines 121-126 (Node, Rust versions) [`docs/Research.md:121-126`]

## Decisions / Notes
- Chromium is included in the devcontainer image to support scraper development and headful tests. This increases image size but enables local headed runs and CI-friendly browser testing. If contributors prefer mapping a host browser for undetected-chromedriver, document that option in `docs/README-SETUP.md`.
- Devcontainer pinning uses `rust-toolchain` = 1.70.0 and `.nvmrc` = 18 for Node; these files are authoritative for local non-container setup.

## Risks & Open Questions
- Some contributors may not use Docker; docs/README-SETUP.md contains alternative local setup steps.