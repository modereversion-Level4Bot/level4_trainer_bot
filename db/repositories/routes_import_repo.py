"""Routes repository helpers for import and active-sync operations."""

from __future__ import annotations

import sqlite3

from db.repositories.routes_repo_common import (
    _normalize_int,
    _normalize_is_active,
    _normalize_positive_int,
    _normalize_step_type,
    _optional_text,
    _required_text,
)


def upsert_route(
    conn: sqlite3.Connection,
    *,
    route_code: str,
    route_order: int,
    title_ru: str,
    title_en: str | None,
    briefing_ru: str,
    briefing_en: str | None,
    image_file: str | None,
    is_active: int,
) -> None:
    """Insert or update one route by stable route code."""
    normalized_route_code = _required_text(route_code, field_name="route_code")
    normalized_route_order = _normalize_int(
        route_order,
        field_name="route_order",
        min_value=0,
    )
    normalized_title_ru = _required_text(title_ru, field_name="title_ru")
    normalized_briefing_ru = _required_text(briefing_ru, field_name="briefing_ru")
    normalized_is_active = _normalize_is_active(is_active)

    conn.execute(
        """
        INSERT INTO routes (
            code,
            title,
            route_order,
            title_ru,
            title_en,
            briefing_ru,
            briefing_en,
            image_file,
            is_active,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(code) DO UPDATE SET
            title = excluded.title,
            route_order = excluded.route_order,
            title_ru = excluded.title_ru,
            title_en = excluded.title_en,
            briefing_ru = excluded.briefing_ru,
            briefing_en = excluded.briefing_en,
            image_file = excluded.image_file,
            is_active = excluded.is_active,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            normalized_route_code,
            normalized_title_ru,
            normalized_route_order,
            normalized_title_ru,
            _optional_text(title_en),
            normalized_briefing_ru,
            _optional_text(briefing_en),
            _optional_text(image_file),
            normalized_is_active,
        ),
    )


def deactivate_routes_absent(
    conn: sqlite3.Connection,
    *,
    route_codes: set[str],
) -> int:
    """Mark routes absent in sheet as inactive."""
    normalized_codes = {
        _required_text(route_code, field_name="route_code")
        for route_code in route_codes
    }
    if normalized_codes:
        placeholders = ", ".join("?" for _ in normalized_codes)
        result = conn.execute(
            f"""
            UPDATE routes
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE COALESCE(is_active, 1) = 1
              AND code NOT IN ({placeholders})
            """,
            tuple(sorted(normalized_codes)),
        )
    else:
        result = conn.execute(
            """
            UPDATE routes
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE COALESCE(is_active, 1) = 1
            """
        )
    return int(result.rowcount or 0)


def get_route_id_by_code(
    conn: sqlite3.Connection,
    *,
    route_code: str,
) -> int | None:
    """Resolve internal route id by stable route code."""
    normalized_route_code = _required_text(route_code, field_name="route_code")
    row = conn.execute(
        """
        SELECT id
        FROM routes
        WHERE code = ?
        LIMIT 1
        """,
        (normalized_route_code,),
    ).fetchone()
    return int(row["id"]) if row is not None else None


def upsert_route_step(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    step_number: int,
    step_type: str,
    text_ru: str | None,
    text_en: str | None,
    image_file: str | None,
    audio_file: str | None,
    transcript_ru: str | None,
    transcript_en: str | None,
    pilot_answer_ru: str | None,
    pilot_answer_en: str | None,
    is_active: int,
) -> None:
    """Insert or update one route step by (route_id, step_number)."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_step_number = _normalize_positive_int(
        step_number,
        field_name="step_number",
    )
    normalized_step_type = _normalize_step_type(step_type)
    normalized_text_ru = _optional_text(text_ru)
    normalized_text_en = _optional_text(text_en)
    legacy_text = normalized_text_ru or normalized_text_en or ""
    normalized_is_active = _normalize_is_active(is_active)

    conn.execute(
        """
        INSERT INTO route_steps (
            route_id,
            step_no,
            title,
            text,
            image_path,
            audio_path,
            step_number,
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(route_id, step_no) DO UPDATE SET
            title = excluded.title,
            text = excluded.text,
            image_path = excluded.image_path,
            audio_path = excluded.audio_path,
            step_number = excluded.step_number,
            step_type = excluded.step_type,
            text_ru = excluded.text_ru,
            text_en = excluded.text_en,
            image_file = excluded.image_file,
            audio_file = excluded.audio_file,
            transcript_ru = excluded.transcript_ru,
            transcript_en = excluded.transcript_en,
            pilot_answer_ru = excluded.pilot_answer_ru,
            pilot_answer_en = excluded.pilot_answer_en,
            is_active = excluded.is_active
        """,
        (
            normalized_route_id,
            normalized_step_number,
            normalized_step_type,
            legacy_text,
            _optional_text(image_file),
            _optional_text(audio_file),
            normalized_step_number,
            normalized_step_type,
            normalized_text_ru,
            normalized_text_en,
            _optional_text(image_file),
            _optional_text(audio_file),
            _optional_text(transcript_ru),
            _optional_text(transcript_en),
            _optional_text(pilot_answer_ru),
            _optional_text(pilot_answer_en),
            normalized_is_active,
        ),
    )


