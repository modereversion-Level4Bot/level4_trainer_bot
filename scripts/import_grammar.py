"""Import grammar topics/questions from Google Sheets into SQLite."""

from __future__ import annotations

from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.connection import get_connection
from integrations.google_sheets.client import (
    build_client,
    get_google_sheet_id,
    open_spreadsheet_by_id,
)
from integrations.google_sheets.import_grammar import (
    import_grammar_from_spreadsheet,
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


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    _safe_print(
        "📘 Importing grammar from Google Sheets...",
        "Importing grammar from Google Sheets...",
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
        with get_connection() as conn:
            stats = import_grammar_from_spreadsheet(conn, spreadsheet)
    except RuntimeError as exc:
        error_message = str(exc)
        if "headers mismatch" in error_message:
            _print_header_error(error_message)
            return 1
        _print_error(error_message)
        return 1
    except Exception:
        _print_error("Unexpected error during grammar import")
        return 1

    _safe_print("✅ grammar_topics headers OK", "OK grammar_topics headers OK")
    _safe_print("✅ grammar_questions headers OK", "OK grammar_questions headers OK")
    _safe_print(
        f"📘 grammar_topics rows: {stats.topics_rows}",
        f"grammar_topics rows: {stats.topics_rows}",
    )
    _safe_print(
        f"🎯 grammar_questions rows: {stats.questions_rows}",
        f"grammar_questions rows: {stats.questions_rows}",
    )
    _safe_print(
        f"✅ grammar_topics imported: {stats.topics_imported}",
        f"OK grammar_topics imported: {stats.topics_imported}",
    )
    _safe_print(f"   main: {stats.topics_main}")
    _safe_print(f"   extra: {stats.topics_extra}")
    _safe_print(
        f"✅ grammar_questions imported: {stats.questions_imported}",
        f"OK grammar_questions imported: {stats.questions_imported}",
    )
    _safe_print(
        "ℹ️ Grammar active sync: rows absent from Sheets are marked inactive (not deleted).",
        "INFO: Grammar active sync: rows absent from Sheets are marked inactive (not deleted).",
    )
    _safe_print("✅ Grammar import completed.", "OK Grammar import completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
