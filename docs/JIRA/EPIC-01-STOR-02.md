# EPIC-01-STOR-02

Title: Pin toolchain (rust-toolchain, .nvmrc) and add devcontainer

Epic: [`EPIC-01`](docs/JIRA/EPIC-LIST.md:14)

Status: TODO

## Description
As a developer, I need pinned toolchain files (.nvmrc, rust-toolchain) and an optional VS Code devcontainer so contributors get a reproducible environment matching Research.md.

## Acceptance Criteria
- [ ] `.nvmrc` sets Node 18 (verify with `node -v`)
- [ ] `rust-toolchain` file pins 1.70 (verify with `rustup show`)
- [ ] `.devcontainer/devcontainer.json` present and builds a container with node 18, rust 1.70, python3.9
- [ ] `docs/JIRA/EPIC-LIST.md` updated to reference devcontainer usage (see Research.md lines 121-126)

## Dependencies
- EPIC-01-STOR-01

## Tasks
- [ ] Create `.nvmrc` with content `18` (file: `.nvmrc`) — command: `echo "18" > .nvmrc` (0.25h)
- [ ] Create `rust-toolchain` with content `1.70.0` (file: `rust-toolchain`) — command: `echo "1.70.0" > rust-toolchain` (0.25h)
- [ ] Add `.devcontainer/devcontainer.json` and supporting `Dockerfile` (path: `.devcontainer/`) — include node 18, rust 1.70, python3.9 (2.0h)
- [ ] Add README note `docs/README-SETUP.md` describing how to use devcontainer and alternatives (0.5h)

## Estimate
Total: 3 hours

## Research References
- Research.md lines 121-126 (Node, Rust versions) [`docs/Research.md:121-126`]

## Risks & Open Questions
- Some contributors may not use Docker; ensure docs include non-container steps.
- Open question: Should devcontainer include Chrome/Chromium or map host browser for undetected-chromedriver (decision affects image size).