"""Small SQLite persistence layer for recent files and operation history."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from contextlib import contextmanager
from typing import Iterator


class AppDatabase:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS recent_files (
                    path TEXT PRIMARY KEY, last_opened TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, operation TEXT NOT NULL,
                    success INTEGER NOT NULL, message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path)
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def add_recent_file(self, path: str | Path, limit: int = 20) -> None:
        with self.connection() as db:
            db.execute("INSERT INTO recent_files(path) VALUES (?) ON CONFLICT(path) DO UPDATE SET last_opened=CURRENT_TIMESTAMP", (str(Path(path)),))
            db.execute("DELETE FROM recent_files WHERE path NOT IN (SELECT path FROM recent_files ORDER BY last_opened DESC LIMIT ?)", (limit,))

    def recent_files(self) -> list[str]:
        with self.connection() as db:
            return [row[0] for row in db.execute("SELECT path FROM recent_files ORDER BY last_opened DESC")]

    def record_operation(self, operation: str, success: bool, message: str) -> None:
        with self.connection() as db:
            db.execute("INSERT INTO operations(operation, success, message) VALUES (?, ?, ?)", (operation, int(success), message))

    def operation_history(self, limit: int = 100) -> list[tuple[str, bool, str, str]]:
        with self.connection() as db:
            return [(row[0], bool(row[1]), row[2], row[3]) for row in db.execute("SELECT operation, success, message, created_at FROM operations ORDER BY id DESC LIMIT ?", (limit,))]
