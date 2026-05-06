"""Progress and runtime state repository for Questions feature."""

from __future__ import annotations

import sqlite3


def _validate_level(level: int) -> int:
    normalized = int(level)
    if normalized not in {4, 5}:
        raise RuntimeError("level must be 4 or 5")
    return normalized


def _validate_question_number(question_number: int) -> int:
    normalized = int(question_number)
    if normalized <= 0:
        raise RuntimeError("question_number must be positive integer")
    return normalized


def mark_question_completed(
    conn: sqlite3.Connection,
    user_id: int,
    level: int,
    question_number: int,
) -> None:
    """Mark one level question as completed (idempotent)."""
    normalized_level = _validate_level(level)
    normalized_question_number = _validate_question_number(question_number)
    conn.execute(
        """
        INSERT INTO exam_question_progress (
            user_id,
            level,
            question_number,
            completed_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, level, question_number) DO UPDATE SET
            completed_at = CURRENT_TIMESTAMP
        """,
        (user_id, normalized_level, normalized_question_number),
    )


def is_question_completed(
    conn: sqlite3.Connection,
    user_id: int,
    level: int,
    question_number: int,
) -> bool:
    """Check if question is completed for user."""
    normalized_level = _validate_level(level)
    normalized_question_number = _validate_question_number(question_number)
    row = conn.execute(
        """
        SELECT 1
        FROM exam_question_progress
        WHERE user_id = ?
          AND level = ?
          AND question_number = ?
        LIMIT 1
        """,
        (user_id, normalized_level, normalized_question_number),
    ).fetchone()
    return row is not None


def count_completed_questions_by_level(
    conn: sqlite3.Connection,
    user_id: int,
    level: int,
) -> int:
    """Count completed questions for user by level."""
    normalized_level = _validate_level(level)
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM exam_question_progress
        WHERE user_id = ?
          AND level = ?
        """,
        (user_id, normalized_level),
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def set_current_question(
    conn: sqlite3.Connection,
    user_id: int,
    level: int,
    question_number: int | None,
) -> None:
    """Set current question number for one level."""
    normalized_level = _validate_level(level)
    normalized_question_number = (
        _validate_question_number(question_number) if question_number is not None else None
    )
    conn.execute(
        """
        INSERT INTO exam_question_state (
            user_id,
            level,
            current_question_number,
            updated_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, level) DO UPDATE SET
            current_question_number = excluded.current_question_number,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, normalized_level, normalized_question_number),
    )


def get_current_question_number(conn: sqlite3.Connection, user_id: int, level: int) -> int | None:
    """Get current question number for one level."""
    normalized_level = _validate_level(level)
    row = conn.execute(
        """
        SELECT current_question_number
        FROM exam_question_state
        WHERE user_id = ?
          AND level = ?
        LIMIT 1
        """,
        (user_id, normalized_level),
    ).fetchone()
    if row is None:
        return None
    raw_value = row["current_question_number"]
    return int(raw_value) if raw_value is not None else None


def set_last_audio_message_id(
    conn: sqlite3.Connection,
    user_id: int,
    level: int,
    message_id: int | None,
) -> None:
    """Legacy helper: set last audio message id in exam_question_state."""
    normalized_level = _validate_level(level)
    normalized_message_id = int(message_id) if message_id is not None else None
    conn.execute(
        """
        INSERT INTO exam_question_state (
            user_id,
            level,
            last_audio_message_id,
            updated_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, level) DO UPDATE SET
            last_audio_message_id = excluded.last_audio_message_id,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, normalized_level, normalized_message_id),
    )


def get_last_audio_message_id(conn: sqlite3.Connection, user_id: int, level: int) -> int | None:
    """Legacy helper: get last audio message id from exam_question_state."""
    normalized_level = _validate_level(level)
    row = conn.execute(
        """
        SELECT last_audio_message_id
        FROM exam_question_state
        WHERE user_id = ?
          AND level = ?
        LIMIT 1
        """,
        (user_id, normalized_level),
    ).fetchone()
    if row is None:
        return None
    raw_value = row["last_audio_message_id"]
    return int(raw_value) if raw_value is not None else None


def clear_last_audio_message_id(conn: sqlite3.Connection, user_id: int, level: int) -> None:
    """Legacy helper: clear last audio message id in exam_question_state."""
    normalized_level = _validate_level(level)
    conn.execute(
        """
        UPDATE exam_question_state
        SET last_audio_message_id = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
          AND level = ?
        """,
        (user_id, normalized_level),
    )


def reset_questions_progress(conn: sqlite3.Connection, user_id: int) -> None:
    """Clear completed Questions progress for user."""
    conn.execute(
        """
        DELETE FROM exam_question_progress
        WHERE user_id = ?
        """,
        (user_id,),
    )


def reset_all_questions_state(conn: sqlite3.Connection, user_id: int) -> None:
    """Clear runtime Questions state for user."""
    conn.execute(
        """
        DELETE FROM exam_question_state
        WHERE user_id = ?
        """,
        (user_id,),
    )