def deactivate_route_steps_absent(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    step_numbers: set[int],
) -> int:
    """Mark route steps absent in sheet as inactive for one route."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_step_numbers = {
        _normalize_positive_int(step_number, field_name="step_number")
        for step_number in step_numbers
    }
    if normalized_step_numbers:
        placeholders = ", ".join("?" for _ in normalized_step_numbers)
        result = conn.execute(
            f"""
            UPDATE route_steps
            SET is_active = 0
            WHERE route_id = ?
              AND COALESCE(is_active, 1) = 1
              AND COALESCE(step_number, step_no) NOT IN ({placeholders})
            """,
            (normalized_route_id, *sorted(normalized_step_numbers)),
        )
    else:
        result = conn.execute(
            """
            UPDATE route_steps
            SET is_active = 0
            WHERE route_id = ?
              AND COALESCE(is_active, 1) = 1
            """,
            (normalized_route_id,),
        )
    return int(result.rowcount or 0)


def upsert_route_news(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    news_code: str,
    news_order: int,
    image_file: str | None,
    audio_file: str | None,
    transcript_ru: str | None,
    transcript_en: str | None,
    is_active: int,
) -> None:
    """Insert or update one route news item by (route_id, news_code)."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_news_code = _required_text(news_code, field_name="news_code")
    normalized_news_order = _normalize_int(
        news_order,
        field_name="news_order",
        min_value=0,
    )
    normalized_transcript_ru = _optional_text(transcript_ru)
    normalized_transcript_en = _optional_text(transcript_en)
    legacy_text = normalized_transcript_ru or normalized_transcript_en or ""
    normalized_image_file = _optional_text(image_file)
    normalized_audio_file = _optional_text(audio_file)
    normalized_is_active = _normalize_is_active(is_active)

    conn.execute(
        """
        INSERT INTO route_news (
            route_id,
            title,
            text,
            audio_path,
            news_code,
            news_order,
            image_file,
            audio_file,
            transcript_ru,
            transcript_en,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(route_id, news_code) DO UPDATE SET
            title = excluded.title,
            text = excluded.text,
            audio_path = excluded.audio_path,
            news_order = excluded.news_order,
            image_file = excluded.image_file,
            audio_file = excluded.audio_file,
            transcript_ru = excluded.transcript_ru,
            transcript_en = excluded.transcript_en,
            is_active = excluded.is_active
        """,
        (
            normalized_route_id,
            normalized_news_code,
            legacy_text,
            normalized_audio_file,
            normalized_news_code,
            normalized_news_order,
            normalized_image_file,
            normalized_audio_file,
            normalized_transcript_ru,
            normalized_transcript_en,
            normalized_is_active,
        ),
    )


def deactivate_route_news_absent(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    news_codes: set[str],
) -> int:
    """Mark route news absent in sheet as inactive for one route."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_news_codes = {
        _required_text(news_code, field_name="news_code")
        for news_code in news_codes
    }
    if normalized_news_codes:
        placeholders = ", ".join("?" for _ in normalized_news_codes)
        result = conn.execute(
            f"""
            UPDATE route_news
            SET is_active = 0
            WHERE route_id = ?
              AND COALESCE(is_active, 1) = 1
              AND news_code NOT IN ({placeholders})
            """,
            (normalized_route_id, *sorted(normalized_news_codes)),
        )
    else:
        result = conn.execute(
            """
            UPDATE route_news
            SET is_active = 0
            WHERE route_id = ?
              AND COALESCE(is_active, 1) = 1
            """,
            (normalized_route_id,),
        )
    return int(result.rowcount or 0)


def upsert_route_question_block(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_code: str,
    block_order: int,
    is_active: int,
) -> None:
    """Insert or update one route question block by (route_id, block_code)."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_code = _required_text(block_code, field_name="block_code")
    normalized_block_order = _normalize_int(
        block_order,
        field_name="block_order",
        min_value=0,
    )
    normalized_is_active = _normalize_is_active(is_active)

    conn.execute(
        """
        INSERT INTO route_question_blocks (
            route_id,
            block_code,
            block_order,
            is_active,
            updated_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(route_id, block_code) DO UPDATE SET
            block_order = excluded.block_order,
            is_active = excluded.is_active,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            normalized_route_id,
            normalized_block_code,
            normalized_block_order,
            normalized_is_active,
        ),
    )


def deactivate_route_question_blocks_absent(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_codes: set[str],
) -> int:
    """Mark route question blocks absent in sheet as inactive for one route."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_codes = {
        _required_text(block_code, field_name="block_code")
        for block_code in block_codes
    }
    if normalized_block_codes:
        placeholders = ", ".join("?" for _ in normalized_block_codes)
        result = conn.execute(
            f"""
            UPDATE route_question_blocks
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE route_id = ?
              AND COALESCE(is_active, 1) = 1
              AND block_code NOT IN ({placeholders})
            """,
            (normalized_route_id, *sorted(normalized_block_codes)),
        )
    else:
        result = conn.execute(
            """
            UPDATE route_question_blocks
            SET is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE route_id = ?
              AND COALESCE(is_active, 1) = 1
            """,
            (normalized_route_id,),
        )
    return int(result.rowcount or 0)


