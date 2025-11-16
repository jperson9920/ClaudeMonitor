# Scraper — Usage & Setup

This folder contains convenience scripts for creating a Python virtual environment and performing a manual login run for the Claude usage scraper.

Files:
- requirements.txt — pinned dependencies for the scraper environment
- setup.sh / setup.ps1 — create and install a venv with requirements
- run_manual_login.sh / run_manual_login.ps1 — start the scraper in manual login mode
- chrome-profile/ — persistent Chrome profile and session files (created by scraper at runtime)
- scraper.log — scraper runtime log (appended by scraper)

Quick setup (Unix/macOS):
1. ./setup.sh
2. source scraper-env/bin/activate
3. ./run_manual_login.sh

Quick setup (Windows PowerShell):
1. .\setup.ps1
2. .\run_manual_login.ps1

Manual login notes:
- The manual login flow opens a real Chrome window via undetected-chromedriver. Complete the login, any CAPTCHAs or 2FA, and do not close the Chrome window until the scraper finishes and indicates success.
- Session files are stored under scraper/chrome-profile/ (e.g. session.json). Use these to persist authentication between runs.
- Logs are written to scraper/scraper.log. Inspect this file for diagnostics if anything fails.

Troubleshooting:
- If undetected-chromedriver fails to download a matching driver, see Research.md for offline-driver instructions and consider running the script on a machine with internet access to populate the driver cache.
- If you prefer an isolated venv path, create it manually and ensure you install requirements.txt into that environment.

License and safety:
- This scraper is intended for single-user personal automation. Do not use it to bypass security controls or to automate actions prohibited by the target website's terms of service.