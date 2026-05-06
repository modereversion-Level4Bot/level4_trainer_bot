"""Repository for temporary Telegram messages."""

from __future__ import annotations

import sqlite3


def add_temp_message(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    chat_id: int,
    message_id: int,
    feature: str,
    message_type: str,
    scope: str | None = None,
) -> int:
    """Insert one temporary message record and return record id."""
    cursor = conn.execute(
        """
        INSERT INTO temporary_messages (
            user_id,
            chat_id,
            message_id,
            feature,
            message_type,
            scope,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            int(user_id),
            int(chat_id),
            int(message_id),
            str(feature).strip(),
            str(message_type).strip(),
            (scope or "").strip() or None,
        ),
    )
    return int(cursor.lastrowid)


def list_temp_messages(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    feature: str | None = None,
    message_type: str | None = None,
) -> list[dict[str, object]]:
    """List temporary messages for user with optional filters."""
    where_clauses = ["user_id = ?"]
    params: list[object] = [int(user_id)]

    normalized_feature = (feature or "").strip()
    if normalized_feature:
        where_clauses.append("feature = ?")
        params.append(normalized_feature)

    normalized_message_type = (message_type or "").strip()
    if normalized_message_type:
        where_clauses.append("message_type = ?")
        params.append(normalized_message_type)

    where_sql = " AND ".join(where_clauses)
    rows = conn.execute(
        f"""
        SELECT
            id,
            user_id,
            chat_id,
            message_id,
            feature,
            message_type,
            scope,
            created_at
        FROM temporary_messages
        WHERE {where_sql}
        ORDER BY id ASC
        """,
        tuple(params),
    ).fetchall()
    return [dict(row) for row in rows]


def list_temp_messages_by_feature(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    feature: str,
) -> list[dict[str, object]]:
    """List temporary messages by user and feature."""
    return list_temp_messages(conn, user_id=user_id, feature=feature)


def delete_temp_message_record(
    conn: sqlite3.Connection,
    *,
    record_id: int | None = None,
    message_id: int | None = None,
) -> None:
    """Delete temporary message by record id or by Telegram message id."""
    if record_id is not None:
        conn.execute(
            """
            DELETE FROM temporary_messages
            WHERE id = ?
            """,
            (int(record_id),),
        )
        return

    if message_id is not None:
        conn.execute(
            """
            DELETE FROM temporary_messages
            WHERE message_id = ?
            """,
            (int(message_id),),
        )
        return

    raise ValueError("Either record_id or message_id must be provided")


def clear_temp_messages(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    feature: str | None = None,
    message_type: str | None = None,
) -> None:
    """Clear temporary message records for user with optional filters."""
    where_clauses = ["user_id = ?"]
    params: list[object] = [int(user_id)]

    normalized_feature = (feature or "").strip()
    if normalized_feature:
        where_clauses.append("feature = ?")
        params.append(normalized_feature)

    normalized_message_type = (message_type or "").strip()
    if normalized_message_type:
        where_clauses.append("message_type = ?")
        params.append(normalized_message_type)

    where_sql = " AND ".join(where_clauses)
    conn.execute(
        f"""
        DELETE FROM temporary_messages
        WHERE {where_sql}
        """,
        tuple(params),
    )
