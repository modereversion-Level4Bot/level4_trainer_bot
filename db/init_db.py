"""Database schema initialization."""

from __future__ import annotations

import logging
from pathlib import Path

from db.connection import get_connection, resolve_db_path


logger = logging.getLogger(__name__)
SCHEMA_DIR = Path(__file__).resolve().parent / "schema"


def _get_schema_files() -> list[Path]:
    files = sorted(SCHEMA_DIR.glob("*.sql"), key=lambda path: path.name)
    if not files:
        raise FileNotFoundError(f"No schema files found in {SCHEMA_DIR}")
    return files


def _ensure_migrations_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _is_schema_applied(conn, filename: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM schema_migrations
        WHERE filename = ?
        """,
        (filename,),
    ).fetchone()
    return row is not None


def _mark_schema_applied(conn, filename: str) -> None:
    conn.execute(
        """
        INSERT INTO schema_migrations (filename)
        VALUES (?)
        """,
        (filename,),
    )


def init_db() -> None:
    """Apply all SQL schema files in lexicographical order."""
    schema_files = _get_schema_files()
    logger.info("Initializing DB at %s", resolve_db_path())

    with get_connection() as conn:
        _ensure_migrations_table(conn)
        for schema_file in schema_files:
            if _is_schema_applied(conn, schema_file.name):
                logger.info("Skipped schema (already applied): %s", schema_file.name)
                continue
            sql = schema_file.read_text(encoding="utf-8")
            try:
                conn.executescript(sql)
                _mark_schema_applied(conn, schema_file.name)
                logger.info("Applied schema: %s", schema_file.name)
            except Exception:
                logger.exception("Failed to apply schema: %s", schema_file.name)
                raise


def main() -> None:
    init_db()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
