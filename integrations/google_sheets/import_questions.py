"""Import questions data from Google Sheets into SQLite."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from gspread import Spreadsheet
from gspread.exceptions import APIError, WorksheetNotFound

from db.repositories.questions_repo import upsert_question


QUESTIONS_HEADERS = [
    "level",
    "question_number",
    "question_en",
    "audio_file",
    "question_translation_ru",
    "sample_answer_en",
    "sample_answer_translation_ru",
]


@dataclass(frozen=True, slots=True)
class QuestionsImportStats:
    questions_rows: int
    questions_imported: int
    level4_imported: int
    level5_imported: int


def _normalize_row(row: list[str], expected_len: int) -> list[str]:
    if len(row) >= expected_len:
        return row[:expected_len]
    return [*row, *([""] * (expected_len - len(row)))]


def _is_empty_row(row: list[str]) -> bool:
    return not any((cell or "").strip() for cell in row)


def _required_text(value: str, *, field_name: str, row_number: int, sheet_name: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"{sheet_name} row {row_number}: {field_name} is required")
    return normalized


def _required_int(value: str, *, field_name: str, row_number: int, sheet_name: str) -> int:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"{sheet_name} row {row_number}: {field_name} is required")
    try:
        return int(normalized)
    except ValueError as exc:
        raise RuntimeError(
            f"{sheet_name} row {row_number}: {field_name} must be integer"
        ) from exc


def _optional_text(value: str) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def count_non_empty_rows(rows: list[list[str]]) -> int:
    if len(rows) <= 1:
        return 0
    return sum(1 for row in rows[1:] if any((cell or "").strip() for cell in row))


def load_worksheet_rows(spreadsheet: Spreadsheet, worksheet_title: str) -> list[list[str]]:
    """Load all rows from worksheet with user-friendly errors."""
    try:
        worksheet = spreadsheet.worksheet(worksheet_title)
    except WorksheetNotFound as exc:
        raise RuntimeError(f"Worksheet not found: {worksheet_title}") from exc
    except APIError as exc:
        raise RuntimeError(
            f"Could not open worksheet: {worksheet_title}. Check sharing permissions."
        ) from exc

    try:
        return worksheet.get_all_values()
    except APIError as exc:
        raise RuntimeError(
            f"Could not read worksheet rows: {worksheet_title}. Check API access."
        ) from exc


def validate_headers(
    worksheet_title: str,
    rows: list[list[str]],
    expected_headers: list[str],
) -> None:
    """Validate worksheet headers strictly by order and title."""
    actual_headers = rows[0] if rows else []
    if actual_headers == expected_headers:
        return
    raise RuntimeError(
        f"{worksheet_title} headers mismatch\n"
        f"Expected headers: {expected_headers}\n"
        f"Actual headers:   {actual_headers}"
    )


def prepare_questions_rows(
    rows: list[list[str]],
) -> list[tuple[int, int, str, str | None, str | None, str | None, str | None]]:
    """Validate questions rows and return normalized payload for import."""
    seen_question_keys: dict[tuple[int, int], int] = {}
    prepared_rows: list[
        tuple[int, int, str, str | None, str | None, str | None, str | None]
    ] = []

    for row_number, source_row in enumerate(rows[1:], start=2):
        row = _normalize_row(source_row, len(QUESTIONS_HEADERS))
        if _is_empty_row(row):
            continue

        level = _required_int(
            row[0],
            field_name="level",
            row_number=row_number,
            sheet_name="questions",
        )
        if level not in {4, 5}:
            raise RuntimeError(f"questions row {row_number}: level must be 4 or 5")

        question_number = _required_int(
            row[1],
            field_name="question_number",
            row_number=row_number,
            sheet_name="questions",
        )
        if question_number <= 0:
            raise RuntimeError(
                f"questions row {row_number}: question_number must be positive integer"
            )

        question_key = (level, question_number)
        previous_row = seen_question_keys.get(question_key)
        if previous_row is not None:
            raise RuntimeError(
                f"questions row {row_number}: duplicate level/question_number "
                f"{level}/{question_number} already used in row {previous_row}"
            )
        seen_question_keys[question_key] = row_number

        question_en = _required_text(
            row[2],
            field_name="question_en",
            row_number=row_number,
            sheet_name="questions",
        )

        prepared_rows.append(
            (
                level,
                question_number,
                question_en,
                _optional_text(row[3]),
                _optional_text(row[4]),
                _optional_text(row[5]),
                _optional_text(row[6]),
            )
        )

    if not prepared_rows:
        raise RuntimeError("questions sheet has no data rows")

    return prepared_rows


def apply_full_refresh_rows(
    conn: sqlite3.Connection,
    prepared_rows: list[tuple[int, int, str, str | None, str | None, str | None, str | None]],
) -> tuple[int, int, int]:
    """Apply full-refresh write into exam_questions and reset user question state."""
    conn.execute("DELETE FROM exam_questions")
    conn.execute("DELETE FROM exam_question_progress")
    conn.execute("DELETE FROM exam_question_state")

    imported = 0
    level4_imported = 0
    level5_imported = 0
    for (
        level,
        question_number,
        question_en,
        audio_file,
        question_translation_ru,
        sample_answer_en,
        sample_answer_translation_ru,
    ) in prepared_rows:
        upsert_question(
            conn,
            level=level,
            question_number=question_number,
            question_en=question_en,
            audio_file=audio_file,
            question_translation_ru=question_translation_ru,
            sample_answer_en=sample_answer_en,
            sample_answer_translation_ru=sample_answer_translation_ru,
        )
        imported += 1
        if level == 4:
            level4_imported += 1
        else:
            level5_imported += 1

    return imported, level4_imported, level5_imported


def import_questions_rows(conn: sqlite3.Connection, rows: list[list[str]]) -> tuple[int, int, int]:
    """
    Import questions worksheet rows using full-refresh strategy.

    Validation happens first. Database cleanup starts only after successful validation.
    """
    prepared_rows = prepare_questions_rows(rows)
    return apply_full_refresh_rows(conn, prepared_rows)


def import_questions_from_spreadsheet(
    conn: sqlite3.Connection,
    spreadsheet: Spreadsheet,
) -> QuestionsImportStats:
    """Run full questions import from spreadsheet."""
    questions_rows = load_worksheet_rows(spreadsheet, "questions")
    validate_headers("questions", questions_rows, QUESTIONS_HEADERS)
    questions_imported, level4_imported, level5_imported = import_questions_rows(
        conn,
        questions_rows,
    )

    return QuestionsImportStats(
        questions_rows=count_non_empty_rows(questions_rows),
        questions_imported=questions_imported,
        level4_imported=level4_imported,
        level5_imported=level5_imported,
    )
