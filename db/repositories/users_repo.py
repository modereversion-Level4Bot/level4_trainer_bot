"""Repository for users and onboarding profile records."""

from __future__ import annotations

import sqlite3
from typing import Any
from telegram import User


ONBOARDING_COLUMN_ALIASES = {
    "language": "interface_language",
}

ONBOARDING_ALLOWED_COLUMNS = {
    "interface_language",
    "timezone",
    "daily_tips_enabled",
    "daily_tip_time",
    "training_reminders_enabled",
    "training_reminder_time",
    "sound_enabled",
    "onboarding_completed",
    "onboarding_step",
    "waiting_state",
}


def _adapt_value(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    return value


def _ensure_related_rows(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        """
        INSERT INTO user_settings (user_id)
        VALUES (?)
        ON CONFLICT(user_id) DO NOTHING
        """,
        (user_id,),
    )
    conn.execute(
        """
        INSERT INTO user_message_state (user_id)
        VALUES (?)
        ON CONFLICT(user_id) DO NOTHING
        """,
        (user_id,),
    )
    conn.execute(
        """
        INSERT INTO user_onboarding_state (user_id)
        VALUES (?)
        ON CONFLICT(user_id) DO NOTHING
        """,
        (user_id,),
    )


def _select_user_with_onboarding(
    conn: sqlite3.Connection,
    where_clause: str,
    params: tuple[Any, ...],
) -> sqlite3.Row | None:
    row = conn.execute(
        f"""
        SELECT
            u.*,
            o.interface_language,
            o.timezone,
            o.daily_tips_enabled,
            o.daily_tip_time,
            o.training_reminders_enabled,
            o.training_reminder_time,
            o.sound_enabled,
            o.onboarding_completed,
            o.onboarding_step,
            o.waiting_state
        FROM users u
        LEFT JOIN user_onboarding_state o ON o.user_id = u.id
        WHERE {where_clause}
        """,
        params,
    ).fetchone()
    if row is None:
        return None

    _ensure_related_rows(conn, user_id=row["id"])
    return conn.execute(
        f"""
        SELECT
            u.*,
            o.interface_language,
            o.timezone,
            o.daily_tips_enabled,
            o.daily_tip_time,
            o.training_reminders_enabled,
            o.training_reminder_time,
            o.sound_enabled,
            o.onboarding_completed,
            o.onboarding_step,
            o.waiting_state
        FROM users u
        LEFT JOIN user_onboarding_state o ON o.user_id = u.id
        WHERE {where_clause}
        """,
        params,
    ).fetchone()


def upsert_user(conn: sqlite3.Connection, telegram_user: User) -> sqlite3.Row | None:
    """Insert or update user by Telegram ID."""
    conn.execute(
        """
        INSERT INTO users (
            telegram_id,
            username,
            first_name,
            last_name,
            language_code,
            is_bot,
            last_activity_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            language_code = excluded.language_code,
            is_bot = excluded.is_bot,
            updated_at = CURRENT_TIMESTAMP,
            last_activity_at = CURRENT_TIMESTAMP
        """,
        (
            telegram_user.id,
            telegram_user.username,
            telegram_user.first_name,
            telegram_user.last_name,
            telegram_user.language_code,
            int(telegram_user.is_bot),
        ),
    )

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_user.id,),
    ).fetchone()

    if row is not None:
        _ensure_related_rows(conn, user_id=row["id"])
    return row


def get_user_by_telegram_id(
    conn: sqlite3.Connection,
    telegram_id: int,
) -> sqlite3.Row | None:
    """Fetch user by Telegram ID."""
    return conn.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    ).fetchone()


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    """Fetch user by internal ID."""
    return conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()


def get_user_with_onboarding_by_telegram_id(
    conn: sqlite3.Connection,
    telegram_id: int,
) -> sqlite3.Row | None:
    """Fetch user with onboarding state by Telegram ID."""
    return _select_user_with_onboarding(
        conn=conn,
        where_clause="u.telegram_id = ?",
        params=(telegram_id,),
    )


def get_user_with_onboarding_by_user_id(
    conn: sqlite3.Connection,
    user_id: int,
) -> sqlite3.Row | None:
    """Fetch user with onboarding state by internal user ID."""
    return _select_user_with_onboarding(
        conn=conn,
        where_clause="u.id = ?",
        params=(user_id,),
    )


def update_onboarding_settings(
    conn: sqlite3.Connection,
    user_id: int,
    **fields: Any,
) -> None:
    """Update onboarding state fields for user."""
    if not fields:
        return

    normalized_fields: dict[str, Any] = {}
    for key, value in fields.items():
        column_name = ONBOARDING_COLUMN_ALIASES.get(key, key)
        if column_name not in ONBOARDING_ALLOWED_COLUMNS:
            raise ValueError(f"Unsupported onboarding field: {key}")
        normalized_fields[column_name] = _adapt_value(value)

    _ensure_related_rows(conn, user_id=user_id)
    assignments = ", ".join([f"{column} = ?" for column in normalized_fields])
    values = list(normalized_fields.values()) + [user_id]
    conn.execute(
        f"""
        UPDATE user_onboarding_state
        SET {assignments},
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        values,
    )


def apply_default_onboarding_settings(conn: sqlite3.Connection, user_id: int) -> None:
    """Apply default onboarding configuration (UTC+3 + tips/reminders at 21:00)."""
    update_onboarding_settings(
        conn=conn,
        user_id=user_id,
        timezone="Europe/Moscow UTC+3",
        daily_tips_enabled=True,
        daily_tip_time="21:00",
        training_reminders_enabled=True,
        training_reminder_time="21:00",
        sound_enabled=True,
        onboarding_step="final",
        waiting_state=None,
    )


def delete_user_account(conn: sqlite3.Connection, user_id: int) -> bool:
    """Delete user account and related rows via FK cascade."""
    cursor = conn.execute(
        """
        DELETE FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    return cursor.rowcount > 0
