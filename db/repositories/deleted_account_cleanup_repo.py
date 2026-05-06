"""Repository helpers for cleanup after account deletion."""

from __future__ import annotations

import sqlite3


def upsert_deleted_account_cleanup(
    conn: sqlite3.Connection,
    *,
    telegram_id: int,
    chat_id: int,
    message_id: int,
) -> None:
    """Store message id that should be removed on next /start."""
    conn.execute(
        """
        INSERT INTO deleted_account_cleanup (
            telegram_id,
            chat_id,
            message_id,
            created_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(telegram_id, chat_id) DO UPDATE SET
            message_id = excluded.message_id,
            created_at = CURRENT_TIMESTAMP
        """,
        (telegram_id, chat_id, message_id),
    )


def get_deleted_account_cleanup_message_id(
    conn: sqlite3.Connection,
    *,
    telegram_id: int,
    chat_id: int,
) -> int | None:
    """Return pending cleanup message id for user/chat."""
    row = conn.execute(
        """
        SELECT message_id
        FROM deleted_account_cleanup
        WHERE telegram_id = ? AND chat_id = ?
        """,
        (telegram_id, chat_id),
    ).fetchone()
    if row is None:
        return None
    return int(row["message_id"])


def delete_deleted_account_cleanup(
    conn: sqlite3.Connection,
    *,
    telegram_id: int,
    chat_id: int,
) -> None:
    """Delete pending cleanup marker."""
    conn.execute(
        """
        DELETE FROM deleted_account_cleanup
        WHERE telegram_id = ? AND chat_id = ?
        """,
        (telegram_id, chat_id),
    )
