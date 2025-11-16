# EPIC-02-STOR-03

Title: JSON output schema and stdout protocol for Rust IPC

Epic: [`EPIC-02`](docs/JIRA/EPIC-LIST.md:24)

Status: TODO

## Description
As a developer, I need a precise JSON output schema and stdout/stderr protocol so the Rust Tauri backend can reliably consume scraper output and surface errors.

This story defines the JSON structure, stdout patterns, and error codes the Python scraper must emit. It also adds a `scraper/protocol.md` documenting examples.

## Acceptance Criteria
- [ ] `scraper/protocol.md` exists and documents:
  - JSON schema for scraper output (root keys: `components`, `status`, `found_components`, `diagnostics`, `timestamp`)
  - Example JSON payload with three components including fields: `id`, `name`, `usage_percent`, `tokens_used`, `tokens_limit`, `reset_time` (ISO8601|null), `raw_reset_text`, `last_updated`, `status`.
  - Error emission patterns: errors written to stderr as JSON objects with `error_code`, `message`, `details`, `timestamp`.
- [ ] Scraper stdout contains only a single JSON object per run (no extraneous logs). Non-critical logs go to stderr.
- [ ] Define error codes consistent with EPIC-08: `session_required`, `navigation_failed`, `session_expired`, `extraction_failed`, `fatal`.
- [ ] `docs/JIRA/EPIC-LIST.md` references updated to point to `scraper/protocol.md` for IPC contract.

## Dependencies
- EPIC-02-STOR-01 (scraper implemented)
- EPIC-04 (Rust backend will consume this protocol)

## Tasks
- [ ] Create `scraper/protocol.md` with schema and examples (0.75h)
- [ ] Add JSON serialization snippet in `scraper/claude_scraper.py` to `print(json.dumps(payload))` to stdout and route logs to stderr (0.5h)
- [ ] Add example error output for stderr (0.25h)
- [ ] Update `docs/JIRA/EPIC-LIST.md` with pointer to protocol (0.25h)

## Estimate
Total: 2 hours

## Research References
- EPIC-LIST.json schema expectations: EPIC-02 lines 26-31 [`docs/JIRA/EPIC-LIST.md:26-31`]
- Research.md: data flow & stdout JSON guidance: lines 69-74, 46-53 [`docs/Research.md:69-74`, `docs/Research.md:46-53`]

## Risks & Open Questions
- Risk: Extraneous stdout may break Rust JSON parser; ensure strict stdout policy.
- Open question: Should we support streaming multiple JSON messages per run or single-run output? For v1.0, choose single JSON per invocation (simpler for Rust subprocess handling).