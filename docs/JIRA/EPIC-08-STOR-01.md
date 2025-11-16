# EPIC-08-STOR-01

Title: Implement exponential backoff retry handler and integration points

Epic: [`EPIC-08`](docs/JIRA/EPIC-LIST.md:84)

Status: TODO

## Description
As a backend engineer, I need a reusable exponential-backoff retry handler so transient scraper failures (navigation timeouts, Cloudflare momentary blocks) are retried automatically with configurable parameters. The handler will be used by the Python scraper and by the Rust poller when appropriate.

This story implements:
- `scraper/retry_handler.py` for Python (used by scraper)
- `src-tauri/src/retry.rs` for Rust (used by poller/invoker)
- Standard configuration defaults and unit tests

## Acceptance Criteria
- [ ] `scraper/retry_handler.py` exports:
  - `class RetryPolicy(initial_delay: float=1.0, multiplier: float=2.0, max_attempts: int=4, max_delay: float=60.0)`
  - `def with_retry(func, policy: RetryPolicy, on_retry: Optional[Callable]=None) -> Any` or decorator `@retry(policy)`
  - Documentation of default values and example usage with `navigate_to_usage_page()` and `spawn_scraper()` flows
- [ ] `src-tauri/src/retry.rs` exports equivalent Rust helper (`RetryPolicy` struct and `retry_async` helper) used by poller and scraper invoker
- [ ] Default policy values documented and configurable via `config.json` (EPIC-07 config subsystem)
- [ ] Unit tests:
  - `scraper/tests/test_retry_handler.py` verifies exponential delays and stops after `max_attempts`
  - `src-tauri/tests/test_retry.rs` verifies Rust retry helper behavior (mocked async operation)
- [ ] Retry handler logs attempt number, delay, and reason to `scraper/scraper.log` or Rust logger.

## Dependencies
- EPIC-02 (scraper functions to be wrapped)
- EPIC-04 (Rust poller to use Rust retry helper)
- EPIC-07 (config persistence to store policy overrides)
- Research.md recommendation for retry/backoff parameters; see EPIC-LIST open questions for defaults (`docs/JIRA/EPIC-LIST.md:120`)

## Tasks (1-3 hours each)
- [ ] Implement `scraper/retry_handler.py` with `RetryPolicy` and decorator/helper usage examples (1.5h)
  - Example usage in scraper: `@retry(policy) def navigate_and_extract(...): ...`
- [ ] Add logging and allow `on_retry` callback to record diagnostics into JSON payload `diagnostics['retries']` (0.5h)
- [ ] Implement Rust equivalent `src-tauri/src/retry.rs` with async-friendly API using `tokio::time::sleep` (1.5h)
- [ ] Add tests for both Python and Rust implementations (1.25h)
- [ ] Document configuration keys and CLI/env overrides in `docs/JIRA/EPIC-08-RETRY.md` (0.5h)

## Estimate
Total: 5.25 hours

## Research References
- EPIC-LIST retry/backoff discussion and configuration suggestion (`docs/JIRA/EPIC-LIST.md:120`)
- Research.md: error handling and resilience requirements (see sections on Exponential backoff and logging) [`docs/Research.md:80-90`, `docs/Research.md:244-252`]

## Risks & Open Questions
- Risk: Aggressive retries may increase Cloudflare triggers; choose conservative defaults (initial 1s, multiplier 2, max_attempts 4).
- Open question: Should Rust and Python policies be kept in sync via shared config format (yes — tie to `config.json` in EPIC-07).