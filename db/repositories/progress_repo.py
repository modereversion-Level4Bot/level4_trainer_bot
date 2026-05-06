"""User progress repository."""

from __future__ import annotations

import sqlite3

from db.repositories.questions_progress_repo import (
    reset_all_questions_state as reset_questions_runtime_state,
    reset_questions_progress as reset_questions_completed_progress,
)
from db.repositories.temporary_messages_repo import clear_temp_messages


def reset_grammar_progress(conn: sqlite3.Connection, user_id: int) -> None:
    """Delete grammar progress and active training records for a user."""
    conn.execute(
        """
        DELETE FROM grammar_progress
        WHERE user_id = ?
        """,
        (user_id,),
    )
    conn.execute(
        """
        DELETE FROM grammar_training_sessions
        WHERE user_id = ?
        """,
        (user_id,),
    )


def reset_questions_progress(conn: sqlite3.Connection, user_id: int) -> None:
    """Delete exam questions progress and runtime state records for a user."""
    reset_questions_completed_progress(conn, user_id)
    reset_questions_runtime_state(conn, user_id)
    clear_temp_messages(
        conn,
        user_id=user_id,
        feature="questions",
        message_type="audio",
    )


def reset_routes_progress(conn: sqlite3.Connection, user_id: int) -> None:
    """Delete routes progress records for a user."""
    conn.execute(
        """
        DELETE FROM route_progress
        WHERE user_id = ?
        """,
        (user_id,),
    )


def reset_all_progress(conn: sqlite3.Connection, user_id: int) -> None:
    """Delete all learning progress records for a user."""
    reset_grammar_progress(conn, user_id)
    reset_questions_progress(conn, user_id)
    reset_routes_progress(conn, user_id)
