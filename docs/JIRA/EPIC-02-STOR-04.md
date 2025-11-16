# EPIC-02-STOR-04 — Persistent storage and schema migration

## Summary
- Implemented a lightweight SQLite-backed storage layer and simple migration runner.
- Scheduler now persists scrapes into DB via `storage.insert_scrape_result(...)`.
- Includes basic retention configuration and a programmatic prune API.

## Files added/changed
- `src/scraper/storage.py`
- `src/scraper/migrations/0001_initial_schema.sql`
- `src/scraper/migrations/0002_retention_meta.sql`
- `src/scraper/scheduler.py` (modified to persist scrapes)
- `tests/integration/test_storage.py`

## Schema (design)
- `scrapes`: id, scraped_at (ISO), data_json (JSON), status, created_at
- `components`: id, scrape_id (FK), component_id, label, percent, raw_text, scraped_at
- `schema_migrations`: version, name, applied_at
- `retention_config`: single-row config (id=1) with `max_rows`, `retention_days`, `updated_at`

## Migrations
- Migration files are simple ordered SQL scripts under `src/scraper/migrations/`.
- `Storage.apply_migrations()` applies any migration not yet recorded in `schema_migrations`.
- Included migrations:
  - `0001_initial_schema.sql` — creates `scrapes` and `components`
  - `0002_retention_meta.sql` — creates `retention_config` table

## Usage
- Default DB path: `./scraper/data/usage.db`
- Override data directory with environment variable: `CLAUDE_SCRAPER_DATA_DIR` (directory containing `usage.db`)
- Programmatic API (in `src/scraper/storage.py`):
  - `Storage(db_path=None)`
  - `apply_migrations()`
  - `insert_scrape_result(result: dict, scraped_at: Optional[str]) -> int`
  - `get_scrape(id) -> dict`
  - `list_scrapes(limit) -> List[dict]`
  - `prune(retention_days=None, max_rows=None) -> int`
  - `close()`

## Scheduler integration
- `src/scraper/scheduler.py` now imports `Storage` and calls `Storage.insert_scrape_result(...)` on successful scrapes.
- If DB writes fail, the scheduler falls back to writing the JSON payload to the `DATA_DIR` as before.

## Migration instructions
- No external tooling required. Instantiating `Storage()` runs `apply_migrations()` automatically:
  ```py
  from src.scraper.storage import Storage
  s = Storage()
  ```
- Migrations are idempotent; they will only be applied once and are recorded in `schema_migrations`.

## Tests
- `tests/integration/test_storage.py` validates:
  - DB creation and that migrations were recorded
  - insert / get / list behavior
  - prune behavior (max_rows pruning)
- Run tests:
  - pytest tests/integration/test_storage.py

## Acceptance criteria status
- [x] Design SQLite schema for usage data (components table, raw_json table, retention metadata)
- [x] Implement persistence layer (CRUD + insert_scrape_result(result_json, scraped_at))
- [x] Add migration support (create DB and apply migrations; included at least one migration file)
- [x] Implement data retention policy config and an API to prune old records
- [x] Scheduler integration: scheduler saves each successful scrape via `storage.insert_scrape_result(...)`
- [x] Provide minimal docs/usage in this file with applied changes and migration instructions
- [x] Add tests that validate storage writes and migration path (create DB, run migrations, insert sample record, read back)

## Notes
- Concurrency: the storage connection uses `check_same_thread=False` and a `threading.Lock` to serialize access across threads. For higher throughput or multiple processes, consider a server DB (Postgres) or connection pooling.
- Future work: replace the simple SQL migration runner with Alembic if migration complexity grows.