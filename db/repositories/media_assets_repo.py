"""Repository helpers for media_assets table."""

from __future__ import annotations

from collections.abc import Iterable
import sqlite3


_ALLOWED_STATUSES = {"ready", "missing", "failed", "outdated", "skipped"}
_QUESTIONS_FEATURE = "questions"
_QUESTION_AUDIO_CONTENT_TYPE = "question_audio"
_ROUTES_FEATURE = "routes"
_ROUTE_BRIEFING_IMAGE_CONTENT_TYPE = "route_briefing_image"
_ROUTE_STEP_IMAGE_CONTENT_TYPE = "route_step_image"
_ROUTE_NEWS_IMAGE_CONTENT_TYPE = "route_news_image"
_ROUTE_QUESTION_IMAGE_CONTENT_TYPE = "route_question_image"
_ROUTE_STEP_AUDIO_CONTENT_TYPE = "route_step_audio"
_ROUTE_NEWS_AUDIO_CONTENT_TYPE = "route_news_audio"


def _required_text(value: str, *, field_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"{field_name} is required")
    return normalized


def _optional_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _normalize_status(status: str) -> str:
    normalized = _required_text(status, field_name="status").lower()
    if normalized not in _ALLOWED_STATUSES:
        raise RuntimeError(f"Unsupported media asset status: {normalized}")
    return normalized


