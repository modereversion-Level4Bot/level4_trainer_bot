"""Export ready Questions audio media_assets to JSON and base64 files."""

from __future__ import annotations

import base64
import datetime
import gzip
import json
import os
from pathlib import Path
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import BASE_DIR


DEFAULT_LOCAL_DB_PATH = "data/local/dev_main.db"
DEFAULT_RAILWAY_DB_PATH = "/data/level4_trainer.db"
EXPECTED_COUNT = 261
EXPORT_TYPE = "question_audio_media_assets"
EXPORT_VERSION = 1

OUTPUT_DIR = "exports"
OUTPUT_JSON = "question_audio_media_assets.json"
OUTPUT_B64 = "question_audio_media_assets.b64"
OUTPUT_GZIP_B64 = "question_audio_media_assets.json.gz.b64"
OUTPUT_RAILWAY_VARS = "question_audio_media_assets_railway_vars.txt"

CHUNK_SIZE = 30000
RAILWAY_CHUNKS_VAR = "MEDIA_ASSETS_IMPORT_JSON_GZIP_BASE64_CHUNKS"
RAILWAY_CHUNK_PREFIX = "MEDIA_ASSETS_IMPORT_JSON_GZIP_BASE64_CHUNK_"


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


def _resolve_db_path() -> tuple[str, Path]:
    app_env = os.getenv("APP_ENV", "local").strip().lower()
    default_db_path = DEFAULT_RAILWAY_DB_PATH if app_env == "production" else DEFAULT_LOCAL_DB_PATH
    env_value = os.getenv("DB_PATH", "").strip()
    db_path_value = env_value if env_value else default_db_path
    db_path = Path(db_path_value).expanduser()
    if not db_path.is_absolute():
        db_path = (BASE_DIR / db_path).resolve()
    return db_path_value, db_path


def _build_read_only_uri(db_path: Path) -> str:
    return f"file:{db_path.as_posix()}?mode=ro"


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


def _required_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    columns: set[str] = set()
    for row in rows:
        if len(row) >= 2 and row[1]:
            columns.add(str(row[1]))
    return columns


def _normalize_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _normalize_required_text(value: object, field_name: str) -> str:
    text = _normalize_optional_text(value)
    if not text:
        raise RuntimeError(f"Unexpected empty value for required field: {field_name}")
    return text


def _fetch_export_records(conn: sqlite3.Connection) -> list[dict[str, object]]:
    rows = conn.execute(
        """
        SELECT
            feature,
            content_type,
            content_key,
            local_path,
            file_id,
            file_unique_id,
            checksum,
            status,
            last_error
        FROM media_assets
        WHERE feature = 'questions'
          AND content_type = 'question_audio'
          AND status = 'ready'
          AND file_id IS NOT NULL
          AND TRIM(CAST(file_id AS TEXT)) != ''
        ORDER BY content_key
        """
    ).fetchall()

    records: list[dict[str, object]] = []
    for row in rows:
        record = {
            "feature": _normalize_required_text(row[0], "feature"),
            "content_type": _normalize_required_text(row[1], "content_type"),
            "content_key": _normalize_required_text(row[2], "content_key"),
            "local_path": _normalize_required_text(row[3], "local_path"),
            "file_id": _normalize_required_text(row[4], "file_id"),
            "file_unique_id": _normalize_optional_text(row[5]),
            "checksum": _normalize_optional_text(row[6]),
            "status": _normalize_required_text(row[7], "status"),
            "last_error": _normalize_optional_text(row[8]),
        }
        records.append(record)
    return records


def _build_payload(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "export_type": EXPORT_TYPE,
        "version": EXPORT_VERSION,
        "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": len(records),
        "expected_count": EXPECTED_COUNT,
        "records": records,
    }


def _split_into_chunks(text: str, chunk_size: int) -> list[str]:
    if chunk_size <= 0:
        raise RuntimeError("chunk_size must be > 0")
    chunks = [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]
    return chunks if chunks else [""]


