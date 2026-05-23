import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from config import SQLITE_PATH

# Maximum records returned by recent_runs to prevent memory bloat
DEFAULT_CONTEXT_LIMIT = 50


class MemoryStore:
    def __init__(self, db_path: str = SQLITE_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source TEXT NOT NULL,
                verdict TEXT NOT NULL,
                priority TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source TEXT NOT NULL,
                note TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def save_run(self, source: str, verdict: str, priority: str, payload: Dict[str, Any]):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO runs (created_at, source, verdict, priority, payload_json) VALUES (?, ?, ?, ?, ?)",
            (
                datetime.utcnow().isoformat(timespec="seconds"),
                source,
                verdict,
                priority,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        conn.commit()
        conn.close()

    def save_note(self, source: str, note: str):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO notes (created_at, source, note) VALUES (?, ?, ?)",
            (datetime.utcnow().isoformat(timespec="seconds"), source, note),
        )
        conn.commit()
        conn.close()

    def recent_runs(self, limit: int = DEFAULT_CONTEXT_LIMIT) -> List[Dict[str, Any]]:
        """
        Returns recent runs up to `limit` records.
        Default capped at DEFAULT_CONTEXT_LIMIT to prevent unbounded memory growth
        when called without an explicit limit in long-running agent sessions.
        """
        # Clamp limit to prevent accidental full-table scans
        safe_limit = min(limit, DEFAULT_CONTEXT_LIMIT)
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT created_at, source, verdict, priority, payload_json FROM runs ORDER BY id DESC LIMIT ?",
            (safe_limit,),
        )
        rows = cur.fetchall()
        conn.close()

        return [
            {
                "created_at": created_at,
                "source": source,
                "verdict": verdict,
                "priority": priority,
                "payload": json.loads(payload_json),
            }
            for created_at, source, verdict, priority, payload_json in rows
        ]

    def close(self):
        """No-op for interface compatibility. Connections are closed per-operation."""
        pass
