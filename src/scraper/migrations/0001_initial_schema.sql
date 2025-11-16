-- 0001_initial_schema.sql
-- Initial schema: scrapes table and components table

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS scrapes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scraped_at TEXT NOT NULL,
    data_json TEXT NOT NULL,
    status TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scrapes_scraped_at ON scrapes (scraped_at);

CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scrape_id INTEGER NOT NULL REFERENCES scrapes(id) ON DELETE CASCADE,
    component_id TEXT,
    label TEXT,
    percent REAL,
    raw_text TEXT,
    scraped_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_components_scrape_id ON components (scrape_id);

COMMIT;