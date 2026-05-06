"""Check Google Sheets access and worksheet headers."""

from __future__ import annotations

from pathlib import Path
import sys

from dotenv import load_dotenv
from gspread.exceptions import APIError, WorksheetNotFound

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from integrations.google_sheets.client import (
    build_client,
    get_google_sheet_id,
    open_spreadsheet_by_id,
)


GRAMMAR_TOPICS_HEADERS = [
    "topic_number",
    "topic_type",
    "topic_title_ru",
    "topic_title_en",
    "simple_explanation_ru",
    "simple_explanation_en",
    "detailed_explanation_ru",
    "detailed_explanation_en",
]

GRAMMAR_QUESTIONS_HEADERS = [
    "topic_number",
    "question_number",
    "question",
    "answer_1",
    "answer_2",
    "answer_3",
    "correct_answer",
    "wrong_explanation_ru",
    "wrong_explanation_en",
]

QUESTIONS_HEADERS = [
    "level",
    "question_number",
    "question_en",
    "audio_file",
    "question_translation_ru",
    "sample_answer_en",
    "sample_answer_translation_ru",
]


def _safe_print(message: str, fallback: str | None = None) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(fallback if fallback is not None else message.encode("ascii", "replace").decode("ascii"))


def _count_non_empty_rows(rows: list[list[str]]) -> int:
    if len(rows) <= 1:
        return 0
    return sum(1 for row in rows[1:] if any((cell or "").strip() for cell in row))


def _load_worksheet_rows(spreadsheet, worksheet_title: str) -> list[list[str]]:
    try:
        worksheet = spreadsheet.worksheet(worksheet_title)
    except WorksheetNotFound as exc:
        raise RuntimeError(f"Worksheet not found: {worksheet_title}") from exc
    except APIError as exc:
        raise RuntimeError(
            f"Could not open worksheet: {worksheet_title}. Check sharing permissions."
        ) from exc

    _safe_print(
        f"✅ Worksheet found: {worksheet_title}",
        f"OK Worksheet found: {worksheet_title}",
    )

    try:
        return worksheet.get_all_values()
    except APIError as exc:
        raise RuntimeError(
            f"Could not read worksheet rows: {worksheet_title}. Check API access."
        ) from exc


def _check_headers(
    worksheet_title: str,
    expected_headers: list[str],
    actual_headers: list[str],
) -> bool:
    if actual_headers == expected_headers:
        _safe_print(f"✅ {worksheet_title} headers OK", f"OK {worksheet_title} headers OK")
        return True

    _safe_print(
        f"❌ {worksheet_title} headers mismatch",
        f"ERROR {worksheet_title} headers mismatch",
    )
    _safe_print(f"Expected headers: {expected_headers}")
    _safe_print(f"Actual headers:   {actual_headers}")
    return False


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")

    try:
        spreadsheet_id = get_google_sheet_id()
    except RuntimeError as exc:
        _safe_print(f"❌ {exc}", f"ERROR: {exc}")
        return 1

    try:
        client = build_client()
    except RuntimeError as exc:
        _safe_print(f"❌ {exc}", f"ERROR: {exc}")
        return 1
    except Exception:
        _safe_print(
            "❌ Could not authorize service account credentials",
            "ERROR: Could not authorize service account credentials",
        )
        return 1

    _safe_print("✅ Google Sheets connection OK", "OK Google Sheets connection OK")

    try:
        spreadsheet = open_spreadsheet_by_id(client, spreadsheet_id)
    except RuntimeError as exc:
        _safe_print(f"❌ {exc}", f"ERROR: {exc}")
        return 1

    _safe_print("✅ Spreadsheet opened", "OK Spreadsheet opened")

    try:
        grammar_topics_rows = _load_worksheet_rows(spreadsheet, "grammar_topics")
        grammar_questions_rows = _load_worksheet_rows(spreadsheet, "grammar_questions")
        questions_rows = _load_worksheet_rows(spreadsheet, "questions")
    except RuntimeError as exc:
        _safe_print(f"❌ {exc}", f"ERROR: {exc}")
        return 1

    topics_headers = grammar_topics_rows[0] if grammar_topics_rows else []
    questions_headers = grammar_questions_rows[0] if grammar_questions_rows else []
    exam_questions_headers = questions_rows[0] if questions_rows else []

    topics_headers_ok = _check_headers("grammar_topics", GRAMMAR_TOPICS_HEADERS, topics_headers)
    questions_headers_ok = _check_headers(
        "grammar_questions",
        GRAMMAR_QUESTIONS_HEADERS,
        questions_headers,
    )
    exam_questions_headers_ok = _check_headers("questions", QUESTIONS_HEADERS, exam_questions_headers)

    if not topics_headers_ok or not questions_headers_ok or not exam_questions_headers_ok:
        return 1

    topics_rows_count = _count_non_empty_rows(grammar_topics_rows)
    questions_rows_count = _count_non_empty_rows(grammar_questions_rows)
    exam_questions_rows_count = _count_non_empty_rows(questions_rows)
    _safe_print(
        f"📘 grammar_topics rows: {topics_rows_count}",
        f"grammar_topics rows: {topics_rows_count}",
    )
    _safe_print(
        f"🎯 grammar_questions rows: {questions_rows_count}",
        f"grammar_questions rows: {questions_rows_count}",
    )
    _safe_print(
        f"🎙 questions rows: {exam_questions_rows_count}",
        f"questions rows: {exam_questions_rows_count}",
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        _safe_print(
            "❌ Unexpected error during Google Sheets check",
            "ERROR: Unexpected error during Google Sheets check",
        )
        raise SystemExit(1)
