"""Import routes content from Google Sheets into SQLite."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.connection import get_connection, resolve_db_path
from integrations.google_sheets.client import (
    build_client,
    get_google_sheet_id,
    open_spreadsheet_by_id,
)
from integrations.google_sheets.import_routes import import_routes_from_spreadsheet


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
        description="Import routes content from Google Sheets into SQLite."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate sheets and print import summary without DB changes.",
    )
    parser.add_argument(
        "--confirm-import",
        action="store_true",
        help="Confirm real DB import (required unless --dry-run is used).",
    )
    return parser.parse_args()


def _is_production_env() -> bool:
    return os.getenv("APP_ENV", "local").strip().lower() == "production"


def main() -> int:
    args = _parse_args()
    load_dotenv(PROJECT_ROOT / ".env")
    is_production = _is_production_env()
    configured_db_path = os.getenv("DB_PATH", "").strip() or "data/local/dev_main.db"
    resolved_db_path = resolve_db_path()

    if not args.dry_run and not args.confirm_import:
        _print_error("Refusing to run import without explicit flag: use --dry-run or --confirm-import")
        return 1
    _safe_print(
        "🛫 Importing routes from Google Sheets...",
        "Importing routes from Google Sheets...",
    )
    if args.dry_run:
        _safe_print("🔎 Dry-run mode: no DB changes will be applied.", "Dry-run mode: no DB changes will be applied.")
    else:
        _safe_print("⚠️ Confirmed import mode: DB changes will be applied.", "Confirmed import mode: DB changes will be applied.")
        if is_production:
            _safe_print(
                "ℹ️ Production mode: --confirm-import check passed.",
                "INFO: Production mode: --confirm-import check passed.",
            )
    _safe_print(f"ℹ️ DB_PATH: {configured_db_path}")
    _safe_print(f"ℹ️ Resolved DB path: {resolved_db_path}")
    _safe_print(f"ℹ️ Operation mode: {'dry-run' if args.dry_run else 'confirm-import'}")
    _safe_print(
        "ℹ️ Active-sync mode: rows absent from Sheets are marked inactive (not deleted).",
        "INFO: Active-sync mode: rows absent from Sheets are marked inactive (not deleted).",
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
            stats = import_routes_from_spreadsheet(
                conn,
                spreadsheet,
                dry_run=args.dry_run,
            )
    except RuntimeError as exc:
        error_message = str(exc)
        if "headers mismatch" in error_message:
            _print_header_error(error_message)
            return 1
        _print_error(error_message)
        return 1
    except Exception:
        _print_error("Unexpected error during routes import")
        return 1

    _safe_print("✅ routes headers OK", "OK routes headers OK")
    _safe_print("✅ route_steps headers OK", "OK route_steps headers OK")
    _safe_print("✅ route_news headers OK", "OK route_news headers OK")
    _safe_print("✅ route_question_blocks headers OK", "OK route_question_blocks headers OK")
    _safe_print("✅ route_questions headers OK", "OK route_questions headers OK")

    _safe_print(
        f"🛫 routes read/upserted/active/inactivated: "
        f"{stats.routes_read}/{stats.routes_upserted}/{stats.routes_active}/{stats.routes_inactivated}"
    )
    _safe_print(
        f"🧭 steps read/upserted/active/inactivated: "
        f"{stats.steps_read}/{stats.steps_upserted}/{stats.steps_active}/{stats.steps_inactivated}"
    )
    _safe_print(
        f"📰 news read/upserted/active/inactivated: "
        f"{stats.news_read}/{stats.news_upserted}/{stats.news_active}/{stats.news_inactivated}"
    )
    _safe_print(
        f"🧱 question_blocks read/upserted/active/inactivated: "
        f"{stats.question_blocks_read}/{stats.question_blocks_upserted}/"
        f"{stats.question_blocks_active}/{stats.question_blocks_inactivated}"
    )
    _safe_print(
        f"❓ questions read/upserted/active/inactivated: "
        f"{stats.questions_read}/{stats.questions_upserted}/{stats.questions_active}/{stats.questions_inactivated}"
    )
    _safe_print(
        "ℹ️ route_progress and route_user_state are not reset in this phase.",
        "INFO: route_progress and route_user_state are not reset in this phase.",
    )
    if args.dry_run:
        _safe_print("✅ Routes dry-run completed (no DB changes).", "OK Routes dry-run completed (no DB changes).")
    else:
        _safe_print("✅ Routes import completed.", "OK Routes import completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
