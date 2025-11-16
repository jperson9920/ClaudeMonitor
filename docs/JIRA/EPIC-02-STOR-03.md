# EPIC-02-STOR-03
Title: Scheduler and periodic collection
Epic: EPIC-02
Status: DONE

## Description
Add scheduling capability to run scraper every 5 minutes and collect usage data.

## Implementation Notes
- Implemented scheduler using APScheduler BackgroundScheduler in [`src/scraper/scheduler.py`](src/scraper/scheduler.py:1).
- Default polling interval: 5 minutes, configurable via ScraperScheduler(interval_minutes=...).
- Retry logic: integrates with existing `src/scraper/retry_handler.py` if present; falls back to a built-in exponential backoff (3 retries).
- Results are stored as timestamped JSON files in ./scraper/data by default (override with CLAUDE_SCRAPER_DATA_DIR env var).
- Scheduler can be started/stopped programmatically via ScraperScheduler.start()/stop().
- Logging added for scheduled runs and failures.
- Prepared for EPIC-02-STOR-04 storage integration by storing full payload under "payload" key and "collected_at" timestamp.

## Acceptance Criteria
- [x] Implement scheduler using APScheduler or similar
- [x] Configure 5-minute polling interval
- [x] Add retry logic for failed scrapes
- [x] Store results with timestamps