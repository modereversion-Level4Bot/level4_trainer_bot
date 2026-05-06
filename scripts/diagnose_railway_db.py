"""Read-only diagnostic for Railway SQLite database state."""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import sys


DEFAULT_DB_PATH = "/data/level4_trainer.db"

EXPECTED_GRAMMAR_TOPICS_ACTIVE = 21
EXPECTED_GRAMMAR_QUESTIONS_ACTIVE = 1500
EXPECTED_EXAM_QUESTIONS_TOTAL = 261
EXPECTED_LEVEL_4 = 131
EXPECTED_LEVEL_5 = 130
EXPECTED_QUESTIONS_AUDIO_READY = 261


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
    env_value = os.getenv("DB_PATH", "").strip()
    db_path_value = env_value if env_value else DEFAULT_DB_PATH
    db_path = Path(db_path_value).expanduser()
    if not db_path.is_absolute():
        db_path = db_path.resolve()
    return db_path_value, db_path


def _build_read_only_uri(db_path: Path) -> str:
    # SQLite URI in read-only mode prevents accidental DB creation.
    return f"file:{db_path.as_posix()}?mode=ro"


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    query = """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        LIMIT 1
    """
    row = conn.execute(query, (table_name,)).fetchone()
    return row is not None


def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    columns: set[str] = set()
    try:
        rows = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    except sqlite3.Error:
        return columns
    for row in rows:
        if len(row) >= 2 and row[1]:
            columns.add(str(row[1]))
    return columns


def _run_scalar_count(
    conn: sqlite3.Connection,
    label: str,
    sql: str,
    params: tuple[object, ...] = (),
) -> tuple[bool, int | None]:
    try:
        row = conn.execute(sql, params).fetchone()
        if row is None:
            _safe_print(f"{label}: ERROR (no result)")
            return False, None
        value = int(row[0]) if row[0] is not None else 0
        _safe_print(f"{label}: {value}")
        return True, value
    except sqlite3.Error as exc:
        _safe_print(f"{label}: ERROR ({_format_error(exc)})")
        return False, None
    except Exception as exc:  # defensive, diagnostic should continue
        _safe_print(f"{label}: ERROR ({_format_error(exc)})")
        return False, None


def _print_table_statuses(conn: sqlite3.Connection, table_names: list[str]) -> dict[str, bool]:
    _safe_print("")
    _safe_print("=== Tables ===")
    statuses: dict[str, bool] = {}
    for table_name in table_names:
        exists = _table_exists(conn, table_name)
        statuses[table_name] = exists
        _safe_print(f"{table_name}: {'OK' if exists else 'MISSING'}")
    return statuses


def _print_content_counts(
    conn: sqlite3.Connection,
    table_statuses: dict[str, bool],
    table_columns: dict[str, set[str]],
) -> dict[str, int | None]:
    _safe_print("")
    _safe_print("=== Content counts ===")
    actuals: dict[str, int | None] = {
        "grammar_topics_active": None,
        "grammar_questions_active": None,
        "exam_questions_total": None,
        "level_4": None,
        "level_5": None,
        "questions_audio_ready": None,
    }

    if table_statuses.get("grammar_topics", False):
        _, topics_total = _run_scalar_count(
            conn,
            "grammar_topics total",
            "SELECT COUNT(*) FROM grammar_topics",
        )
        if "is_active" in table_columns.get("grammar_topics", set()):
            _, topics_active = _run_scalar_count(
                conn,
                "grammar_topics active",
                "SELECT COUNT(*) FROM grammar_topics WHERE CAST(is_active AS INTEGER) = 1",
            )
            actuals["grammar_topics_active"] = topics_active
        else:
            _safe_print("grammar_topics active: SKIPPED (column is_active missing)")
    else:
        _safe_print("grammar_topics total: ERROR (table missing)")
        _safe_print("grammar_topics active: ERROR (table missing)")

    if table_statuses.get("grammar_questions", False):
        _, grammar_questions_total = _run_scalar_count(
            conn,
            "grammar_questions total",
            "SELECT COUNT(*) FROM grammar_questions",
        )
        if "is_active" in table_columns.get("grammar_questions", set()):
            _, grammar_questions_active = _run_scalar_count(
                conn,
                "grammar_questions active",
                "SELECT COUNT(*) FROM grammar_questions WHERE CAST(is_active AS INTEGER) = 1",
            )
            actuals["grammar_questions_active"] = grammar_questions_active
        else:
            _safe_print("grammar_questions active: SKIPPED (column is_active missing)")
    else:
        _safe_print("grammar_questions total: ERROR (table missing)")
        _safe_print("grammar_questions active: ERROR (table missing)")

    if table_statuses.get("exam_questions", False):
        _, exam_total = _run_scalar_count(
            conn,
            "exam_questions total",
            "SELECT COUNT(*) FROM exam_questions",
        )
        actuals["exam_questions_total"] = exam_total

        _, level_4 = _run_scalar_count(
            conn,
            "exam_questions level 4",
            "SELECT COUNT(*) FROM exam_questions WHERE CAST(level AS TEXT) = '4'",
        )
        actuals["level_4"] = level_4

        _, level_5 = _run_scalar_count(
            conn,
            "exam_questions level 5",
            "SELECT COUNT(*) FROM exam_questions WHERE CAST(level AS TEXT) = '5'",
        )
        actuals["level_5"] = level_5

        if "audio_file" in table_columns.get("exam_questions", set()):
            _run_scalar_count(
                conn,
                "exam_questions with non-empty audio_file",
                "SELECT COUNT(*) FROM exam_questions WHERE audio_file IS NOT NULL AND TRIM(CAST(audio_file AS TEXT)) != ''",
            )
        else:
            _safe_print("exam_questions with non-empty audio_file: SKIPPED (column audio_file missing)")
    else:
        _safe_print("exam_questions total: ERROR (table missing)")
        _safe_print("exam_questions level 4: ERROR (table missing)")
        _safe_print("exam_questions level 5: ERROR (table missing)")
        _safe_print("exam_questions with non-empty audio_file: ERROR (table missing)")

    return actuals


