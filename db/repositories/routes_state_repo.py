"""Routes repository helpers for route_user_state."""

from __future__ import annotations

import sqlite3

from db.repositories.routes_repo_common import (
    _normalize_is_active,
    _normalize_positive_int,
    _required_text,
)


def upsert_route_user_state(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
    phase: str,
    current_step_number: int | None,
    show_transcript: int,
    show_pilot_answer: int,
    show_ru_translation: int,
    entry_mode: str,
    is_active_session: int,
) -> None:
    """Insert or update route user runtime state for one route."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_phase = _required_text(phase, field_name="phase")
    normalized_entry_mode = _required_text(entry_mode, field_name="entry_mode")
    normalized_current_step = (
        None
        if current_step_number is None
        else _normalize_positive_int(current_step_number, field_name="current_step_number")
    )
    conn.execute(
        """
        INSERT INTO route_user_state (
            user_id,
            route_id,
            phase,
            current_step_number,
            selected_news_id,
            selected_block_id,
            current_question_number,
            show_transcript,
            show_pilot_answer,
            show_ru_translation,
            entry_mode,
            is_active_session,
            updated_at
        )
        VALUES (?, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, route_id) DO UPDATE SET
            phase = excluded.phase,
            current_step_number = excluded.current_step_number,
            selected_news_id = NULL,
            selected_block_id = NULL,
            current_question_number = NULL,
            show_transcript = excluded.show_transcript,
            show_pilot_answer = excluded.show_pilot_answer,
            show_ru_translation = excluded.show_ru_translation,
            entry_mode = excluded.entry_mode,
            is_active_session = excluded.is_active_session,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            normalized_user_id,
            normalized_route_id,
            normalized_phase,
            normalized_current_step,
            _normalize_is_active(show_transcript),
            _normalize_is_active(show_pilot_answer),
            _normalize_is_active(show_ru_translation),
            normalized_entry_mode,
            _normalize_is_active(is_active_session),
        ),
    )


def get_route_user_state(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
) -> dict[str, object] | None:
    """Get route runtime state for one user and route."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    row = conn.execute(
        """
        SELECT
            id,
            user_id,
            route_id,
            phase,
            current_step_number,
            selected_news_id,
            selected_block_id,
            current_question_number,
            show_transcript,
            show_pilot_answer,
            show_ru_translation,
            entry_mode,
            is_active_session,
            created_at,
            updated_at
        FROM route_user_state
        WHERE user_id = ?
          AND route_id = ?
        LIMIT 1
        """,
        (normalized_user_id, normalized_route_id),
    ).fetchone()
    return dict(row) if row is not None else None


def deactivate_active_route_sessions(
    conn: sqlite3.Connection,
    *,
    user_id: int,
) -> int:
    """Deactivate all active route sessions for user."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    result = conn.execute(
        """
        UPDATE route_user_state
        SET is_active_session = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
          AND COALESCE(is_active_session, 1) = 1
        """,
        (normalized_user_id,),
    )
    return int(result.rowcount or 0)


def clear_route_user_state(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
) -> int:
    """Deactivate route session and reset transient state fields."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    result = conn.execute(
        """
        UPDATE route_user_state
        SET phase = 'idle',
            current_step_number = NULL,
            selected_news_id = NULL,
            selected_block_id = NULL,
            current_question_number = NULL,
            show_transcript = 0,
            show_pilot_answer = 0,
            show_ru_translation = 0,
            is_active_session = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
          AND route_id = ?
        """,
        (normalized_user_id, normalized_route_id),
    )
    return int(result.rowcount or 0)


def update_route_step_state(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
    current_step_number: int,
    show_transcript: int,
    show_pilot_answer: int,
) -> int:
    """Update current scenario step and toggle states."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_step_number = _normalize_positive_int(
        current_step_number,
        field_name="current_step_number",
    )
    result = conn.execute(
        """
        UPDATE route_user_state
        SET current_step_number = ?,
            show_transcript = ?,
            show_pilot_answer = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
          AND route_id = ?
        """,
        (
            normalized_step_number,
            _normalize_is_active(show_transcript),
            _normalize_is_active(show_pilot_answer),
            normalized_user_id,
            normalized_route_id,
        ),
    )
    return int(result.rowcount or 0)


