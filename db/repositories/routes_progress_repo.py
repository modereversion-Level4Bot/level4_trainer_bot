"""Routes repository helpers for user progress."""

from __future__ import annotations

import sqlite3

from db.repositories.routes_repo_common import (
    _COMPLETED_ROUTE_STATUSES,
    _normalize_positive_int,
)


def count_completed_routes(conn: sqlite3.Connection, user_id: int) -> int:
    """Count completed active routes for user."""
    placeholders = ", ".join(["?"] * len(_COMPLETED_ROUTE_STATUSES))
    params: tuple[object, ...] = (user_id, *_COMPLETED_ROUTE_STATUSES)
    row = conn.execute(
        f"""
        SELECT COUNT(DISTINCT rp.route_id) AS total
        FROM route_progress AS rp
        JOIN routes AS r ON r.id = rp.route_id
        WHERE rp.user_id = ?
          AND COALESCE(r.is_active, 1) = 1
          AND LOWER(COALESCE(rp.status, '')) IN ({placeholders})
        """,
        params,
    ).fetchone()
    return int(row["total"]) if row is not None else 0


def mark_route_completed(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    route_id: int,
) -> None:
    """Mark route as completed in route_progress."""
    normalized_user_id = _normalize_positive_int(user_id, field_name="user_id")
    normalized_route_id = _normalize_positive_int(route_id, field_name="route_id")
    conn.execute(
        """
        INSERT INTO route_progress (
            user_id,
            route_id,
            current_step,
            status,
            updated_at
        )
        VALUES (?, ?, 0, 'completed', CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, route_id) DO UPDATE SET
            status = 'completed',
            updated_at = CURRENT_TIMESTAMP
        """,
        (normalized_user_id, normalized_route_id),
    )
