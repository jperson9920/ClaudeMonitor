# Development Environment — Setup

## Devcontainer (recommended)
- Open this repository in VS Code.
- Use "Remote-Containers: Reopen in Container" (or "Dev Containers: Reopen in Container") to build the image from `.devcontainer/Dockerfile`.
- The devcontainer image includes Node 18, Rust 1.70.0 (via rustup), Python 3.9, and Chromium for headed testing.
- VS Code extensions configured in `.devcontainer/devcontainer.json` (Rust, Python, TypeScript/JS tooling, formatter/linters) will be suggested/installed automatically.
- The `postCreateCommand` config will attempt to set the rust toolchain and install common Rust components.
- Note: including Chromium increases image size. Alternative: map a host Chrome/Chromium binary into the container for undetected-chromedriver usage — see "Troubleshooting" below.

## Alternative: Local (non-container) setup
- Node: use nvm and the provided `.nvmrc`:
  - nvm install
  - nvm use
  - or: nvm install 18 && nvm use 18
- Rust: rustup will respect the `rust-toolchain` file if present:
  - rustup toolchain install
  - rustup default 1.70.0
- Python 3.9:
  - python3.9 -m venv venv
  - source venv/bin/activate  (or venv\Scripts\Activate on Windows)
  - pip install -r scraper/requirements.txt  (if present)

## Verification commands
- Verify Node: node -v  (should show v18.x)
- Verify Rust: rustup show or rustup show active-toolchain (should indicate 1.70.0)
- Verify Python: python --version  (should show 3.9.x)

## Troubleshooting
- If Node version is incorrect: run `nvm install 18` then `nvm use 18`.
- If Rust toolchain not active: run `rustup default 1.70.0`.
- If Chromium is not available in your environment: either map the host browser into the container or install a browser on the host and configure the scraper to use the host path.

## Decision log
- Chromium included in the devcontainer to support headed scraper development and local CI-friendly browser tests. This increases image size but simplifies contributor setup. Mapping a host browser is documented as an alternative.