def upsert_route_news_state(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
    selected_news_id: int,
    show_transcript: int,
    entry_mode: str,
    is_active_session: int,
) -> None:
    """Set route_user_state to news phase."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_news_id = _normalize_positive_int(selected_news_id, field_name="selected_news_id")
    normalized_entry_mode = _required_text(entry_mode, field_name="entry_mode")
    conn.execute(
        """
        INSERT INTO route_user_state (
            user_id,
            route_id,
            phase,
            current_step_number,
            selected_news_id,
            selected_block_id,
            current_question_number,
            show_transcript,
            show_pilot_answer,
            show_ru_translation,
            entry_mode,
            is_active_session,
            updated_at
        )
        VALUES (?, ?, 'news', NULL, ?, NULL, NULL, ?, 0, 0, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, route_id) DO UPDATE SET
            phase = 'news',
            current_step_number = NULL,
            selected_news_id = excluded.selected_news_id,
            selected_block_id = NULL,
            current_question_number = NULL,
            show_transcript = excluded.show_transcript,
            show_pilot_answer = 0,
            show_ru_translation = 0,
            entry_mode = excluded.entry_mode,
            is_active_session = excluded.is_active_session,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            normalized_user_id,
            normalized_route_id,
            normalized_news_id,
            _normalize_is_active(show_transcript),
            normalized_entry_mode,
            _normalize_is_active(is_active_session),
        ),
    )


def update_route_news_transcript_state(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
    show_transcript: int,
) -> int:
    """Update news transcript toggle in route_user_state."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    result = conn.execute(
        """
        UPDATE route_user_state
        SET show_transcript = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
          AND route_id = ?
        """,
        (
            _normalize_is_active(show_transcript),
            normalized_user_id,
            normalized_route_id,
        ),
    )
    return int(result.rowcount or 0)


def upsert_route_questions_state(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
    selected_block_id: int,
    current_question_number: int,
    show_ru_translation: int,
    entry_mode: str,
    is_active_session: int,
) -> None:
    """Set route_user_state to questions phase."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(selected_block_id, field_name="selected_block_id")
    normalized_question_number = _normalize_positive_int(
        current_question_number,
        field_name="current_question_number",
    )
    normalized_entry_mode = _required_text(entry_mode, field_name="entry_mode")
    conn.execute(
        """
        INSERT INTO route_user_state (
            user_id,
            route_id,
            phase,
            current_step_number,
            selected_news_id,
            selected_block_id,
            current_question_number,
            show_transcript,
            show_pilot_answer,
            show_ru_translation,
            entry_mode,
            is_active_session,
            updated_at
        )
        VALUES (?, ?, 'questions', NULL, NULL, ?, ?, 0, 0, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, route_id) DO UPDATE SET
            phase = 'questions',
            current_step_number = NULL,
            selected_news_id = NULL,
            selected_block_id = excluded.selected_block_id,
            current_question_number = excluded.current_question_number,
            show_transcript = 0,
            show_pilot_answer = 0,
            show_ru_translation = excluded.show_ru_translation,
            entry_mode = excluded.entry_mode,
            is_active_session = excluded.is_active_session,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            normalized_user_id,
            normalized_route_id,
            normalized_block_id,
            normalized_question_number,
            _normalize_is_active(show_ru_translation),
            normalized_entry_mode,
            _normalize_is_active(is_active_session),
        ),
    )


def update_route_question_state(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
    current_question_number: int,
    show_ru_translation: int,
) -> int:
    """Update current route question position and RU translation toggle."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_question_number = _normalize_positive_int(
        current_question_number,
        field_name="current_question_number",
    )
    result = conn.execute(
        """
        UPDATE route_user_state
        SET current_question_number = ?,
            show_ru_translation = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
          AND route_id = ?
        """,
        (
            normalized_question_number,
            _normalize_is_active(show_ru_translation),
            normalized_user_id,
            normalized_route_id,
        ),
    )
    return int(result.rowcount or 0)
