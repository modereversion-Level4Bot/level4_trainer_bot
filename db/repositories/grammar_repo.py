"""Grammar content repository."""

from __future__ import annotations

import sqlite3


_STUDIED_TOPIC_STATUSES = ("completed", "studied", "passed", "done", "finished")


def _normalize_topic_type(topic_type: str) -> str:
    normalized = (topic_type or "").strip().lower()
    if normalized not in {"main", "extra"}:
        raise RuntimeError("topic_type must be 'main' or 'extra'")
    return normalized


def _build_topic_slug(topic_number: int) -> str:
    return f"grammar_{topic_number:03d}"


def _base_topic_projection() -> str:
    return """
        SELECT
            id,
            topic_number,
            LOWER(COALESCE(topic_type, 'main')) AS topic_type,
            title_ru AS title_ru,
            title_en AS title_en,
            simple_explanation_ru AS simple_explanation_ru,
            simple_explanation_en AS simple_explanation_en,
            detailed_explanation_ru AS detailed_explanation_ru,
            detailed_explanation_en AS detailed_explanation_en
        FROM grammar_topics
        WHERE COALESCE(is_active, 1) = 1
    """


def list_main_topics(conn: sqlite3.Connection) -> list[dict[str, object]]:
    """List grammar topics that belong to main progress."""
    rows = conn.execute(
        _base_topic_projection()
        + """
        AND LOWER(COALESCE(topic_type, 'main')) = 'main'
        ORDER BY topic_number ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_extra_topics(conn: sqlite3.Connection) -> list[dict[str, object]]:
    """List grammar topics marked as extra."""
    rows = conn.execute(
        _base_topic_projection()
        + """
        AND LOWER(COALESCE(topic_type, 'main')) = 'extra'
        ORDER BY topic_number ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_topic_by_number(
    conn: sqlite3.Connection,
    topic_number: int,
) -> dict[str, object] | None:
    """Get one topic by stable topic_number key."""
    row = conn.execute(
        _base_topic_projection()
        + """
        AND topic_number = ?
        """,
        (topic_number,),
    ).fetchone()
    return dict(row) if row is not None else None


def upsert_grammar_topic(
    conn: sqlite3.Connection,
    *,
    topic_number: int,
    topic_type: str,
    topic_title_ru: str,
    topic_title_en: str | None,
    simple_explanation_ru: str,
    simple_explanation_en: str | None,
    detailed_explanation_ru: str | None,
    detailed_explanation_en: str | None,
) -> None:
    """Insert or update grammar topic by topic_number."""
    normalized_topic_type = _normalize_topic_type(topic_type)
    slug = _build_topic_slug(topic_number)
    title_ru = topic_title_ru.strip()
    title_en = (topic_title_en or "").strip() or None
    simple_ru = simple_explanation_ru.strip()
    simple_en = (simple_explanation_en or "").strip() or None
    detailed_ru = (detailed_explanation_ru or "").strip() or None
    detailed_en = (detailed_explanation_en or "").strip() or None

    conn.execute(
        """
        INSERT INTO grammar_topics (
            slug,
            title,
            description,
            sort_order,
            is_active,
            topic_number,
            topic_type,
            title_ru,
            title_en,
            simple_explanation_ru,
            simple_explanation_en,
            detailed_explanation_ru,
            detailed_explanation_en,
            updated_at
        )
        VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(topic_number) DO UPDATE SET
            slug = excluded.slug,
            title = excluded.title,
            description = excluded.description,
            sort_order = excluded.sort_order,
            is_active = 1,
            topic_type = excluded.topic_type,
            title_ru = excluded.title_ru,
            title_en = excluded.title_en,
            simple_explanation_ru = excluded.simple_explanation_ru,
            simple_explanation_en = excluded.simple_explanation_en,
            detailed_explanation_ru = excluded.detailed_explanation_ru,
            detailed_explanation_en = excluded.detailed_explanation_en,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            slug,
            title_ru,
            simple_ru,
            topic_number,
            topic_number,
            normalized_topic_type,
            title_ru,
            title_en,
            simple_ru,
            simple_en,
            detailed_ru,
            detailed_en,
        ),
    )


def upsert_grammar_question(
    conn: sqlite3.Connection,
    *,
    topic_number: int,
    question_number: int,
    question: str,
    answer_1: str,
    answer_2: str,
    answer_3: str,
    correct_answer: int,
    wrong_explanation_ru: str,
    wrong_explanation_en: str | None,
) -> None:
    """Insert or update grammar question by (topic_number, question_number)."""
    if correct_answer not in {1, 2, 3}:
        raise RuntimeError("correct_answer must be one of: 1, 2, 3")

    topic_exists = conn.execute(
        """
        SELECT 1
        FROM grammar_topics
        WHERE topic_number = ?
        LIMIT 1
        """,
        (topic_number,),
    ).fetchone()
    if topic_exists is None:
        raise RuntimeError(
            f"topic_number {topic_number} not found in grammar_topics"
        )

    q_text = question.strip()
    a1_text = answer_1.strip()
    a2_text = answer_2.strip()
    a3_text = answer_3.strip()
    wrong_ru = wrong_explanation_ru.strip()
    wrong_en = (wrong_explanation_en or "").strip() or None

    conn.execute(
        """
        INSERT INTO grammar_questions (
            topic_number,
            question_number,
            question,
            answer_1,
            answer_2,
            answer_3,
            correct_answer,
            wrong_explanation_ru,
            wrong_explanation_en,
            is_active,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(topic_number, question_number) DO UPDATE SET
            question = excluded.question,
            answer_1 = excluded.answer_1,
            answer_2 = excluded.answer_2,
            answer_3 = excluded.answer_3,
            correct_answer = excluded.correct_answer,
            wrong_explanation_ru = excluded.wrong_explanation_ru,
            wrong_explanation_en = excluded.wrong_explanation_en,
            is_active = 1,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            topic_number,
            question_number,
            q_text,
            a1_text,
            a2_text,
            a3_text,
            correct_answer,
            wrong_ru,
            wrong_en,
        ),
    )


def deactivate_missing_topics(
    conn: sqlite3.Connection,
    *,
    active_topic_numbers: set[int],
) -> int:
    """Mark grammar topics absent in current import as inactive."""
    if active_topic_numbers:
        placeholders = ", ".join("?" for _ in active_topic_numbers)
        result = conn.execute(
            f"""
            UPDATE grammar_topics
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE COALESCE(is_active, 1) = 1
              AND topic_number NOT IN ({placeholders})
            """,
            tuple(sorted(active_topic_numbers)),
        )
    else:
        result = conn.execute(
            """
            UPDATE grammar_topics
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE COALESCE(is_active, 1) = 1
            """
        )
    return int(result.rowcount or 0)


def deactivate_missing_questions(
    conn: sqlite3.Connection,
    *,
    active_question_keys: set[tuple[int, int]],
) -> int:
    """Mark grammar questions absent in current import as inactive."""
    if active_question_keys:
        placeholders = ", ".join("(?, ?)" for _ in active_question_keys)
        params: list[int] = []
        for topic_number, question_number in sorted(active_question_keys):
            params.extend([topic_number, question_number])
        result = conn.execute(
            f"""
            UPDATE grammar_questions
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE COALESCE(is_active, 1) = 1
              AND (topic_number, question_number) NOT IN ({placeholders})
            """,
            tuple(params),
        )
    else:
        result = conn.execute(
            """
            UPDATE grammar_questions
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE COALESCE(is_active, 1) = 1
            """
        )
    return int(result.rowcount or 0)


def count_main_topics(conn: sqlite3.Connection) -> int:
    """Count grammar topics with topic_type='main'."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM grammar_topics
        WHERE LOWER(COALESCE(topic_type, 'main')) = 'main'
          AND COALESCE(is_active, 1) = 1
        """
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def count_active_main_topics(conn: sqlite3.Connection) -> int:
    """
    Backward-compatible alias for main topics count.

    Main menu uses this function name, so keep it stable.
    """
    return count_main_topics(conn)


def count_extra_topics(conn: sqlite3.Connection) -> int:
    """Count grammar topics with topic_type='extra'."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM grammar_topics
        WHERE LOWER(COALESCE(topic_type, 'main')) = 'extra'
          AND COALESCE(is_active, 1) = 1
        """
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def count_questions_for_topic(conn: sqlite3.Connection, topic_number: int) -> int:
    """Count grammar questions for a single topic_number."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM grammar_questions AS gq
        JOIN grammar_topics AS gt ON gt.topic_number = gq.topic_number
        WHERE gq.topic_number = ?
          AND COALESCE(gq.is_active, 1) = 1
          AND COALESCE(gt.is_active, 1) = 1
        """,
        (topic_number,),
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def list_questions_for_training(
    conn: sqlite3.Connection,
    topic_number: int,
    limit: int = 10,
) -> list[dict[str, object]]:
    """List random questions for one training launch."""
    safe_limit = max(1, min(int(limit), 100))
    rows = conn.execute(
        """
        SELECT
            gq.id,
            gq.topic_number,
            gq.question_number
        FROM grammar_questions AS gq
        JOIN grammar_topics AS gt ON gt.topic_number = gq.topic_number
        WHERE gq.topic_number = ?
          AND COALESCE(gq.is_active, 1) = 1
          AND COALESCE(gt.is_active, 1) = 1
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (topic_number, safe_limit),
    ).fetchall()
    return [dict(row) for row in rows]


def get_question_by_topic_and_number(
    conn: sqlite3.Connection,
    topic_number: int,
    question_number: int,
) -> dict[str, object] | None:
    """Get one grammar question by topic_number + question_number."""
    row = conn.execute(
        """
        SELECT
            gq.id,
            gq.topic_number,
            gq.question_number,
            gq.question,
            gq.answer_1,
            gq.answer_2,
            gq.answer_3,
            gq.correct_answer,
            gq.wrong_explanation_ru,
            gq.wrong_explanation_en
        FROM grammar_questions AS gq
        JOIN grammar_topics AS gt ON gt.topic_number = gq.topic_number
        WHERE gq.topic_number = ?
          AND gq.question_number = ?
          AND COALESCE(gq.is_active, 1) = 1
          AND COALESCE(gt.is_active, 1) = 1
        LIMIT 1
        """,
        (topic_number, question_number),
    ).fetchone()
    return dict(row) if row is not None else None


def mark_grammar_topic_studied(
    conn: sqlite3.Connection,
    user_id: int,
    topic_number: int,
) -> None:
    """Mark grammar topic as studied for user."""
    topic_row = conn.execute(
        """
        SELECT id
        FROM grammar_topics
        WHERE topic_number = ?
          AND COALESCE(is_active, 1) = 1
        LIMIT 1
        """,
        (topic_number,),
    ).fetchone()
    if topic_row is None:
        return

    topic_id = int(topic_row["id"])
    conn.execute(
        """
        INSERT INTO grammar_progress (
            user_id,
            topic_id,
            status,
            updated_at
        )
        VALUES (?, ?, 'studied', CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, topic_id) DO UPDATE SET
            status = 'studied',
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, topic_id),
    )


