import os
import sqlite3
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATA_DIR_ENV = "CLAUDE_SCRAPER_DATA_DIR"
DEFAULT_DATA_DIR = "./scraper/data"
MIGRATIONS_DIRNAME = "migrations"


class Storage:
    """
    Simple SQLite-backed storage with file-based migrations.

    Provides:
      - apply_migrations()
      - insert_scrape_result(result, scraped_at=None) -> int
      - get_scrape(scrape_id) -> dict|None
      - list_scrapes(limit=100) -> List[dict]
      - prune(retention_days=None, max_rows=None) -> int (rows deleted)
      - close()
    """

    def __init__(self, db_path: Optional[str] = None):
        data_dir = os.environ.get(DATA_DIR_ENV, DEFAULT_DATA_DIR)
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = db_path or os.path.join(data_dir, "usage.db")
        self._lock = threading.Lock()
        # Use check_same_thread=False so callers from scheduler threads can share this connection safely;
        # we still serialize access with a lock.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            cur = self._conn.cursor()
            # Tunable pragmas for acceptable concurrency and durability for a local SQLite DB.
            try:
                cur.execute("PRAGMA journal_mode=WAL;")
            except Exception:
                pass
            try:
                cur.execute("PRAGMA synchronous=NORMAL;")
            except Exception:
                pass
            cur.close()
        # Ensure migrations/tables exist on init
        self.apply_migrations()

    def apply_migrations(self) -> None:
        """
        Apply .sql files from the migrations directory in ascending numeric order.
        Migration files must be named like: 0001_description.sql
        Creates schema_migrations to track applied versions.
        """
        migrations_dir = os.path.join(os.path.dirname(__file__), MIGRATIONS_DIRNAME)
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT, applied_at TEXT)"
            )
            cur.execute("SELECT MAX(version) as v FROM schema_migrations")
            row = cur.fetchone()
            current = int(row["v"]) if row and row["v"] is not None else 0
            if not os.path.isdir(migrations_dir):
                cur.close()
                return
            files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
            for fname in files:
                try:
                    version = int(fname.split("_")[0])
                except Exception:
                    # Skip non-conforming filenames
                    continue
                if version <= current:
                    continue
                path = os.path.join(migrations_dir, fname)
                with open(path, "r", encoding="utf-8") as fh:
                    sql = fh.read()
                # executescript allows multi-statement SQL files
                cur.executescript(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    (version, fname, datetime.utcnow().isoformat() + "Z"),
                )
                self._conn.commit()
            cur.close()

    def insert_scrape_result(self, result: Any, scraped_at: Optional[str] = None) -> int:
        """
        Insert a scrape result. `result` may be a dict (recommended) or a JSON string.
        Returns the inserted scrape id.
        """
        if isinstance(result, dict):
            data_json = json.dumps(result, ensure_ascii=False)
            payload = result.get("payload", {})
        else:
            data_json = str(result)
            try:
                payload = json.loads(result)
            except Exception:
                payload = {}
        scraped_at = (
            scraped_at
            or (result.get("collected_at") if isinstance(result, dict) else None)
            or (datetime.utcnow().isoformat() + "Z")
        )
        status = payload.get("status") if isinstance(payload, dict) else None

        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "INSERT INTO scrapes (scraped_at, data_json, status, created_at) VALUES (?, ?, ?, ?)",
                (scraped_at, data_json, status, datetime.utcnow().isoformat() + "Z"),
            )
            scrape_id = cur.lastrowid
            # Attempt to insert component-level rows if available (best-effort)
            try:
                components = payload.get("components", []) if isinstance(payload, dict) else []
                for comp in components:
                    cur.execute(
                        "INSERT INTO components (scrape_id, component_id, label, percent, raw_text, scraped_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            scrape_id,
                            comp.get("component_id"),
                            comp.get("label"),
                            comp.get("percent"),
                            comp.get("raw_text"),
                            comp.get("scraped_at"),
                        ),
                    )
            except Exception:
                # Do not fail the main insert on component storage errors
                pass
            self._conn.commit()
            cur.close()
        return scrape_id

    def get_scrape(self, scrape_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT id, scraped_at, data_json, status, created_at FROM scrapes WHERE id = ?", (scrape_id,))
            row = cur.fetchone()
            cur.close()
        if not row:
            return None
        try:
            data = json.loads(row["data_json"])
        except Exception:
            data = row["data_json"]
        return {"id": row["id"], "scraped_at": row["scraped_at"], "data": data, "status": row["status"], "created_at": row["created_at"]}

    def list_scrapes(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT id, scraped_at, data_json, status, created_at FROM scrapes ORDER BY scraped_at DESC LIMIT ?", (limit,))
            rows = cur.fetchall()
            cur.close()
        out = []
        for row in rows:
            try:
                data = json.loads(row["data_json"])
            except Exception:
                data = row["data_json"]
            out.append({"id": row["id"], "scraped_at": row["scraped_at"], "data": data, "status": row["status"], "created_at": row["created_at"]})
        return out

    def prune(self, retention_days: Optional[int] = None, max_rows: Optional[int] = None) -> int:
        """
        Prune old records.
        - retention_days: remove scrapes older than this many days (based on scraped_at)
        - max_rows: keep only the newest `max_rows` scrapes, delete the rest.
        Returns number of rows deleted (approximate; sum of deletes executed).
        """
        deleted = 0
        with self._lock:
            cur = self._conn.cursor()
            if retention_days is not None:
                cutoff = (datetime.utcnow() - timedelta(days=retention_days)).isoformat() + "Z"
                cur.execute("DELETE FROM components WHERE scrape_id IN (SELECT id FROM scrapes WHERE scraped_at < ?)", (cutoff,))
                cur.execute("DELETE FROM scrapes WHERE scraped_at < ?", (cutoff,))
                deleted += cur.rowcount
            if max_rows is not None:
                # Delete older rows keeping newest max_rows by scraped_at
                # SQLite supports LIMIT with OFFSET only in subselects on newer versions; using a NOT IN approach
                cur.execute(
                    "DELETE FROM components WHERE scrape_id IN (SELECT id FROM scrapes ORDER BY scraped_at DESC LIMIT -1 OFFSET ?)",
                    (max_rows,),
                )
                cur.execute(
                    "DELETE FROM scrapes WHERE id IN (SELECT id FROM scrapes ORDER BY scraped_at DESC LIMIT -1 OFFSET ?)",
                    (max_rows,),
                )
                deleted += cur.rowcount
            self._conn.commit()
            cur.close()
        return deleted

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass