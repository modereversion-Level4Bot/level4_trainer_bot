"""Repository for grammar training session state."""

from __future__ import annotations

import json
import sqlite3


def _dump_question_numbers(question_numbers: list[int]) -> str:
    return json.dumps(question_numbers)


def get_training_session_by_id(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
) -> sqlite3.Row | None:
    """Return training session by ID scoped to current user."""
    return conn.execute(
        """
        SELECT *
        FROM grammar_training_sessions
        WHERE id = ? AND user_id = ?
        """,
        (session_id, user_id),
    ).fetchone()


def upsert_training_session(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    topic_number: int,
    topic_type: str,
    source_page: int,
    question_numbers: list[int],
) -> sqlite3.Row:
    """Create a fresh active training session for user."""
    conn.execute(
        """
        DELETE FROM grammar_training_sessions
        WHERE user_id = ?
        """,
        (user_id,),
    )

    cursor = conn.execute(
        """
        INSERT INTO grammar_training_sessions (
            user_id,
            topic_number,
            topic_type,
            source_page,
            question_numbers_json,
            current_index,
            total_questions,
            correct_count,
            wrong_count,
            is_finished,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, 0, ?, 0, 0, 0, CURRENT_TIMESTAMP)
        """,
        (
            user_id,
            topic_number,
            topic_type,
            source_page,
            _dump_question_numbers(question_numbers),
            len(question_numbers),
        ),
    )

    session_id = int(cursor.lastrowid or 0)
    row = conn.execute(
        """
        SELECT *
        FROM grammar_training_sessions
        WHERE id = ?
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("Could not create grammar training session")
    return row


def update_training_session_progress(
    conn: sqlite3.Connection,
    *,
    session_id: int,
    current_index: int,
    correct_count: int,
    wrong_count: int,
    is_finished: bool,
) -> None:
    """Update session progress counters and index."""
    conn.execute(
        """
        UPDATE grammar_training_sessions
        SET
            current_index = ?,
            correct_count = ?,
            wrong_count = ?,
            is_finished = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            current_index,
            correct_count,
            wrong_count,
            int(is_finished),
            session_id,
        ),
    )