def get_question_block_id(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_code: str,
) -> int | None:
    """Resolve route question block id by (route_id, block_code)."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_code = _required_text(block_code, field_name="block_code")
    row = conn.execute(
        """
        SELECT id
        FROM route_question_blocks
        WHERE route_id = ?
          AND block_code = ?
        LIMIT 1
        """,
        (normalized_route_id, normalized_block_code),
    ).fetchone()
    return int(row["id"]) if row is not None else None


def upsert_route_question(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_id: int,
    question_number: int,
    question_en: str,
    question_translation_ru: str | None,
    image_file: str | None,
    is_active: int,
) -> None:
    """Insert or update one route question by (route_id, block_id, question_number)."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(block_id, field_name="block_id")
    normalized_question_number = _normalize_positive_int(
        question_number,
        field_name="question_number",
    )
    normalized_question_en = _required_text(question_en, field_name="question_en")
    normalized_is_active = _normalize_is_active(is_active)

    conn.execute(
        """
        INSERT INTO route_questions (
            route_id,
            prompt,
            question_block_id,
            question_number,
            question_en,
            question_translation_ru,
            image_file,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(route_id, question_block_id, question_number) DO UPDATE SET
            prompt = excluded.prompt,
            question_en = excluded.question_en,
            question_translation_ru = excluded.question_translation_ru,
            image_file = excluded.image_file,
            is_active = excluded.is_active
        """,
        (
            normalized_route_id,
            normalized_question_en,
            normalized_block_id,
            normalized_question_number,
            normalized_question_en,
            _optional_text(question_translation_ru),
            _optional_text(image_file),
            normalized_is_active,
        ),
    )


def deactivate_route_questions_absent(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_id: int,
    question_numbers: set[int],
) -> int:
    """Mark route questions absent in sheet as inactive for one route block."""
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_id = _normalize_positive_int(block_id, field_name="block_id")
    normalized_question_numbers = {
        _normalize_positive_int(question_number, field_name="question_number")
        for question_number in question_numbers
    }
    if normalized_question_numbers:
        placeholders = ", ".join("?" for _ in normalized_question_numbers)
        result = conn.execute(
            f"""
            UPDATE route_questions
            SET is_active = 0
            WHERE route_id = ?
              AND question_block_id = ?
              AND COALESCE(is_active, 1) = 1
              AND question_number NOT IN ({placeholders})
            """,
            (
                normalized_route_id,
                normalized_block_id,
                *sorted(normalized_question_numbers),
            ),
        )
    else:
        result = conn.execute(
            """
            UPDATE route_questions
            SET is_active = 0
            WHERE route_id = ?
              AND question_block_id = ?
              AND COALESCE(is_active, 1) = 1
            """,
            (normalized_route_id, normalized_block_id),
        )
    return int(result.rowcount or 0)


def deactivate_route_questions_absent_blocks(
    conn: sqlite3.Connection,
    *,
    route_id: int,
    block_ids: set[int],
) -> int:
    """
    Mark route questions that belong to removed/unknown blocks as inactive.

    This keeps active-sync semantics stable when blocks are removed or renamed.
    """
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    normalized_block_ids = {
        _normalize_positive_int(block_id, field_name="block_id")
        for block_id in block_ids
    }
    if normalized_block_ids:
        placeholders = ", ".join("?" for _ in normalized_block_ids)
        result = conn.execute(
            f"""
            UPDATE route_questions
            SET is_active = 0
            WHERE route_id = ?
              AND COALESCE(is_active, 1) = 1
              AND (
                    question_block_id IS NULL
                    OR question_block_id NOT IN ({placeholders})
              )
            """,
            (normalized_route_id, *sorted(normalized_block_ids)),
        )
    else:
        result = conn.execute(
            """
            UPDATE route_questions
            SET is_active = 0
            WHERE route_id = ?
              AND COALESCE(is_active, 1) = 1
            """,
            (normalized_route_id,),
        )
    return int(result.rowcount or 0)
