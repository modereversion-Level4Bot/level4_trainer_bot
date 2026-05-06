"""Import question_audio media_assets from base64 JSON env variable."""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import sqlite3
import sys


DEFAULT_DB_PATH = "/data/level4_trainer.db"
EXPECTED_COUNT = 261
IMPORT_ENV_KEY = "MEDIA_ASSETS_IMPORT_JSON_BASE64"
EXPECTED_EXPORT_TYPE = "question_audio_media_assets"
EXPECTED_VERSION = 1


def _safe_print(message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", "replace").decode("ascii"))


def _format_error(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return exc.__class__.__name__
    return text.replace("\n", " ")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import question_audio media_assets from MEDIA_ASSETS_IMPORT_JSON_BASE64 "
            "into media_assets table."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate payload and show counts without writing to DB.",
    )
    parser.add_argument(
        "--confirm-import",
        action="store_true",
        help="Actually write records into DB.",
    )
    return parser.parse_args(argv)


def _resolve_db_path() -> tuple[str, Path]:
    env_value = os.getenv("DB_PATH", "").strip()
    db_path_value = env_value if env_value else DEFAULT_DB_PATH
    db_path = Path(db_path_value).expanduser()
    if not db_path.is_absolute():
        db_path = db_path.resolve()
    return db_path_value, db_path


def _parse_payload_from_env() -> dict[str, object]:
    encoded = os.getenv(IMPORT_ENV_KEY, "").strip()
    if not encoded:
        raise RuntimeError(f"{IMPORT_ENV_KEY} is missing or empty")

    try:
        decoded_bytes = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise RuntimeError(f"{IMPORT_ENV_KEY} is not valid base64: {_format_error(exc)}") from exc

    try:
        payload = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"{IMPORT_ENV_KEY} does not decode to valid UTF-8 JSON: {_format_error(exc)}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Decoded payload must be a JSON object")
    return payload


def _normalize_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _normalize_required_text(record: dict[str, object], field_name: str) -> str:
    value = _normalize_optional_text(record.get(field_name))
    if not value:
        raise RuntimeError(f"Record has empty required field: {field_name}")
    return value


def _validate_metadata(payload: dict[str, object]) -> list[dict[str, object]]:
    export_type = payload.get("export_type")
    version = payload.get("version")
    records = payload.get("records")

    if export_type != EXPECTED_EXPORT_TYPE:
        raise RuntimeError(
            f"Invalid export_type: expected {EXPECTED_EXPORT_TYPE}, got {export_type!r}"
        )
    if version != EXPECTED_VERSION:
        raise RuntimeError(f"Invalid version: expected {EXPECTED_VERSION}, got {version!r}")
    if not isinstance(records, list):
        raise RuntimeError("Payload field 'records' must be a list")

    normalized_records: list[dict[str, object]] = []
    for index, raw in enumerate(records, start=1):
        if not isinstance(raw, dict):
            raise RuntimeError(f"Record #{index} is not an object")

        feature = _normalize_required_text(raw, "feature")
        content_type = _normalize_required_text(raw, "content_type")
        status = _normalize_required_text(raw, "status")
        content_key = _normalize_required_text(raw, "content_key")
        local_path = _normalize_required_text(raw, "local_path")
        file_id = _normalize_required_text(raw, "file_id")

        if feature != "questions":
            raise RuntimeError(f"Record #{index}: feature must be 'questions'")
        if content_type != "question_audio":
            raise RuntimeError(f"Record #{index}: content_type must be 'question_audio'")
        if status != "ready":
            raise RuntimeError(f"Record #{index}: status must be 'ready'")

        normalized_records.append(
            {
                "feature": feature,
                "content_type": content_type,
                "content_key": content_key,
                "local_path": local_path,
                "file_id": file_id,
                "file_unique_id": _normalize_optional_text(raw.get("file_unique_id")),
                "checksum": _normalize_optional_text(raw.get("checksum")),
                "status": status,
                "last_error": _normalize_optional_text(raw.get("last_error")),
            }
        )
    return normalized_records


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    columns: set[str] = set()
    for row in rows:
        if len(row) >= 2 and row[1]:
            columns.add(str(row[1]))
    return columns


