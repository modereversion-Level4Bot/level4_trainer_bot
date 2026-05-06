"""Import grammar data from Google Sheets into SQLite."""

from __future__ import annotations

from dataclasses import dataclass
import sqlite3

from gspread import Spreadsheet
from gspread.exceptions import APIError, WorksheetNotFound

from db.repositories.grammar_repo import (
    deactivate_missing_questions,
    deactivate_missing_topics,
    upsert_grammar_question,
    upsert_grammar_topic,
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


@dataclass(frozen=True, slots=True)
class GrammarImportStats:
    topics_rows: int
    questions_rows: int
    topics_imported: int
    topics_main: int
    topics_extra: int
    questions_imported: int


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
    """Load all rows from worksheet with safe, user-facing errors."""
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
    """Validate headers strictly by order and title."""
    actual_headers = rows[0] if rows else []
    if actual_headers == expected_headers:
        return
    raise RuntimeError(
        f"{worksheet_title} headers mismatch\n"
        f"Expected headers: {expected_headers}\n"
        f"Actual headers:   {actual_headers}"
    )


def import_topics_rows(
    conn: sqlite3.Connection,
    rows: list[list[str]],
) -> tuple[int, int, int, set[int]]:
    """Import grammar_topics worksheet rows."""
    imported = 0
    main_count = 0
    extra_count = 0
    seen_topic_numbers: dict[int, int] = {}
    active_topic_numbers: set[int] = set()

    for row_number, source_row in enumerate(rows[1:], start=2):
        row = _normalize_row(source_row, len(GRAMMAR_TOPICS_HEADERS))
        if _is_empty_row(row):
            continue

        topic_number = _required_int(
            row[0],
            field_name="topic_number",
            row_number=row_number,
            sheet_name="grammar_topics",
        )
        previous_row = seen_topic_numbers.get(topic_number)
        if previous_row is not None:
            raise RuntimeError(
                f"grammar_topics row {row_number}: duplicate topic_number {topic_number} "
                f"(already used in row {previous_row})"
            )
        seen_topic_numbers[topic_number] = row_number
        active_topic_numbers.add(topic_number)
        topic_type = _required_text(
            row[1],
            field_name="topic_type",
            row_number=row_number,
            sheet_name="grammar_topics",
        ).lower()
        if topic_type not in {"main", "extra"}:
            raise RuntimeError(
                f"grammar_topics row {row_number}: topic_type must be 'main' or 'extra'"
            )

        topic_title_ru = _required_text(
            row[2],
            field_name="topic_title_ru",
            row_number=row_number,
            sheet_name="grammar_topics",
        )
        simple_explanation_ru = _required_text(
            row[4],
            field_name="simple_explanation_ru",
            row_number=row_number,
            sheet_name="grammar_topics",
        )

        upsert_grammar_topic(
            conn,
            topic_number=topic_number,
            topic_type=topic_type,
            topic_title_ru=topic_title_ru,
            topic_title_en=_optional_text(row[3]),
            simple_explanation_ru=simple_explanation_ru,
            simple_explanation_en=_optional_text(row[5]),
            detailed_explanation_ru=_optional_text(row[6]),
            detailed_explanation_en=_optional_text(row[7]),
        )
        imported += 1
        if topic_type == "main":
            main_count += 1
        else:
            extra_count += 1

    return imported, main_count, extra_count, active_topic_numbers


def import_questions_rows(
    conn: sqlite3.Connection,
    rows: list[list[str]],
    *,
    active_topic_numbers: set[int],
) -> tuple[int, set[tuple[int, int]]]:
    """Import grammar_questions worksheet rows."""
    imported = 0
    seen_question_keys: dict[tuple[int, int], int] = {}
    active_question_keys: set[tuple[int, int]] = set()

    for row_number, source_row in enumerate(rows[1:], start=2):
        row = _normalize_row(source_row, len(GRAMMAR_QUESTIONS_HEADERS))
        if _is_empty_row(row):
            continue

        topic_number = _required_int(
            row[0],
            field_name="topic_number",
            row_number=row_number,
            sheet_name="grammar_questions",
        )
        question_number = _required_int(
            row[1],
            field_name="question_number",
            row_number=row_number,
            sheet_name="grammar_questions",
        )
        if topic_number not in active_topic_numbers:
            raise RuntimeError(
                f"grammar_questions row {row_number}: topic_number {topic_number} "
                "is not present in grammar_topics sheet"
            )
        question_key = (topic_number, question_number)
        active_question_keys.add(question_key)
        previous_row = seen_question_keys.get(question_key)
        if previous_row is not None:
            raise RuntimeError(
                f"grammar_questions row {row_number}: duplicate question key "
                f"(topic_number={topic_number}, question_number={question_number}) "
                f"(already used in row {previous_row})"
            )
        seen_question_keys[question_key] = row_number
        question = _required_text(
            row[2],
            field_name="question",
            row_number=row_number,
            sheet_name="grammar_questions",
        )
        answer_1 = _required_text(
            row[3],
            field_name="answer_1",
            row_number=row_number,
            sheet_name="grammar_questions",
        )
        answer_2 = _required_text(
            row[4],
            field_name="answer_2",
            row_number=row_number,
            sheet_name="grammar_questions",
        )
        answer_3 = _required_text(
            row[5],
            field_name="answer_3",
            row_number=row_number,
            sheet_name="grammar_questions",
        )
        correct_answer = _required_int(
            row[6],
            field_name="correct_answer",
            row_number=row_number,
            sheet_name="grammar_questions",
        )
        if correct_answer not in {1, 2, 3}:
            raise RuntimeError(
                f"grammar_questions row {row_number}: correct_answer must be 1, 2 or 3"
            )

        wrong_explanation_ru = _required_text(
            row[7],
            field_name="wrong_explanation_ru",
            row_number=row_number,
            sheet_name="grammar_questions",
        )

        try:
            upsert_grammar_question(
                conn,
                topic_number=topic_number,
                question_number=question_number,
                question=question,
                answer_1=answer_1,
                answer_2=answer_2,
                answer_3=answer_3,
                correct_answer=correct_answer,
                wrong_explanation_ru=wrong_explanation_ru,
                wrong_explanation_en=_optional_text(row[8]),
            )
        except RuntimeError as exc:
            raise RuntimeError(f"grammar_questions row {row_number}: {exc}") from exc

        imported += 1

    return imported, active_question_keys


def import_grammar_from_spreadsheet(
    conn: sqlite3.Connection,
    spreadsheet: Spreadsheet,
) -> GrammarImportStats:
    """Run full grammar import from spreadsheet with active sync policy."""
    topics_rows = load_worksheet_rows(spreadsheet, "grammar_topics")
    questions_rows = load_worksheet_rows(spreadsheet, "grammar_questions")

    validate_headers("grammar_topics", topics_rows, GRAMMAR_TOPICS_HEADERS)
    validate_headers("grammar_questions", questions_rows, GRAMMAR_QUESTIONS_HEADERS)

    topics_imported, topics_main, topics_extra, active_topic_numbers = import_topics_rows(
        conn,
        topics_rows,
    )
    questions_imported, active_question_keys = import_questions_rows(
        conn,
        questions_rows,
        active_topic_numbers=active_topic_numbers,
    )
    deactivate_missing_topics(conn, active_topic_numbers=active_topic_numbers)
    deactivate_missing_questions(conn, active_question_keys=active_question_keys)

    return GrammarImportStats(
        topics_rows=count_non_empty_rows(topics_rows),
        questions_rows=count_non_empty_rows(questions_rows),
        topics_imported=topics_imported,
        topics_main=topics_main,
        topics_extra=topics_extra,
        questions_imported=questions_imported,
    )
