# Browser Visibility & Scraper Behavior (BEHAVIOR)

## Objective
- Describe the visibility policy and operational constraints for the headed scraper browser.

## Visibility policy
- The headed browser used by the scraper is visible only when:
  - The user initiates a manual login (`--login`) — the browser remains open until the user completes login and confirms.
  - A poll is running in single-run mode (`--poll_once`) — the browser may be visible briefly while navigation and Cloudflare resolution occurs (target ~5–10s).
- The scraper must never attempt to close or interfere with the user's primary browser windows. It uses a dedicated user-data-dir (`./scraper/chrome-profile`) to isolate cookies/profile.

## Headed vs headless
- Headed mode is required to avoid Cloudflare issues and for manual login flows. Automated single-run polls still run in headed mode but briefly; `create_driver` uses `headless=False` for polls.

## Session persistence
- Session cookies and metadata are saved to `./scraper/chrome-profile/session.json`.
- `session_manager.save_session` / `load_session` handle atomic writes and loads; polls will refuse to run in `--poll_once` mode if no valid session exists.

## Security & UX notes
- The scraper should respect the user's environment: do not close other Chrome windows, do not overwrite global browser settings.
- Keep poll windows short to minimize disruption and Cloudflare exposure.

## Developer testing
- Run single poll: `python scraper/claude_scraper.py --poll_once`
- Manual login flow: `python scraper/claude_scraper.py --login`
- Check session: `python scraper/claude_scraper.py --check-session`

## References
- docs/JIRA/EPIC-07-TRAY.md
- docs/JIRA/EPIC-07-STOR-02.md