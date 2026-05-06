"""Exam questions repository."""

from __future__ import annotations

import sqlite3


_QUESTION_COLUMNS = """
    id,
    level,
    question_number,
    question_en,
    audio_file,
    question_translation_ru,
    sample_answer_en,
    sample_answer_translation_ru,
    is_active,
    created_at,
    updated_at
"""


def _validate_level(level: int) -> int:
    normalized = int(level)
    if normalized not in {4, 5}:
        raise RuntimeError("level must be 4 or 5")
    return normalized


def _validate_positive_number(value: int, *, field_name: str) -> int:
    normalized = int(value)
    if normalized <= 0:
        raise RuntimeError(f"{field_name} must be positive integer")
    return normalized


def _required_text(value: str, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"{field_name} is required")
    return normalized


def _optional_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def upsert_question(
    conn: sqlite3.Connection,
    *,
    level: int,
    question_number: int,
    question_en: str,
    audio_file: str | None,
    question_translation_ru: str | None,
    sample_answer_en: str | None,
    sample_answer_translation_ru: str | None,
) -> None:
    """Insert or update one question by stable (level, question_number)."""
    normalized_level = _validate_level(level)
    normalized_question_number = _validate_positive_number(
        question_number,
        field_name="question_number",
    )
    normalized_question_en = _required_text(question_en, field_name="question_en")

    conn.execute(
        """
        INSERT INTO exam_questions (
            level,
            question_number,
            question_en,
            audio_file,
            question_translation_ru,
            sample_answer_en,
            sample_answer_translation_ru,
            is_active,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(level, question_number) DO UPDATE SET
            question_en = excluded.question_en,
            audio_file = excluded.audio_file,
            question_translation_ru = excluded.question_translation_ru,
            sample_answer_en = excluded.sample_answer_en,
            sample_answer_translation_ru = excluded.sample_answer_translation_ru,
            is_active = 1,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            normalized_level,
            normalized_question_number,
            normalized_question_en,
            _optional_text(audio_file),
            _optional_text(question_translation_ru),
            _optional_text(sample_answer_en),
            _optional_text(sample_answer_translation_ru),
        ),
    )


def count_active_exam_questions(conn: sqlite3.Connection) -> int:
    """Count active exam questions (used by main menu progress)."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM exam_questions
        WHERE is_active = 1
        """
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def count_active_questions_by_level(conn: sqlite3.Connection, level: int) -> int:
    """Count active questions for one level."""
    normalized_level = _validate_level(level)
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM exam_questions
        WHERE level = ?
          AND is_active = 1
        """,
        (normalized_level,),
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def list_available_active_levels(conn: sqlite3.Connection) -> list[int]:
    """List levels that currently have active questions."""
    rows = conn.execute(
        """
        SELECT DISTINCT level
        FROM exam_questions
        WHERE is_active = 1
        ORDER BY level ASC
        """
    ).fetchall()
    return [int(row["level"]) for row in rows]


def list_active_questions_by_level(conn: sqlite3.Connection, level: int) -> list[dict[str, object]]:
    """List active questions for level ordered by question_number ASC."""
    normalized_level = _validate_level(level)
    rows = conn.execute(
        """
        SELECT
            """
        + _QUESTION_COLUMNS
        + """
        FROM exam_questions
        WHERE level = ?
          AND is_active = 1
        ORDER BY question_number ASC
        """,
        (normalized_level,),
    ).fetchall()
    return [dict(row) for row in rows]


def count_completed_exam_questions(conn: sqlite3.Connection, user_id: int) -> int:
    """Count completed active exam questions for user."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM exam_question_progress AS eqp
        JOIN exam_questions AS eq
          ON eq.level = eqp.level
         AND eq.question_number = eqp.question_number
        WHERE eqp.user_id = ?
          AND eq.is_active = 1
        """,
        (user_id,),
    ).fetchone()
    return int(row["total"]) if row is not None else 0
