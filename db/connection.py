"""SQLite connection helpers."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
import os
from typing import Iterator

from config import BASE_DIR


def resolve_db_path() -> Path:
    """Resolve DB path from settings and ensure parent directory exists."""
    db_path = Path(os.getenv("DB_PATH", "level4_trainer.db"))
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a safe SQLite connection with Row factory."""
    db_path = resolve_db_path()
    connection = sqlite3.connect(db_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