def _print_media_assets(
    conn: sqlite3.Connection,
    table_statuses: dict[str, bool],
    table_columns: dict[str, set[str]],
) -> int | None:
    _safe_print("")
    _safe_print("=== Media assets ===")
    if not table_statuses.get("media_assets", False):
        _safe_print("media_assets total: ERROR (table missing)")
        _safe_print("media_assets status breakdown: ERROR (table missing)")
        _safe_print("media_assets ready total: ERROR (table missing)")
        _safe_print("media_assets not ready total: ERROR (table missing)")
        _safe_print("questions audio ready: ERROR (table missing)")
        _safe_print("media_assets with non-empty file_id: ERROR (table missing)")
        _safe_print("questions audio with non-empty file_id: ERROR (table missing)")
        _safe_print("")
        _safe_print("questions/audio not-ready sample (up to 10): ERROR (table missing)")
        return None

    columns = table_columns.get("media_assets", set())
    _run_scalar_count(conn, "media_assets total", "SELECT COUNT(*) FROM media_assets")

    if "status" in columns:
        _safe_print("media_assets status breakdown:")
        try:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM media_assets GROUP BY status ORDER BY status"
            ).fetchall()
            if not rows:
                _safe_print("  (empty)")
            else:
                for status, count_value in rows:
                    display_status = "NULL" if status is None else str(status)
                    _safe_print(f"  {display_status}: {int(count_value)}")
        except sqlite3.Error as exc:
            _safe_print(f"media_assets status breakdown: ERROR ({_format_error(exc)})")
    else:
        _safe_print("media_assets status breakdown: SKIPPED (column status missing)")

    if "status" in columns:
        _run_scalar_count(
            conn,
            "media_assets ready total",
            "SELECT COUNT(*) FROM media_assets WHERE status = 'ready'",
        )
        _run_scalar_count(
            conn,
            "media_assets not ready total",
            "SELECT COUNT(*) FROM media_assets WHERE status IS NULL OR status != 'ready'",
        )
    else:
        _safe_print("media_assets ready total: SKIPPED (column status missing)")
        _safe_print("media_assets not ready total: SKIPPED (column status missing)")

    required_for_ready = {"feature", "content_type", "status"}
    questions_audio_ready: int | None = None
    if required_for_ready.issubset(columns):
        _, questions_audio_ready = _run_scalar_count(
            conn,
            "questions audio ready",
            """
            SELECT COUNT(*)
            FROM media_assets
            WHERE feature = 'questions'
              AND content_type = 'question_audio'
              AND status = 'ready'
            """,
        )
        _run_scalar_count(
            conn,
            "questions audio ready (legacy content_type='audio')",
            """
            SELECT COUNT(*)
            FROM media_assets
            WHERE feature = 'questions'
              AND content_type = 'audio'
              AND status = 'ready'
            """,
        )
    else:
        missing = sorted(required_for_ready - columns)
        _safe_print(f"questions audio ready: SKIPPED (missing columns: {', '.join(missing)})")

    if "file_id" in columns:
        _run_scalar_count(
            conn,
            "media_assets with non-empty file_id",
            "SELECT COUNT(*) FROM media_assets WHERE file_id IS NOT NULL AND TRIM(CAST(file_id AS TEXT)) != ''",
        )
    else:
        _safe_print("media_assets with non-empty file_id: SKIPPED (column file_id missing)")

    required_for_questions_file_id = {"feature", "content_type", "file_id"}
    if required_for_questions_file_id.issubset(columns):
        _run_scalar_count(
            conn,
            "questions audio with non-empty file_id",
            """
            SELECT COUNT(*)
            FROM media_assets
            WHERE feature = 'questions'
              AND content_type = 'question_audio'
              AND file_id IS NOT NULL
              AND TRIM(CAST(file_id AS TEXT)) != ''
            """,
        )
        _run_scalar_count(
            conn,
            "questions audio with non-empty file_id (legacy content_type='audio')",
            """
            SELECT COUNT(*)
            FROM media_assets
            WHERE feature = 'questions'
              AND content_type = 'audio'
              AND file_id IS NOT NULL
              AND TRIM(CAST(file_id AS TEXT)) != ''
            """,
        )
    else:
        missing = sorted(required_for_questions_file_id - columns)
        _safe_print(
            "questions audio with non-empty file_id: "
            f"SKIPPED (missing columns: {', '.join(missing)})"
        )

    _safe_print("")
    _safe_print("questions/audio not-ready sample (up to 10):")
    required_for_sample = {"feature", "content_type", "content_key", "local_path", "status", "last_error"}
    if required_for_sample.issubset(columns):
        try:
            rows = conn.execute(
                """
                SELECT content_key, local_path, status, last_error
                FROM media_assets
                WHERE feature = 'questions'
                  AND content_type = 'question_audio'
                  AND (status IS NULL OR status != 'ready')
                ORDER BY content_key
                LIMIT 10
                """
            ).fetchall()
            if not rows:
                _safe_print("  none")
            else:
                for index, row in enumerate(rows, start=1):
                    content_key = "" if row[0] is None else str(row[0])
                    local_path = "" if row[1] is None else str(row[1])
                    status = "NULL" if row[2] is None else str(row[2])
                    last_error = "" if row[3] is None else str(row[3])
                    _safe_print(f"  #{index}")
                    _safe_print(f"    content_key: {content_key}")
                    _safe_print(f"    local_path: {local_path}")
                    _safe_print(f"    status: {status}")
                    _safe_print(f"    last_error: {last_error}")
        except sqlite3.Error as exc:
            _safe_print(f"  ERROR ({_format_error(exc)})")
    else:
        missing = sorted(required_for_sample - columns)
        _safe_print(f"  SKIPPED (missing columns: {', '.join(missing)})")

    return questions_audio_ready