def _count_questions_ready(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM media_assets
        WHERE feature = 'questions'
          AND content_type = 'question_audio'
          AND status = 'ready'
        """
    ).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _count_questions_non_empty_file_id(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM media_assets
        WHERE feature = 'questions'
          AND content_type = 'question_audio'
          AND file_id IS NOT NULL
          AND TRIM(CAST(file_id AS TEXT)) != ''
        """
    ).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _upsert_records(conn: sqlite3.Connection, records: list[dict[str, object]]) -> int:
    cursor = conn.cursor()
    upserted = 0
    for record in records:
        cursor.execute(
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
                record["feature"],
                record["content_type"],
                record["content_key"],
                record["local_path"],
                record["file_id"],
                record["file_unique_id"],
                record["checksum"],
                record["status"],
                record["last_error"],
            ),
        )
        upserted += 1
    return upserted


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    if args.dry_run and args.confirm_import:
        _safe_print("ERROR: Use only one mode: --dry-run or --confirm-import")
        return 1
    if not args.dry_run and not args.confirm_import:
        _safe_print("ERROR: Specify one mode flag: --dry-run or --confirm-import")
        return 1

    configured_db_path, resolved_db_path = _resolve_db_path()
    _safe_print("=== Import question_audio media_assets from env ===")
    _safe_print(f"DB_PATH = {configured_db_path}")
    _safe_print(f"mode = {'dry-run' if args.dry_run else 'confirm-import'}")

    if not resolved_db_path.exists():
        _safe_print(f"ERROR: DB file does not exist: {resolved_db_path}")
        return 1
    if not resolved_db_path.is_file():
        _safe_print(f"ERROR: DB path is not a file: {resolved_db_path}")
        return 1

    try:
        payload = _parse_payload_from_env()
        records = _validate_metadata(payload)
    except RuntimeError as exc:
        _safe_print(f"ERROR: {exc}")
        return 1

    _safe_print(f"records decoded: {len(records)}")

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(str(resolved_db_path))
        conn.execute("PRAGMA foreign_keys = ON")

        if not _table_exists(conn, "media_assets"):
            _safe_print("ERROR: table media_assets is missing")
            return 1

        required_columns = {
            "feature",
            "content_type",
            "content_key",
            "local_path",
            "file_id",
            "file_unique_id",
            "checksum",
            "status",
            "last_error",
            "created_at",
            "updated_at",
        }
        columns = _table_columns(conn, "media_assets")
        missing_columns = sorted(required_columns - columns)
        if missing_columns:
            _safe_print(f"ERROR: media_assets is missing columns: {', '.join(missing_columns)}")
            return 1

        before_ready = _count_questions_ready(conn)
        _safe_print(f"before ready count: {before_ready}")

        if args.dry_run:
            imported_count = len(records)
            after_ready = before_ready
            after_non_empty_file_id = _count_questions_non_empty_file_id(conn)
            _safe_print(f"imported/upserted count: {imported_count} (dry-run)")
            _safe_print(f"after ready count: {after_ready} (dry-run, unchanged)")
            _safe_print(
                f"after non-empty file_id count: {after_non_empty_file_id} (dry-run, unchanged)"
            )
            if after_ready != EXPECTED_COUNT:
                _safe_print(
                    f"WARNING: after ready count != expected ({after_ready} != {EXPECTED_COUNT})"
                )
            return 0

        imported_count = _upsert_records(conn, records)
        conn.commit()

        after_ready = _count_questions_ready(conn)
        after_non_empty_file_id = _count_questions_non_empty_file_id(conn)
        _safe_print(f"imported/upserted count: {imported_count}")
        _safe_print(f"after ready count: {after_ready}")
        _safe_print(f"after non-empty file_id count: {after_non_empty_file_id}")
        if after_ready != EXPECTED_COUNT:
            _safe_print(
                f"WARNING: after ready count != expected ({after_ready} != {EXPECTED_COUNT})"
            )
        return 0
    except sqlite3.Error as exc:
        if conn is not None:
            conn.rollback()
        _safe_print(f"ERROR: SQLite failure: {_format_error(exc)}")
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
