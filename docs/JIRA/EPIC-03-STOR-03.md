# EPIC-03-STOR-03

Title: Document re-login procedure and safe storage recommendations

Epic: [`EPIC-03`](docs/JIRA/EPIC-LIST.md:34)

Status: TODO

## Description
As a developer/admin, I need clear documentation describing how to perform a re-login, rotate stored sessions, and securely store `scraper/chrome-profile` to avoid accidental cloud sync or exposure.

This story produces `docs/JIRA/SESSION-MANAGEMENT.md` describing manual steps and recommended file permissions.

## Acceptance Criteria
- [ ] `docs/JIRA/SESSION-MANAGEMENT.md` created with:
  - Manual re-login steps (use `python claude_scraper.py --login`, keep browser open, press Enter)
  - How to invalidate a session (delete `scraper/chrome-profile/session.json`) and troubleshoot common errors (session expired, Cloudflare challenge)
  - Recommended file permissions (owner-only) and OS-specific commands to set them (e.g., `chmod 600` on Unix)
  - Advice to never sync the `scraper/chrome-profile` directory to cloud services (OneDrive, Dropbox)
- [ ] Document sample troubleshooting steps for Cloudflare (open page in browser, confirm manual login) and links back to EPIC-02 Cloudflare docs.

## Dependencies
- EPIC-03-STOR-01
- EPIC-02-STOR-05 (cloudflare handling docs)

## Tasks
- [ ] Draft `docs/JIRA/SESSION-MANAGEMENT.md` with sections: Re-login, Invalidate Session, Secure Storage, Troubleshooting (1.5h)
- [ ] Add OS-specific permission commands and examples (Windows ACLs via icacls, Unix chmod/chown) (0.5h)
- [ ] Link to `scraper/run_manual_login.sh` and CLI flags documented in EPIC-03-STOR-02 (0.25h)

## Estimate
Total: 2.25 hours

## Research References
- Research.md: session persistence rationale (lines 91-96, 356-370) [`docs/Research.md:91-96`, `docs/Research.md:356-370`]
- EPIC-LIST.md: safe storage guidance and not syncing profile (line 109, 124) [`docs/JIRA/EPIC-LIST.md:109`, `docs/JIRA/EPIC-LIST.md:124`]

## Risks & Open Questions
- Risk: Users may inadvertently back up profile directories; docs must clearly warn and suggest `.gitignore` patterns.
- Open question: Should we provide an optional encrypted session storage (deferred to EPIC-10).