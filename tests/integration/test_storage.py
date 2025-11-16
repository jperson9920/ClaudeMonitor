import os
import sqlite3
import json
from datetime import datetime, timedelta
from src.scraper.storage import Storage


def test_storage_create_migrate_insert_query_prune(tmp_path, monkeypatch):
    # Point storage to a temporary data dir
    data_dir = tmp_path / "scraper_data"
    monkeypatch.setenv("CLAUDE_SCRAPER_DATA_DIR", str(data_dir))
    os.makedirs(str(data_dir), exist_ok=True)

    # Initialize storage (should create DB and apply migrations)
    s = Storage()
    assert os.path.exists(s.db_path), "DB file should be created"

    # Verify migrations table exists and at least one migration applied
    conn = sqlite3.connect(s.db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
    assert cur.fetchone() is not None, "schema_migrations table should exist"
    cur.execute("SELECT COUNT(1) FROM schema_migrations")
    row = cur.fetchone()
    assert row is not None and row[0] >= 1, "At least one migration should be recorded"
    cur.close()
    conn.close()

    # Initially no scrapes
    assert s.list_scrapes(limit=10) == []

    # Insert a sample scrape record
    now_iso = datetime.utcnow().isoformat() + "Z"
    sample = {
        "collected_at": now_iso,
        "payload": {
            "components": [
                {
                    "component_id": "current_session",
                    "label": "Current session",
                    "percent": 12.5,
                    "raw_text": "12% used",
                    "scraped_at": now_iso,
                }
            ],
            "status": "ok",
        },
    }
    sid = s.insert_scrape_result(sample)
    assert isinstance(sid, int) and sid > 0

    # Read back the record
    rec = s.get_scrape(sid)
    assert rec is not None
    assert rec["id"] == sid
    assert rec["status"] == "ok" or rec["data"].get("payload", {}).get("status") == "ok"
    assert "data" in rec

    # list_scrapes should return at least the inserted record
    items = s.list_scrapes(limit=10)
    assert any(i["id"] == sid for i in items), "Inserted scrape should appear in list_scrapes"

    # Prune using max_rows=0 should remove all rows
    deleted = s.prune(max_rows=0)
    # After pruning, ensure no scrapes remain
    remaining = s.list_scrapes(limit=10)
    assert remaining == [], f"All scrapes should be pruned, remaining: {remaining}"

    s.close()