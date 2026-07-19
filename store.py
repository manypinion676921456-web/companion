"""
Companion's memory store.

v1 scope: persistent conversation history per session, stored in SQLite
so it survives restarts. This is deliberately simple — no vector search,
no global cache yet. Those get built as separate modules later
(core/retrieval/) once this foundation is solid.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "companion_memory.db"


class MemoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    def add_message(self, session_id: str, role: str, content: str):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, role, content, datetime.now(timezone.utc).isoformat()),
            )

    def get_history(self, session_id: str, limit: int = 20) -> list[dict]:
        """Returns the last `limit` messages for a session, oldest first,
        formatted for direct use as Avcore chat history."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT role, content FROM messages
                   WHERE session_id = ?
                   ORDER BY id DESC LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        rows.reverse()
        return [{"role": role, "content": content} for role, content in rows]

    def clear_session(self, session_id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
