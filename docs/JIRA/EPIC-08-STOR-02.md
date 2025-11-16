# EPIC-08-STOR-02

Title: Define structured error codes, diagnostics schema and logging format

Epic: [`EPIC-08`](docs/JIRA/EPIC-LIST.md:84)

Status: TODO

## Description
As an engineer, I need a documented set of structured error codes and a diagnostics JSON schema so both the Python scraper and Rust backend surface consistent, machine- and human-readable errors to the frontend and logs. This enables clear UI messages and automated handling (e.g., session_required → prompt login).

This story produces `scraper/errors.md`, implements consistent error emission in `scraper/claude_scraper.py` and maps errors to frontend strings in `src-tauri/src/scraper.rs`.

## Acceptance Criteria
- [ ] `scraper/errors.md` lists canonical error codes and shapes:
  - `session_required`, `navigation_failed`, `session_expired`, `extraction_failed`, `cloudflare_detected`, `timeout`, `fatal`
  - Each error includes fields: `error_code`, `message`, `details` (optional), `timestamp`, `attempts` (optional), `diagnostics` (optional)
- [ ] Python scraper writes errors to stderr as a single JSON object when a non-recoverable error occurs.
- [ ] Rust `ScraperError` maps incoming JSON error_code to enum variants and exposes a user-facing message and `diagnostics` object to the frontend.
- [ ] `scraper/scraper.log` entries include both human-readable log lines and structured JSON snippets for errors to ease parsing by log collectors.

## Dependencies
- EPIC-02 (scraper logic)
- EPIC-04 (Rust error mapping)
- EPIC-08-STOR-01 (retry handler)

## Tasks (1-2 hours each)
- [ ] Create `scraper/errors.md` enumerating error codes, example JSON payloads, and recommended handling (0.75h)
- [ ] Update `scraper/claude_scraper.py` to emit stderr JSON for errors and include `diagnostics` when available (1.0h)
  - Example:
    - print(json.dumps({"error_code":"session_required","message":"Login required","timestamp":...}), file=sys.stderr)
- [ ] Update `src-tauri/src/scraper.rs` to parse stderr JSON and convert to `ScraperError::Protocol` with included diagnostics, and to return structured responses to frontend (1.0h)
- [ ] Add short tests or examples demonstrating mapping error JSON to UI-friendly messages (0.5h)

## Estimate
Total: 3.25 hours

## Research References
- EPIC-08 acceptance criteria and error codes: `docs/JIRA/EPIC-LIST.md:86-90`
- Research.md logging and stderr/stdout guidance: `docs/Research.md:233-241`, `docs/Research.md:69-74`

## Risks & Open Questions
- Risk: Including sensitive diagnostics (e.g., cookies, tokens) in `diagnostics` — ensure no sensitive data is emitted. Sanitization required.
- Open question: Level of diagnostics exposed to end-user vs only to logs — recommend UI shows brief message and "Details" expands diagnostics for advanced users.