def is_grammar_topic_studied(
    conn: sqlite3.Connection,
    user_id: int,
    topic_number: int,
) -> bool:
    """Return whether grammar topic is already studied for user."""
    placeholders = ", ".join(["?"] * len(_STUDIED_TOPIC_STATUSES))
    row = conn.execute(
        f"""
        SELECT 1
        FROM grammar_progress AS gp
        JOIN grammar_topics AS gt ON gt.id = gp.topic_id
        WHERE gp.user_id = ?
          AND gt.topic_number = ?
          AND COALESCE(gt.is_active, 1) = 1
          AND LOWER(COALESCE(gp.status, '')) IN ({placeholders})
        LIMIT 1
        """,
        (user_id, topic_number, *_STUDIED_TOPIC_STATUSES),
    ).fetchone()
    return row is not None


def count_studied_main_topics(conn: sqlite3.Connection, user_id: int) -> int:
    """Count studied active grammar topics for user."""
    placeholders = ", ".join(["?"] * len(_STUDIED_TOPIC_STATUSES))
    params: tuple[object, ...] = (user_id, *_STUDIED_TOPIC_STATUSES)
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT gp.topic_id) AS total
        FROM grammar_progress AS gp
        JOIN grammar_topics AS gt ON gt.id = gp.topic_id
        WHERE gp.user_id = ?
          AND LOWER(COALESCE(gt.topic_type, 'main')) = 'main'
          AND COALESCE(gt.is_active, 1) = 1
          AND LOWER(COALESCE(gp.status, '')) IN ({placeholders})
        """,
        params,
    ).fetchone()
    return int(row["total"]) if row is not None else 0
