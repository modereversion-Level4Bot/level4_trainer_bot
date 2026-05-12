"""Routes repository helpers for preload media selectors."""

from __future__ import annotations

import sqlite3


def list_active_route_step_audio_assets(
    conn: sqlite3.Connection,
) -> list[dict[str, object]]:
    """List active route step audio references for preload jobs."""
    rows = conn.execute(
        """
        SELECT
            r.code AS route_code,
            COALESCE(s.step_number, s.step_no) AS step_number,
            s.audio_file
        FROM route_steps AS s
        JOIN routes AS r ON r.id = s.route_id
        WHERE COALESCE(r.is_active, 1) = 1
          AND COALESCE(s.is_active, 1) = 1
          AND NULLIF(TRIM(COALESCE(s.audio_file, '')), '') IS NOT NULL
        ORDER BY r.code ASC, COALESCE(s.step_number, s.step_no) ASC, s.id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_active_route_briefing_image_assets(
    conn: sqlite3.Connection,
) -> list[dict[str, object]]:
    """List active route briefing image references for preload jobs."""
    rows = conn.execute(
        """
        SELECT
            r.code AS route_code,
            r.image_file
        FROM routes AS r
        WHERE COALESCE(r.is_active, 1) = 1
          AND NULLIF(TRIM(COALESCE(r.image_file, '')), '') IS NOT NULL
        ORDER BY r.code ASC, r.id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_active_route_step_image_assets(
    conn: sqlite3.Connection,
) -> list[dict[str, object]]:
    """List active route step image references for preload jobs."""
    rows = conn.execute(
        """
        SELECT
            r.code AS route_code,
            COALESCE(s.step_number, s.step_no) AS step_number,
            s.image_file
        FROM route_steps AS s
        JOIN routes AS r ON r.id = s.route_id
        WHERE COALESCE(r.is_active, 1) = 1
          AND COALESCE(s.is_active, 1) = 1
          AND NULLIF(TRIM(COALESCE(s.image_file, '')), '') IS NOT NULL
        ORDER BY r.code ASC, COALESCE(s.step_number, s.step_no) ASC, s.id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_active_route_news_image_assets(
    conn: sqlite3.Connection,
) -> list[dict[str, object]]:
    """List active route news image references for preload jobs."""
    rows = conn.execute(
        """
        SELECT
            r.code AS route_code,
            n.news_code,
            n.image_file
        FROM route_news AS n
        JOIN routes AS r ON r.id = n.route_id
        WHERE COALESCE(r.is_active, 1) = 1
          AND COALESCE(n.is_active, 1) = 1
          AND NULLIF(TRIM(COALESCE(n.image_file, '')), '') IS NOT NULL
        ORDER BY r.code ASC, COALESCE(n.news_order, 0) ASC, n.id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_active_route_question_image_assets(
    conn: sqlite3.Connection,
) -> list[dict[str, object]]:
    """List active route question image references for preload jobs."""
    rows = conn.execute(
        """
        SELECT
            r.code AS route_code,
            b.block_code,
            q.question_number,
            q.image_file
        FROM route_questions AS q
        JOIN routes AS r ON r.id = q.route_id
        JOIN route_question_blocks AS b
          ON b.id = q.question_block_id
         AND b.route_id = q.route_id
        WHERE COALESCE(r.is_active, 1) = 1
          AND COALESCE(b.is_active, 1) = 1
          AND COALESCE(q.is_active, 1) = 1
          AND NULLIF(TRIM(COALESCE(q.image_file, '')), '') IS NOT NULL
        ORDER BY r.code ASC, b.block_code ASC, q.question_number ASC, q.id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_active_route_news_audio_assets(
    conn: sqlite3.Connection,
) -> list[dict[str, object]]:
    """List active route news audio references for preload jobs."""
    rows = conn.execute(
        """
        SELECT
            r.code AS route_code,
            n.news_code,
            n.audio_file
        FROM route_news AS n
        JOIN routes AS r ON r.id = n.route_id
        WHERE COALESCE(r.is_active, 1) = 1
          AND COALESCE(n.is_active, 1) = 1
          AND NULLIF(TRIM(COALESCE(n.audio_file, '')), '') IS NOT NULL
        ORDER BY r.code ASC, COALESCE(n.news_order, 0) ASC, n.id ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]
