"""Routes repository runtime selectors."""

from __future__ import annotations

import sqlite3

from db.repositories.routes_repo_common import _normalize_int, _normalize_positive_int


def count_active_routes(conn: sqlite3.Connection) -> int:
    """Count active routes."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM routes
        WHERE COALESCE(is_active, 1) = 1
        """
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def list_active_routes(
    conn: sqlite3.Connection,
    *,
    limit: int,
    offset: int,
) -> list[dict[str, object]]:
    """List active routes for paginated routes UI."""
    normalized_limit = _normalize_positive_int(limit, field_name="limit")
    normalized_offset = _normalize_int(offset, field_name="offset", min_value=0)
    rows = conn.execute(
        """
        SELECT
            id,
            code,
            title,
            route_order,
            title_ru,
            title_en,
            briefing_ru,
            briefing_en,
            image_file,
            is_active
        FROM routes
        WHERE COALESCE(is_active, 1) = 1
        ORDER BY COALESCE(route_order, 0) ASC, id ASC
        LIMIT ?
        OFFSET ?
        """,
        (normalized_limit, normalized_offset),
    ).fetchall()
    return [dict(row) for row in rows]


def get_route_by_id(
    conn: sqlite3.Connection,
    *,
    route_id: int,
) -> dict[str, object] | None:
    """Get one route by DB id."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    row = conn.execute(
        """
        SELECT
            id,
            code,
            title,
            route_order,
            title_ru,
            title_en,
            briefing_ru,
            briefing_en,
            image_file,
            is_active
        FROM routes
        WHERE id = ?
        LIMIT 1
        """,
        (normalized_route_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def get_active_steps_for_route(
    conn: sqlite3.Connection,
    *,
    route_id: int,
) -> list[dict[str, object]]:
    """List active route steps ordered by step_number ASC."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    rows = conn.execute(
        """
        SELECT
            id,
            route_id,
            COALESCE(step_number, step_no) AS step_number,
            step_type,
            text_ru,
            text_en,
            image_file,
            audio_file,
            transcript_ru,
            transcript_en,
            pilot_answer_ru,
            pilot_answer_en,
            is_active
        FROM route_steps
        WHERE route_id = ?
          AND COALESCE(is_active, 1) = 1
        ORDER BY COALESCE(step_number, step_no) ASC, id ASC
        """,
        (normalized_route_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_route_step(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    step_number: int,
) -> dict[str, object] | None:
    """Get one route step by route + step number."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_step_number = _normalize_positive_int(
        step_number,
        field_name="step_number",
    )
    row = conn.execute(
        """
        SELECT
            id,
            route_id,
            COALESCE(step_number, step_no) AS step_number,
            step_type,
            text_ru,
            text_en,
            image_file,
            audio_file,
            transcript_ru,
            transcript_en,
            pilot_answer_ru,
            pilot_answer_en,
            is_active
        FROM route_steps
        WHERE route_id = ?
          AND COALESCE(step_number, step_no) = ?
          AND COALESCE(is_active, 1) = 1
        LIMIT 1
        """,
        (normalized_route_id, normalized_step_number),
    ).fetchone()
    return dict(row) if row is not None else None


def get_next_active_step_number(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    current_step_number: int,
) -> int | None:
    """Resolve next active step number for route."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_step_number = _normalize_positive_int(
        current_step_number,
        field_name="current_step_number",
    )
    row = conn.execute(
        """
        SELECT MIN(COALESCE(step_number, step_no)) AS step_number
        FROM route_steps
        WHERE route_id = ?
          AND COALESCE(is_active, 1) = 1
          AND COALESCE(step_number, step_no) > ?
        """,
        (normalized_route_id, normalized_step_number),
    ).fetchone()
    if row is None or row["step_number"] is None:
        return None
    return int(row["step_number"])