def _build_railway_vars_helper(chunks: list[str]) -> str:
    lines = [f"{RAILWAY_CHUNKS_VAR}={len(chunks)}"]
    for index, chunk in enumerate(chunks, start=1):
        lines.append(f"{RAILWAY_CHUNK_PREFIX}{index:03d}={chunk}")
    return "\n".join(lines) + "\n"


def _write_output_files(
    project_root: Path,
    payload: dict[str, object],
) -> tuple[Path, Path, Path, Path, int, int]:
    output_dir = project_root / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / OUTPUT_JSON
    b64_path = output_dir / OUTPUT_B64
    gzip_b64_path = output_dir / OUTPUT_GZIP_B64
    railway_vars_path = output_dir / OUTPUT_RAILWAY_VARS

    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    json_bytes = json_text.encode("utf-8")
    json_path.write_text(json_text, encoding="utf-8")

    b64_text = base64.b64encode(json_bytes).decode("ascii")
    b64_path.write_text(b64_text, encoding="ascii")

    gzip_b64_text = base64.b64encode(gzip.compress(json_bytes)).decode("ascii")
    gzip_b64_path.write_text(gzip_b64_text, encoding="ascii")

    chunks = _split_into_chunks(gzip_b64_text, CHUNK_SIZE)
    railway_vars_text = _build_railway_vars_helper(chunks)
    railway_vars_path.write_text(railway_vars_text, encoding="utf-8")

    return (
        json_path,
        b64_path,
        gzip_b64_path,
        railway_vars_path,
        len(gzip_b64_text),
        len(chunks),
    )


def main() -> int:
    project_root = PROJECT_ROOT
    configured_db_path, resolved_db_path = _resolve_db_path()

    _safe_print("=== Export question_audio media_assets ===")
    _safe_print(f"DB_PATH = {configured_db_path}")
    _safe_print(f"Resolved DB path = {resolved_db_path}")

    if not resolved_db_path.exists():
        _safe_print(f"ERROR: DB file does not exist: {resolved_db_path}")
        return 1
    if not resolved_db_path.is_file():
        _safe_print(f"ERROR: DB path is not a file: {resolved_db_path}")
        return 1

    db_uri = _build_read_only_uri(resolved_db_path)
    _safe_print(f"SQLite URI (read-only) = {db_uri}")

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_uri, uri=True)

        if not _table_exists(conn, "media_assets"):
            _safe_print("ERROR: table media_assets is missing")
            return 1

        required = {
            "feature",
            "content_type",
            "content_key",
            "local_path",
            "file_id",
            "file_unique_id",
            "checksum",
            "status",
            "last_error",
        }
        existing_columns = _required_columns(conn, "media_assets")
        missing_columns = sorted(required - existing_columns)
        if missing_columns:
            _safe_print(f"ERROR: media_assets is missing columns: {', '.join(missing_columns)}")
            return 1

        records = _fetch_export_records(conn)
        payload = _build_payload(records)
        (
            json_path,
            b64_path,
            gzip_b64_path,
            railway_vars_path,
            gzip_b64_length,
            chunk_count,
        ) = _write_output_files(project_root, payload)

        count = len(records)
        _safe_print(f"records exported: {count}")
        _safe_print(f"expected count: {EXPECTED_COUNT}")
        if count != EXPECTED_COUNT:
            _safe_print(f"WARNING: exported count != expected ({count} != {EXPECTED_COUNT})")
        _safe_print(f"json path: {json_path}")
        _safe_print(f"base64 path: {b64_path}")
        _safe_print(f"gzip base64 path: {gzip_b64_path}")
        _safe_print(f"gzip base64 length: {gzip_b64_length}")
        _safe_print(f"chunk count: {chunk_count}")
        _safe_print(f"helper file path: {railway_vars_path}")
        return 0
    except sqlite3.Error as exc:
        _safe_print(f"ERROR: SQLite failure: {_format_error(exc)}")
        return 1
    except OSError as exc:
        _safe_print(f"ERROR: cannot write export files: {_format_error(exc)}")
        return 1
    except RuntimeError as exc:
        _safe_print(f"ERROR: {exc}")
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