def _print_temporary_messages(
    conn: sqlite3.Connection,
    table_statuses: dict[str, bool],
) -> None:
    _safe_print("")
    _safe_print("=== Temporary messages ===")
    if not table_statuses.get("temporary_messages", False):
        _safe_print("temporary_messages total: ERROR (table missing)")
        return
    _run_scalar_count(
        conn,
        "temporary_messages total",
        "SELECT COUNT(*) FROM temporary_messages",
    )


def _print_interpretation_hints(actuals: dict[str, int | None]) -> None:
    _safe_print("")
    _safe_print("=== Interpretation hints ===")
    checks = [
        ("EXPECTED_GRAMMAR_TOPICS_ACTIVE", EXPECTED_GRAMMAR_TOPICS_ACTIVE, actuals.get("grammar_topics_active")),
        (
            "EXPECTED_GRAMMAR_QUESTIONS_ACTIVE",
            EXPECTED_GRAMMAR_QUESTIONS_ACTIVE,
            actuals.get("grammar_questions_active"),
        ),
        ("EXPECTED_EXAM_QUESTIONS_TOTAL", EXPECTED_EXAM_QUESTIONS_TOTAL, actuals.get("exam_questions_total")),
        ("EXPECTED_LEVEL_4", EXPECTED_LEVEL_4, actuals.get("level_4")),
        ("EXPECTED_LEVEL_5", EXPECTED_LEVEL_5, actuals.get("level_5")),
        ("EXPECTED_QUESTIONS_AUDIO_READY", EXPECTED_QUESTIONS_AUDIO_READY, actuals.get("questions_audio_ready")),
    ]
    for name, expected, actual in checks:
        if actual is None:
            _safe_print(f"{name}: expected={expected}, actual=N/A")
        else:
            _safe_print(f"{name}: expected={expected}, actual={actual}")


def main() -> int:
    configured_db_path, resolved_db_path = _resolve_db_path()

    _safe_print("=== Railway DB Diagnostic ===")
    _safe_print(f"DB_PATH = {configured_db_path}")

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

        tables_to_check = [
            "users",
            "grammar_topics",
            "grammar_questions",
            "exam_questions",
            "media_assets",
            "temporary_messages",
        ]
        table_statuses = _print_table_statuses(conn, tables_to_check)

        table_columns = {
            table_name: _get_table_columns(conn, table_name) if table_statuses.get(table_name, False) else set()
            for table_name in tables_to_check
        }

        actuals = _print_content_counts(conn, table_statuses, table_columns)
        questions_audio_ready = _print_media_assets(conn, table_statuses, table_columns)
        actuals["questions_audio_ready"] = questions_audio_ready
        _print_temporary_messages(conn, table_statuses)
        _print_interpretation_hints(actuals)
        return 0
    except sqlite3.Error as exc:
        _safe_print(f"ERROR: Cannot open DB in read-only mode: {_format_error(exc)}")
        return 1
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
