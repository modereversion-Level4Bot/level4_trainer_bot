"""Routes repository."""

from __future__ import annotations

import sqlite3


_COMPLETED_ROUTE_STATUSES = ("completed", "done", "passed", "finished")


def count_active_routes(conn: sqlite3.Connection) -> int:
    """Count active routes."""
    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM routes
        WHERE is_active = 1
        """
    ).fetchone()
    return int(row["total"]) if row is not None else 0


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
          AND r.is_active = 1
          AND LOWER(COALESCE(rp.status, '')) IN ({placeholders})
        """,
        params,
    ).fetchone()
    return int(row["total"]) if row is not None else 0