def get_previous_active_step_number(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    current_step_number: int,
) -> int | None:
    """Resolve previous active step number for route."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_step_number = _normalize_positive_int(
        current_step_number,
        field_name="current_step_number",
    )
    row = conn.execute(
        """
        SELECT MAX(COALESCE(step_number, step_no)) AS step_number
        FROM route_steps
        WHERE route_id = ?
          AND COALESCE(is_active, 1) = 1
          AND COALESCE(step_number, step_no) < ?
        """,
        (normalized_route_id, normalized_step_number),
    ).fetchone()
    if row is None or row["step_number"] is None:
        return None
    return int(row["step_number"])


def list_active_news_for_route(
    conn: sqlite3.Connection,
    *,
    route_id: int,
) -> list[dict[str, object]]:
    """List active news for one route."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    rows = conn.execute(
        """
        SELECT
            id,
            route_id,
            news_code,
            news_order,
            image_file,
            audio_file,
            transcript_ru,
            transcript_en,
            is_active
        FROM route_news
        WHERE route_id = ?
          AND COALESCE(is_active, 1) = 1
        ORDER BY COALESCE(news_order, 0) ASC, id ASC
        """,
        (normalized_route_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def count_active_news_for_route(
    conn: sqlite3.Connection,
    *,
    route_id: int,
) -> int:
    """Count active route news items for one route."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM route_news
        WHERE route_id = ?
          AND COALESCE(is_active, 1) = 1
        """,
        (normalized_route_id,),
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def list_active_news_for_route_paginated(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    limit: int,
    offset: int,
) -> list[dict[str, object]]:
    """List active route news with pagination."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_limit = _normalize_positive_int(limit, field_name="limit")
    normalized_offset = _normalize_int(offset, field_name="offset", min_value=0)
    rows = conn.execute(
        """
        SELECT
            id,
            route_id,
            news_code,
            news_order,
            image_file,
            audio_file,
            transcript_ru,
            transcript_en,
            is_active
        FROM route_news
        WHERE route_id = ?
          AND COALESCE(is_active, 1) = 1
        ORDER BY COALESCE(news_order, 0) ASC, id ASC
        LIMIT ?
        OFFSET ?
        """,
        (normalized_route_id, normalized_limit, normalized_offset),
    ).fetchall()
    return [dict(row) for row in rows]


def get_route_news_by_id(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    news_id: int,
) -> dict[str, object] | None:
    """Get active route news by route_id + news id."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_news_id = _normalize_positive_int(news_id, field_name="news_id")
    row = conn.execute(
        """
        SELECT
            id,
            route_id,
            news_code,
            news_order,
            image_file,
            audio_file,
            transcript_ru,
            transcript_en,
            is_active
        FROM route_news
        WHERE route_id = ?
          AND id = ?
          AND COALESCE(is_active, 1) = 1
        LIMIT 1
        """,
        (normalized_route_id, normalized_news_id),
    ).fetchone()
    return dict(row) if row is not None else None


def list_active_question_blocks(
    conn: sqlite3.Connection,
    *,
    route_id: int,
) -> list[dict[str, object]]:
    """List active question blocks for route."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    rows = conn.execute(
        """
        SELECT
            id,
            route_id,
            block_code,
            block_order,
            is_active
        FROM route_question_blocks
        WHERE route_id = ?
          AND COALESCE(is_active, 1) = 1
        ORDER BY COALESCE(block_order, 0) ASC, id ASC
        """,
        (normalized_route_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def count_active_question_blocks_with_questions(
    conn: sqlite3.Connection,
    *,
    route_id: int,
) -> int:
    """Count active question blocks that contain active questions."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM route_question_blocks AS b
        WHERE b.route_id = ?
          AND COALESCE(b.is_active, 1) = 1
          AND EXISTS (
              SELECT 1
              FROM route_questions AS q
              WHERE q.route_id = b.route_id
                AND q.question_block_id = b.id
                AND COALESCE(q.is_active, 1) = 1
          )
        """,
        (normalized_route_id,),
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def list_active_question_blocks_with_question_counts(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    limit: int,
    offset: int,
) -> list[dict[str, object]]:
    """List active question blocks with active question counts (paginated)."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_limit = _normalize_positive_int(limit, field_name="limit")
    normalized_offset = _normalize_int(offset, field_name="offset", min_value=0)
    rows = conn.execute(
        """
        SELECT
            b.id,
            b.route_id,
            b.block_code,
            b.block_order,
            b.is_active,
            COUNT(q.id) AS questions_count
        FROM route_question_blocks AS b
        JOIN route_questions AS q
          ON q.route_id = b.route_id
         AND q.question_block_id = b.id
         AND COALESCE(q.is_active, 1) = 1
        WHERE b.route_id = ?
          AND COALESCE(b.is_active, 1) = 1
        GROUP BY b.id, b.route_id, b.block_code, b.block_order, b.is_active
        ORDER BY COALESCE(b.block_order, 0) ASC, b.id ASC
        LIMIT ?
        OFFSET ?
        """,
        (normalized_route_id, normalized_limit, normalized_offset),
    ).fetchall()
    return [dict(row) for row in rows]


def get_question_block_by_id(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_id: int,
) -> dict[str, object] | None:
    """Get one active question block that has at least one active question."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(block_id, field_name="block_id")
    row = conn.execute(
        """
        SELECT
            b.id,
            b.route_id,
            b.block_code,
            b.block_order,
            b.is_active
        FROM route_question_blocks AS b
        WHERE b.route_id = ?
          AND b.id = ?
          AND COALESCE(b.is_active, 1) = 1
          AND EXISTS (
              SELECT 1
              FROM route_questions AS q
              WHERE q.route_id = b.route_id
                AND q.question_block_id = b.id
                AND COALESCE(q.is_active, 1) = 1
          )
        LIMIT 1
        """,
        (normalized_route_id, normalized_block_id),
    ).fetchone()
    return dict(row) if row is not None else None


def list_active_questions_for_block(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_id: int,
) -> list[dict[str, object]]:
    """List active route questions for one question block."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(block_id, field_name="block_id")
    rows = conn.execute(
        """
        SELECT
            id,
            route_id,
            question_block_id,
            question_number,
            question_en,
            question_translation_ru,
            image_file,
            is_active
        FROM route_questions
        WHERE route_id = ?
          AND question_block_id = ?
          AND COALESCE(is_active, 1) = 1
        ORDER BY question_number ASC, id ASC
        """,
        (normalized_route_id, normalized_block_id),
    ).fetchall()
    return [dict(row) for row in rows]


def count_questions_in_block(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_id: int,
) -> int:
    """Count active route questions in selected block."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(block_id, field_name="block_id")
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM route_questions
        WHERE route_id = ?
          AND question_block_id = ?
          AND COALESCE(is_active, 1) = 1
        """,
        (normalized_route_id, normalized_block_id),
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def get_route_question(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_id: int,
    question_number: int,
) -> dict[str, object] | None:
    """Get one active route question by route/block/question_number."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(block_id, field_name="block_id")
    normalized_question_number = _normalize_positive_int(
        question_number,
        field_name="question_number",
    )
    row = conn.execute(
        """
        SELECT
            id,
            route_id,
            question_block_id,
            question_number,
            question_en,
            question_translation_ru,
            image_file,
            is_active
        FROM route_questions
        WHERE route_id = ?
          AND question_block_id = ?
          AND question_number = ?
          AND COALESCE(is_active, 1) = 1
        LIMIT 1
        """,
        (normalized_route_id, normalized_block_id, normalized_question_number),
    ).fetchone()
    return dict(row) if row is not None else None


def get_next_question_number(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_id: int,
    current_question_number: int,
) -> int | None:
    """Resolve next active question number in selected block."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(block_id, field_name="block_id")
    normalized_question_number = _normalize_positive_int(
        current_question_number,
        field_name="current_question_number",
    )
    row = conn.execute(
        """
        SELECT MIN(question_number) AS question_number
        FROM route_questions
        WHERE route_id = ?
          AND question_block_id = ?
          AND COALESCE(is_active, 1) = 1
          AND question_number > ?
        """,
        (normalized_route_id, normalized_block_id, normalized_question_number),
    ).fetchone()
    if row is None or row["question_number"] is None:
        return None
    return int(row["question_number"])


def get_previous_question_number(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_id: int,
    current_question_number: int,
) -> int | None:
    """Resolve previous active question number in selected block."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(block_id, field_name="block_id")
    normalized_question_number = _normalize_positive_int(
        current_question_number,
        field_name="current_question_number",
    )
    row = conn.execute(
        """
        SELECT MAX(question_number) AS question_number
        FROM route_questions
        WHERE route_id = ?
          AND question_block_id = ?
          AND COALESCE(is_active, 1) = 1
          AND question_number < ?
        """,
        (normalized_route_id, normalized_block_id, normalized_question_number),
    ).fetchone()
    if row is None or row["question_number"] is None:
        return None
    return int(row["question_number"])
