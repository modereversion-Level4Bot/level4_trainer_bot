"""Repository for runtime bot settings."""

from __future__ import annotations

import sqlite3
from typing import Any

from core.constants import MAINTENANCE_MODE_KEY


SETTINGS_ALLOWED_FIELDS = {
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


def get_setting(
    conn: sqlite3.Connection,
    key: str,
    default: str | None = None,
) -> str | None:
    row = conn.execute(
        "SELECT value FROM bot_settings WHERE key = ?",
        (key,),
    ).fetchone()
    return row["value"] if row else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO bot_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
        """,
        (key, value),
    )


def is_maintenance_mode(conn: sqlite3.Connection) -> bool:
    value = get_setting(conn, MAINTENANCE_MODE_KEY, default="0")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _update_onboarding_fields(
    conn: sqlite3.Connection,
    user_id: int,
    fields: dict[str, Any],
) -> None:
    if not fields:
        return

    assignments = ", ".join([f"{key} = ?" for key in fields])
    params = list(fields.values()) + [user_id]
    conn.execute(
        f"""
        UPDATE user_onboarding_state
        SET {assignments},
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        params,
    )


def update_settings_fields(
    conn: sqlite3.Connection,
    user_id: int,
    **fields: Any,
) -> None:
    """Update settings fields stored in onboarding state."""
    if not fields:
        return

    normalized: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in SETTINGS_ALLOWED_FIELDS:
            raise ValueError(f"Unsupported settings field: {key}")
        normalized[key] = int(value) if isinstance(value, bool) else value

    _update_onboarding_fields(conn, user_id, normalized)


def restart_onboarding(conn: sqlite3.Connection, user_id: int) -> None:
    """Prepare onboarding state for full restart while preserving progress."""
    update_settings_fields(
        conn,
        user_id,
        onboarding_completed=False,
        onboarding_step="language_select",
        waiting_state=None,
    )
