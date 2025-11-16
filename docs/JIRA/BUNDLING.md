# Bundling Strategies for the Python Scraper

This document describes supported approaches for packaging and resolving the Python scraper used by the Tauri/Rust backend.

Supported approaches
- System Python (recommended default for development)
  - The app calls the host Python interpreter to run the scraper source script:
    - python scraper/claude_scraper.py
  - Pros:
    - Small app footprint
    - Easier iterative development / debugging
    - No bundling toolchain required
  - Cons:
    - Requires target machine to have a compatible Python runtime (3.9+ recommended)
    - Slightly more fragile for end-users if their environment varies

- Bundled Python (PyInstaller)
  - Build a self-contained native executable using PyInstaller and ship it inside the Tauri resources folder.
  - Pros:
    - No system Python required on user machines
    - Easier single-binary distribution for end-users
  - Cons:
    - Large binary (often ~50–100MB depending on dependencies)
    - Platform-specific builds required (Windows/macOS/Linux)
    - Potential complications with native drivers (ChromeDriver) and auto-download behavior

PyInstaller example
- Basic one-file build (Windows example shown; adapt path separators on POSIX):
  pyinstaller --onefile --add-data "chrome-profile;chrome-profile" claude_scraper.py
- Notes:
  - Use the --add-data option to include any local profile or data directories needed at runtime.
  - For macOS, PyInstaller may produce an executable inside a .app wrapper; test the resulting layout to ensure the binary is accessible.
  - For Linux, ensure execute permission bits are preserved when packaging into resources.

Resource resolution strategy (runtime)
1. Environment override (manual debug/testing)
   - CLAUDE_SCRAPER_PATH environment variable may be set to an absolute path to either:
     - the Python script (claude_scraper.py), or
     - a bundled executable (claude_scraper or claude_scraper.exe)
   - This is the highest-priority resolution and is useful for manual testing.

2. Bundled app (production)
   - If running as a Tauri bundle, the app will use tauri::api::path::resource_dir() to locate the resource directory and expect:
     - <resource_dir>/scraper/claude_scraper(.exe)
   - The Rust helper resolves OS-specific filename (claude_scraper.exe on Windows, claude_scraper on POSIX).
   - The app will launch the bundled executable directly with CLI args.

3. Development fallback (dev)
   - If no resource dir is detected, the app will fall back to the project-relative script:
     - ../scraper/claude_scraper.py
   - The app will invoke: python ../scraper/claude_scraper.py <args...>

Runtime launcher behavior (summary)
- If resolved path ends with .py: spawn system Python (python <path> <args>)
- Else if resolved path is an executable: run it directly (<path> <args>)
- Working directory will be set to the parent folder of the resolved path where appropriate.

Troubleshooting
- Common resolution errors:
  - "CLAUDE_SCRAPER_PATH is set to '...' but the file does not exist"
    - Verify the path and file permissions.
  - "Tauri resource dir detected at '...' but expected bundled scraper at '...' was not found"
    - Make sure the scraper binary was included in the Tauri build resources (tauri.conf.json / build scripts).
  - "Could not locate scraper" (fallback failure)
    - Ensure the project has scraper/claude_scraper.py relative to the Tauri crate or set CLAUDE_SCRAPER_PATH for local testing.
- ChromeDriver handling:
  - If the scraper auto-downloads ChromeDriver at runtime it may fail inside a tightly packaged environment.
  - Workarounds:
    - Pre-bundle the driver and include it with --add-data or a post-install step.
    - Configure the scraper to download to a writable user data directory (not inside the app bundle).
- Permissions
  - On Linux/macOS, ensure the bundled executable has execute permission. If packaging into resources, preserve execute bit or run a small shim script to set permissions on first launch.

Testing & manual verification
- Development:
  - Run the Tauri app in dev mode (cargo tauri dev) and make sure python scraper/claude_scraper.py exists in the expected location.
  - Or set CLAUDE_SCRAPER_PATH to the script for quick testing.
- Production:
  - Build the PyInstaller binary for each platform, place it under the Tauri resource path scraper/, then build the Tauri bundle and test the bundled app.

Environment override usage
- CLAUDE_SCRAPER_PATH=/absolute/path/to/claude_scraper.exe (or .py)
- Use for quick local tests, CI matrix runs, or when system python is not desired.

Platform-specific notes
- Windows: expected binary name is claude_scraper.exe. Pay attention to Windows path quoting in build commands.
- macOS: PyInstaller may produce a binary inside a .app — ensure the runtime code can locate the inner executable or use a one-file build.
- Linux: Preserve execute permissions and consider ld-linux/GLIBC compatibility for target distributions.

Recommended default
- For development: use System Python (simpler developer experience).
- For production: provide a PyInstaller recipe in repository docs for maintainers who want a self-contained release. Document the build steps and include notes about ChromeDriver and user data directories.

References
- See EPIC-06 stories:
  - docs/JIRA/EPIC-06-STOR-01.md
  - docs/JIRA/EPIC-06-STOR-02.md