def upsert_media_asset(
    conn: sqlite3.Connection,
    *,
    feature: str,
    content_type: str,
    content_key: str,
    local_path: str,
    file_id: str | None = None,
    file_unique_id: str | None = None,
    checksum: str | None = None,
    status: str = "ready",
    last_error: str | None = None,
) -> None:
    """Insert or update one media asset by stable content key."""
    normalized_feature = _required_text(feature, field_name="feature")
    normalized_content_type = _required_text(content_type, field_name="content_type")
    normalized_content_key = _required_text(content_key, field_name="content_key")
    normalized_local_path = _required_text(local_path, field_name="local_path")
    normalized_status = _normalize_status(status)

    conn.execute(
        """
        INSERT INTO media_assets (
            feature,
            content_type,
            content_key,
            local_path,
            file_id,
            file_unique_id,
            checksum,
            status,
            last_error,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(feature, content_type, content_key) DO UPDATE SET
            local_path = excluded.local_path,
            file_id = excluded.file_id,
            file_unique_id = excluded.file_unique_id,
            checksum = excluded.checksum,
            status = excluded.status,
            last_error = excluded.last_error,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            normalized_feature,
            normalized_content_type,
            normalized_content_key,
            normalized_local_path,
            _optional_text(file_id),
            _optional_text(file_unique_id),
            _optional_text(checksum),
            normalized_status,
            _optional_text(last_error),
        ),
    )


def get_media_asset(
    conn: sqlite3.Connection,
    *,
    feature: str,
    content_type: str,
    content_key: str,
) -> dict[str, object] | None:
    """Get one media asset by feature/content type/content key."""
    row = conn.execute(
        """
        SELECT
            id,
            feature,
            content_type,
            content_key,
            local_path,
            file_id,
            file_unique_id,
            checksum,
            status,
            last_error,
            created_at,
            updated_at
        FROM media_assets
        WHERE feature = ?
          AND content_type = ?
          AND content_key = ?
        LIMIT 1
        """,
        (
            _required_text(feature, field_name="feature"),
            _required_text(content_type, field_name="content_type"),
            _required_text(content_key, field_name="content_key"),
        ),
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def get_ready_media_asset(
    conn: sqlite3.Connection,
    *,
    feature: str,
    content_type: str,
    content_key: str,
) -> dict[str, object] | None:
    """Get one ready media asset with non-empty file_id."""
    row = conn.execute(
        """
        SELECT
            id,
            feature,
            content_type,
            content_key,
            local_path,
            file_id,
            file_unique_id,
            checksum,
            status,
            last_error,
            created_at,
            updated_at
        FROM media_assets
        WHERE feature = ?
          AND content_type = ?
          AND content_key = ?
          AND status = 'ready'
          AND NULLIF(TRIM(COALESCE(file_id, '')), '') IS NOT NULL
        LIMIT 1
        """,
        (
            _required_text(feature, field_name="feature"),
            _required_text(content_type, field_name="content_type"),
            _required_text(content_key, field_name="content_key"),
        ),
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def list_media_assets(
    conn: sqlite3.Connection,
    *,
    feature: str | None = None,
    content_type: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    """List media assets with optional filters."""
    where_clauses: list[str] = []
    params: list[object] = []

    normalized_feature = _optional_text(feature)
    if normalized_feature:
        where_clauses.append("feature = ?")
        params.append(normalized_feature)

    normalized_content_type = _optional_text(content_type)
    if normalized_content_type:
        where_clauses.append("content_type = ?")
        params.append(normalized_content_type)

    normalized_status = _optional_text(status)
    if normalized_status:
        where_clauses.append("status = ?")
        params.append(_normalize_status(normalized_status))

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    rows = conn.execute(
        f"""
        SELECT
            id,
            feature,
            content_type,
            content_key,
            local_path,
            file_id,
            file_unique_id,
            checksum,
            status,
            last_error,
            created_at,
            updated_at
        FROM media_assets
        {where_sql}
        ORDER BY feature ASC, content_type ASC, content_key ASC
        """,
        tuple(params),
    ).fetchall()
    return [dict(row) for row in rows]


def mark_media_asset_missing(
    conn: sqlite3.Connection,
    *,
    feature: str,
    content_type: str,
    content_key: str,
    local_path: str,
    checksum: str | None = None,
    error: str | None = None,
) -> None:
    """Upsert media asset in missing state."""
    upsert_media_asset(
        conn,
        feature=feature,
        content_type=content_type,
        content_key=content_key,
        local_path=local_path,
        file_id=None,
        file_unique_id=None,
        checksum=checksum,
        status="missing",
        last_error=(error or "Local media file not found"),
    )


def mark_media_asset_failed(
    conn: sqlite3.Connection,
    *,
    feature: str,
    content_type: str,
    content_key: str,
    local_path: str,
    checksum: str | None = None,
    error: str | None = None,
) -> None:
    """Upsert media asset in failed state."""
    upsert_media_asset(
        conn,
        feature=feature,
        content_type=content_type,
        content_key=content_key,
        local_path=local_path,
        file_id=None,
        file_unique_id=None,
        checksum=checksum,
        status="failed",
        last_error=(error or "Media upload failed"),
    )


def _clear_orphaned_assets(
    conn: sqlite3.Connection,
    *,
    feature: str,
    content_type: str,
    active_content_keys: Iterable[str],
    last_error: str,
) -> int:
    """Mark stale media assets for one feature/content type as outdated."""
    normalized_active_keys = {
        key.strip()
        for key in active_content_keys
        if isinstance(key, str) and key.strip()
    }
    params: list[object] = [feature, content_type]
    not_in_clause = ""
    if normalized_active_keys:
        placeholders = ",".join("?" for _ in normalized_active_keys)
        not_in_clause = f"AND content_key NOT IN ({placeholders})"
        params.extend(sorted(normalized_active_keys))

    cursor = conn.execute(
        f"""
        UPDATE media_assets
        SET status = 'outdated',
            last_error = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE feature = ?
          AND content_type = ?
          AND status <> 'outdated'
          {not_in_clause}
        """,
        (last_error, *params),
    )
    changed = int(cursor.rowcount or 0)
    return changed if changed > 0 else 0


def clear_orphaned_question_audio_assets(
    conn: sqlite3.Connection,
    active_content_keys: Iterable[str],
) -> int:
    """
    Mark stale question-audio assets as outdated.

    Assets are not physically deleted, only marked with status="outdated".
    """
    return _clear_orphaned_assets(
        conn,
        feature=_QUESTIONS_FEATURE,
        content_type=_QUESTION_AUDIO_CONTENT_TYPE,
        active_content_keys=active_content_keys,
        last_error="No active question uses this asset after latest preload.",
    )


def clear_orphaned_route_step_audio_assets(
    conn: sqlite3.Connection,
    active_content_keys: Iterable[str],
) -> int:
    """Mark stale route-step-audio assets as outdated."""
    return _clear_orphaned_assets(
        conn,
        feature=_ROUTES_FEATURE,
        content_type=_ROUTE_STEP_AUDIO_CONTENT_TYPE,
        active_content_keys=active_content_keys,
        last_error="No active route step uses this asset after latest preload.",
    )


def clear_orphaned_route_news_audio_assets(
    conn: sqlite3.Connection,
    active_content_keys: Iterable[str],
) -> int:
    """Mark stale route-news-audio assets as outdated."""
    return _clear_orphaned_assets(
        conn,
        feature=_ROUTES_FEATURE,
        content_type=_ROUTE_NEWS_AUDIO_CONTENT_TYPE,
        active_content_keys=active_content_keys,
        last_error="No active route news uses this asset after latest preload.",
    )


def clear_orphaned_route_briefing_image_assets(
    conn: sqlite3.Connection,
    active_content_keys: Iterable[str],
) -> int:
    """Mark stale route-briefing-image assets as outdated."""
    return _clear_orphaned_assets(
        conn,
        feature=_ROUTES_FEATURE,
        content_type=_ROUTE_BRIEFING_IMAGE_CONTENT_TYPE,
        active_content_keys=active_content_keys,
        last_error="No active route briefing uses this asset after latest preload.",
    )


def clear_orphaned_route_step_image_assets(
    conn: sqlite3.Connection,
    active_content_keys: Iterable[str],
) -> int:
    """Mark stale route-step-image assets as outdated."""
    return _clear_orphaned_assets(
        conn,
        feature=_ROUTES_FEATURE,
        content_type=_ROUTE_STEP_IMAGE_CONTENT_TYPE,
        active_content_keys=active_content_keys,
        last_error="No active route step uses this image after latest preload.",
    )


def clear_orphaned_route_news_image_assets(
    conn: sqlite3.Connection,
    active_content_keys: Iterable[str],
) -> int:
    """Mark stale route-news-image assets as outdated."""
    return _clear_orphaned_assets(
        conn,
        feature=_ROUTES_FEATURE,
        content_type=_ROUTE_NEWS_IMAGE_CONTENT_TYPE,
        active_content_keys=active_content_keys,
        last_error="No active route news uses this image after latest preload.",
    )


def clear_orphaned_route_question_image_assets(
    conn: sqlite3.Connection,
    active_content_keys: Iterable[str],
) -> int:
    """Mark stale route-question-image assets as outdated."""
    return _clear_orphaned_assets(
        conn,
        feature=_ROUTES_FEATURE,
        content_type=_ROUTE_QUESTION_IMAGE_CONTENT_TYPE,
        active_content_keys=active_content_keys,
        last_error="No active route question uses this image after latest preload.",
    )
