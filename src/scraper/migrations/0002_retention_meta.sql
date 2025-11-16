-- 0002_retention_meta.sql
-- Add a simple retention metadata table to store configuration (max_rows, retention_days)

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS retention_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    max_rows INTEGER,
    retention_days INTEGER,
    updated_at TEXT
);

-- Ensure single row exists
INSERT OR IGNORE INTO retention_config (id, max_rows, retention_days, updated_at) VALUES (1, NULL, NULL, datetime('now'));

COMMIT;