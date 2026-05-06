"""Import questions from Google Sheets into SQLite."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.connection import get_connection
from integrations.google_sheets.client import (
    build_client,
    get_google_sheet_id,
    open_spreadsheet_by_id,
)
from integrations.google_sheets.import_questions import (
    QUESTIONS_HEADERS,
    apply_full_refresh_rows,
    count_non_empty_rows,
    load_worksheet_rows,
    prepare_questions_rows,
    validate_headers,
)


def _safe_print(message: str, fallback: str | None = None) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(fallback if fallback is not None else message.encode("ascii", "replace").decode("ascii"))


def _print_error(error_message: str) -> None:
    _safe_print(f"❌ {error_message}", f"ERROR: {error_message}")


def _print_header_error(error_message: str) -> None:
    lines = [line for line in error_message.splitlines() if line.strip()]
    if not lines:
        _print_error("Headers validation failed")
        return
    first_line = lines[0]
    _safe_print(f"❌ {first_line}", f"ERROR: {first_line}")
    for line in lines[1:]:
        _safe_print(line)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import questions from Google Sheets into SQLite."
    )
    parser.add_argument(
        "--allow-full-refresh",
        action="store_true",
        help="Allow full-refresh import when APP_ENV=production.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate sheet and show import summary without changing DB.",
    )
    return parser.parse_args()


def _is_production_env() -> bool:
    return os.getenv("APP_ENV", "local").strip().lower() == "production"


def main() -> int:
    args = _parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    is_production = _is_production_env()

    if is_production and not args.allow_full_refresh and not args.dry_run:
        _print_error(
            "Refusing to run full-refresh import in production without --allow-full-refresh"
        )
        return 1

    _safe_print(
        "🎙 Importing questions from Google Sheets (full-refresh)...",
        "Importing questions from Google Sheets (full-refresh)...",
    )
    if args.dry_run:
        _safe_print("🔎 Dry-run mode: no DB changes will be applied.", "Dry-run mode: no DB changes will be applied.")
    _safe_print(
        "ℹ️ Full-refresh mode clears exam_questions, exam_question_progress, exam_question_state.",
        "INFO: Full-refresh mode clears exam_questions, exam_question_progress, exam_question_state.",
    )

    try:
        spreadsheet_id = get_google_sheet_id()
        client = build_client()
        _safe_print("✅ Google Sheets connection OK", "OK Google Sheets connection OK")
        spreadsheet = open_spreadsheet_by_id(client, spreadsheet_id)
    except RuntimeError as exc:
        _print_error(str(exc))
        return 1
    except Exception:
        _print_error("Could not authorize service account credentials")
        return 1

    try:
        questions_rows = load_worksheet_rows(spreadsheet, "questions")
        _safe_print("✅ Worksheet found: questions", "OK Worksheet found: questions")
    except RuntimeError as exc:
        _print_error(str(exc))
        return 1

    try:
        validate_headers("questions", questions_rows, QUESTIONS_HEADERS)
        _safe_print("✅ questions headers OK", "OK questions headers OK")
    except RuntimeError as exc:
        _print_header_error(str(exc))
        return 1

    questions_rows_count = count_non_empty_rows(questions_rows)
    _safe_print(f"🎙 questions rows: {questions_rows_count}", f"questions rows: {questions_rows_count}")
    if questions_rows_count <= 0:
        _print_error("questions sheet has no data rows")
        return 1

    try:
        prepared_rows = prepare_questions_rows(questions_rows)
    except RuntimeError as exc:
        _print_error(str(exc))
        return 1
    except Exception:
        _print_error("Unexpected error during questions import")
        return 1

    level4_imported = sum(1 for row in prepared_rows if row[0] == 4)
    level5_imported = sum(1 for row in prepared_rows if row[0] == 5)
    questions_imported = len(prepared_rows)

    if not args.dry_run:
        _safe_print(
            "🎙 Applying full-refresh: questions + progress/state reset...",
            "Applying full-refresh: questions + progress/state reset...",
        )
        try:
            with get_connection() as conn:
                questions_imported, level4_imported, level5_imported = apply_full_refresh_rows(
                    conn,
                    prepared_rows,
                )
        except RuntimeError as exc:
            _print_error(str(exc))
            return 1
        except Exception:
            _print_error("Unexpected error during questions import")
            return 1

    _safe_print(
        f"✅ questions imported: {questions_imported}",
        f"OK questions imported: {questions_imported}",
    )
    _safe_print(f"   Level 4: {level4_imported}")
    _safe_print(f"   Level 5: {level5_imported}")
    _safe_print(
        "ℹ️ After importing questions, run: python scripts/preload_question_audio.py",
        "INFO: After importing questions, run: python scripts/preload_question_audio.py",
    )
    if args.dry_run:
        _safe_print("✅ Questions dry-run completed (no DB changes).", "OK Questions dry-run completed (no DB changes).")
    else:
        _safe_print("✅ Questions import completed.", "OK Questions import completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
