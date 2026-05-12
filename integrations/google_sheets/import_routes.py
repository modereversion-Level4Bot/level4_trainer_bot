"""Import routes data from Google Sheets into SQLite."""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
import sqlite3

from gspread import Spreadsheet
from gspread.exceptions import APIError, WorksheetNotFound

from db.repositories.routes_repo import (
    deactivate_route_questions_absent_blocks,
    deactivate_route_news_absent,
    deactivate_route_question_blocks_absent,
    deactivate_route_questions_absent,
    deactivate_route_steps_absent,
    deactivate_routes_absent,
    get_question_block_id,
    get_route_id_by_code,
    upsert_route,
    upsert_route_news,
    upsert_route_question,
    upsert_route_question_block,
    upsert_route_step,
)


ROUTES_HEADERS = [
    "route_id",
    "route_order",
    "title_ru",
    "title_en",
    "briefing_ru",
    "briefing_en",
    "image_file",
    "is_active",
]

ROUTE_STEPS_HEADERS = [
    "route_id",
    "step_number",
    "step_type",
    "text_ru",
    "text_en",
    "image_file",
    "audio_file",
    "transcript_ru",
    "transcript_en",
    "pilot_answer_ru",
    "pilot_answer_en",
    "is_active",
]

ROUTE_NEWS_HEADERS = [
    "route_id",
    "news_id",
    "news_order",
    "image_file",
    "audio_file",
    "transcript_ru",
    "transcript_en",
    "is_active",
]

ROUTE_QUESTION_BLOCKS_HEADERS = [
    "route_id",
    "block_id",
    "block_order",
    "is_active",
]

ROUTE_QUESTIONS_HEADERS = [
    "route_id",
    "block_id",
    "question_number",
    "question_en",
    "question_translation_ru",
    "image_file",
    "is_active",
]

ALLOWED_STEP_TYPES = {"atis", "atc_command", "situation", "info"}


@dataclass(frozen=True, slots=True)
class RouteSheetRow:
    route_code: str
    route_order: int
    title_ru: str
    title_en: str | None
    briefing_ru: str
    briefing_en: str | None
    image_file: str | None
    is_active: int


@dataclass(frozen=True, slots=True)
class RouteStepSheetRow:
    route_code: str
    step_number: int
    step_type: str
    text_ru: str | None
    text_en: str | None
    image_file: str | None
    audio_file: str | None
    transcript_ru: str | None
    transcript_en: str | None
    pilot_answer_ru: str | None
    pilot_answer_en: str | None
    is_active: int


@dataclass(frozen=True, slots=True)
class RouteNewsSheetRow:
    route_code: str
    news_code: str
    news_order: int
    image_file: str | None
    audio_file: str | None
    transcript_ru: str | None
    transcript_en: str | None
    is_active: int


@dataclass(frozen=True, slots=True)
class RouteQuestionBlockSheetRow:
    route_code: str
    block_code: str
    block_order: int
    is_active: int


@dataclass(frozen=True, slots=True)
class RouteQuestionSheetRow:
    route_code: str
    block_code: str
    question_number: int
    question_en: str
    question_translation_ru: str | None
    image_file: str | None
    is_active: int


@dataclass(frozen=True, slots=True)
class RoutesImportPayload:
    routes: list[RouteSheetRow]
    steps: list[RouteStepSheetRow]
    news: list[RouteNewsSheetRow]
    question_blocks: list[RouteQuestionBlockSheetRow]
    questions: list[RouteQuestionSheetRow]


@dataclass(frozen=True, slots=True)
class RoutesImportStats:
    routes_read: int
    routes_upserted: int
    routes_active: int
    routes_inactivated: int
    steps_read: int
    steps_upserted: int
    steps_active: int
    steps_inactivated: int
    news_read: int
    news_upserted: int
    news_active: int
    news_inactivated: int
    question_blocks_read: int
    question_blocks_upserted: int
    question_blocks_active: int
    question_blocks_inactivated: int
    questions_read: int
    questions_upserted: int
    questions_active: int
    questions_inactivated: int


def _normalize_row(row: list[str], expected_len: int) -> list[str]:
    if len(row) >= expected_len:
        return row[:expected_len]
    return [*row, *([""] * (expected_len - len(row)))]


def _is_empty_row(row: list[str]) -> bool:
    return not any((cell or "").strip() for cell in row)


def _required_text(
    value: str,
    *,
    field_name: str,
    row_number: int,
    sheet_name: str,
) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"{sheet_name} row {row_number}: {field_name} is required")
    return normalized


def _required_int(
    value: str,
    *,
    field_name: str,
    row_number: int,
    sheet_name: str,
) -> int:
    normalized = (value or "").strip()
    if not normalized:
        raise RuntimeError(f"{sheet_name} row {row_number}: {field_name} is required")
    try:
        return int(normalized)
    except ValueError as exc:
        raise RuntimeError(
            f"{sheet_name} row {row_number}: {field_name} must be integer"
        ) from exc


def _required_positive_int(
    value: str,
    *,
    field_name: str,
    row_number: int,
    sheet_name: str,
) -> int:
    normalized = _required_int(
        value,
        field_name=field_name,
        row_number=row_number,
        sheet_name=sheet_name,
    )
    if normalized <= 0:
        raise RuntimeError(
            f"{sheet_name} row {row_number}: {field_name} must be positive integer"
        )
    return normalized


def _required_flag_01(
    value: str,
    *,
    field_name: str,
    row_number: int,
    sheet_name: str,
) -> int:
    normalized = _required_text(
        value,
        field_name=field_name,
        row_number=row_number,
        sheet_name=sheet_name,
    )
    if normalized not in {"0", "1"}:
        raise RuntimeError(f"{sheet_name} row {row_number}: {field_name} must be 0 or 1")
    return int(normalized)


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
    """Validate worksheet headers strictly by order and title."""
    actual_headers = rows[0] if rows else []
    if actual_headers == expected_headers:
        return
    raise RuntimeError(
        f"{worksheet_title} headers mismatch\n"
        f"Expected headers: {expected_headers}\n"
        f"Actual headers:   {actual_headers}"
    )


def _parse_routes_rows(rows: list[list[str]]) -> list[RouteSheetRow]:
    parsed: list[RouteSheetRow] = []
    seen_route_codes: dict[str, int] = {}
    for row_number, source_row in enumerate(rows[1:], start=2):
        row = _normalize_row(source_row, len(ROUTES_HEADERS))
        if _is_empty_row(row):
            continue

        route_code = _required_text(
            row[0],
            field_name="route_id",
            row_number=row_number,
            sheet_name="routes",
        )
        previous_row = seen_route_codes.get(route_code)
        if previous_row is not None:
            raise RuntimeError(
                f"routes row {row_number}: duplicate route_id {route_code} "
                f"(already used in row {previous_row})"
            )
        seen_route_codes[route_code] = row_number
        parsed.append(
            RouteSheetRow(
                route_code=route_code,
                route_order=_required_int(
                    row[1],
                    field_name="route_order",
                    row_number=row_number,
                    sheet_name="routes",
                ),
                title_ru=_required_text(
                    row[2],
                    field_name="title_ru",
                    row_number=row_number,
                    sheet_name="routes",
                ),
                title_en=_optional_text(row[3]),
                briefing_ru=_required_text(
                    row[4],
                    field_name="briefing_ru",
                    row_number=row_number,
                    sheet_name="routes",
                ),
                briefing_en=_optional_text(row[5]),
                image_file=_optional_text(row[6]),
                is_active=_required_flag_01(
                    row[7],
                    field_name="is_active",
                    row_number=row_number,
                    sheet_name="routes",
                ),
            )
        )
    return parsed


def _parse_route_steps_rows(
    rows: list[list[str]],
    *,
    route_codes: set[str],
) -> list[RouteStepSheetRow]:
    parsed: list[RouteStepSheetRow] = []
    seen_keys: dict[tuple[str, int], int] = {}
    for row_number, source_row in enumerate(rows[1:], start=2):
        row = _normalize_row(source_row, len(ROUTE_STEPS_HEADERS))
        if _is_empty_row(row):
            continue

        route_code = _required_text(
            row[0],
            field_name="route_id",
            row_number=row_number,
            sheet_name="route_steps",
        )
        if route_code not in route_codes:
            raise RuntimeError(
                f"route_steps row {row_number}: route_id {route_code} "
                "is not present in routes sheet"
            )
        step_number = _required_positive_int(
            row[1],
            field_name="step_number",
            row_number=row_number,
            sheet_name="route_steps",
        )
        key = (route_code, step_number)
        previous_row = seen_keys.get(key)
        if previous_row is not None:
            raise RuntimeError(
                f"route_steps row {row_number}: duplicate key "
                f"(route_id={route_code}, step_number={step_number}) "
                f"(already used in row {previous_row})"
            )
        seen_keys[key] = row_number
        step_type = _required_text(
            row[2],
            field_name="step_type",
            row_number=row_number,
            sheet_name="route_steps",
        ).lower()
        if step_type == "pilot_prompt":
            raise RuntimeError(
                f"route_steps row {row_number}: Unsupported step_type 'pilot_prompt'. "
                "Use 'info' or 'situation' with pilot_answer fields instead."
            )
        if step_type not in ALLOWED_STEP_TYPES:
            allowed = ", ".join(sorted(ALLOWED_STEP_TYPES))
            raise RuntimeError(
                f"route_steps row {row_number}: step_type must be one of: {allowed}"
            )

        parsed.append(
            RouteStepSheetRow(
                route_code=route_code,
                step_number=step_number,
                step_type=step_type,
                text_ru=_optional_text(row[3]),
                text_en=_optional_text(row[4]),
                image_file=_optional_text(row[5]),
                audio_file=_optional_text(row[6]),
                transcript_ru=_optional_text(row[7]),
                transcript_en=_optional_text(row[8]),
                pilot_answer_ru=_optional_text(row[9]),
                pilot_answer_en=_optional_text(row[10]),
                is_active=_required_flag_01(
                    row[11],
                    field_name="is_active",
                    row_number=row_number,
                    sheet_name="route_steps",
                ),
            )
        )
    return parsed


def _parse_route_news_rows(
    rows: list[list[str]],
    *,
    route_codes: set[str],
) -> list[RouteNewsSheetRow]:
    parsed: list[RouteNewsSheetRow] = []
    seen_keys: dict[tuple[str, str], int] = {}
    for row_number, source_row in enumerate(rows[1:], start=2):
        row = _normalize_row(source_row, len(ROUTE_NEWS_HEADERS))
        if _is_empty_row(row):
            continue

        route_code = _required_text(
            row[0],
            field_name="route_id",
            row_number=row_number,
            sheet_name="route_news",
        )
        if route_code not in route_codes:
            raise RuntimeError(
                f"route_news row {row_number}: route_id {route_code} "
                "is not present in routes sheet"
            )
        news_code = _required_text(
            row[1],
            field_name="news_id",
            row_number=row_number,
            sheet_name="route_news",
        )
        key = (route_code, news_code)
        previous_row = seen_keys.get(key)
        if previous_row is not None:
            raise RuntimeError(
                f"route_news row {row_number}: duplicate key "
                f"(route_id={route_code}, news_id={news_code}) "
                f"(already used in row {previous_row})"
            )
        seen_keys[key] = row_number

        parsed.append(
            RouteNewsSheetRow(
                route_code=route_code,
                news_code=news_code,
                news_order=_required_int(
                    row[2],
                    field_name="news_order",
                    row_number=row_number,
                    sheet_name="route_news",
                ),
                image_file=_optional_text(row[3]),
                audio_file=_optional_text(row[4]),
                transcript_ru=_optional_text(row[5]),
                transcript_en=_optional_text(row[6]),
                is_active=_required_flag_01(
                    row[7],
                    field_name="is_active",
                    row_number=row_number,
                    sheet_name="route_news",
                ),
            )
        )
    return parsed


def _parse_route_question_blocks_rows(
    rows: list[list[str]],
    *,
    route_codes: set[str],
) -> list[RouteQuestionBlockSheetRow]:
    parsed: list[RouteQuestionBlockSheetRow] = []
    seen_keys: dict[tuple[str, str], int] = {}
    for row_number, source_row in enumerate(rows[1:], start=2):
        row = _normalize_row(source_row, len(ROUTE_QUESTION_BLOCKS_HEADERS))
        if _is_empty_row(row):
            continue

        route_code = _required_text(
            row[0],
            field_name="route_id",
            row_number=row_number,
            sheet_name="route_question_blocks",
        )
        if route_code not in route_codes:
            raise RuntimeError(
                f"route_question_blocks row {row_number}: route_id {route_code} "
                "is not present in routes sheet"
            )
        block_code = _required_text(
            row[1],
            field_name="block_id",
            row_number=row_number,
            sheet_name="route_question_blocks",
        )
        key = (route_code, block_code)
        previous_row = seen_keys.get(key)
        if previous_row is not None:
            raise RuntimeError(
                f"route_question_blocks row {row_number}: duplicate key "
                f"(route_id={route_code}, block_id={block_code}) "
                f"(already used in row {previous_row})"
            )
        seen_keys[key] = row_number
        parsed.append(
            RouteQuestionBlockSheetRow(
                route_code=route_code,
                block_code=block_code,
                block_order=_required_int(
                    row[2],
                    field_name="block_order",
                    row_number=row_number,
                    sheet_name="route_question_blocks",
                ),
                is_active=_required_flag_01(
                    row[3],
                    field_name="is_active",
                    row_number=row_number,
                    sheet_name="route_question_blocks",
                ),
            )
        )
    return parsed


def _parse_route_questions_rows(
    rows: list[list[str]],
    *,
    route_codes: set[str],
    route_block_keys: set[tuple[str, str]],
) -> list[RouteQuestionSheetRow]:
    parsed: list[RouteQuestionSheetRow] = []
    seen_keys: dict[tuple[str, str, int], int] = {}
    for row_number, source_row in enumerate(rows[1:], start=2):
        row = _normalize_row(source_row, len(ROUTE_QUESTIONS_HEADERS))
        if _is_empty_row(row):
            continue

        route_code = _required_text(
            row[0],
            field_name="route_id",
            row_number=row_number,
            sheet_name="route_questions",
        )
        if route_code not in route_codes:
            raise RuntimeError(
                f"route_questions row {row_number}: route_id {route_code} "
                "is not present in routes sheet"
            )
        block_code = _required_text(
            row[1],
            field_name="block_id",
            row_number=row_number,
            sheet_name="route_questions",
        )
        if (route_code, block_code) not in route_block_keys:
            raise RuntimeError(
                f"route_questions row {row_number}: block_id {block_code} for route_id "
                f"{route_code} is not present in route_question_blocks sheet"
            )
        question_number = _required_positive_int(
            row[2],
            field_name="question_number",
            row_number=row_number,
            sheet_name="route_questions",
        )
        key = (route_code, block_code, question_number)
        previous_row = seen_keys.get(key)
        if previous_row is not None:
            raise RuntimeError(
                f"route_questions row {row_number}: duplicate key "
                f"(route_id={route_code}, block_id={block_code}, "
                f"question_number={question_number}) "
                f"(already used in row {previous_row})"
            )
        seen_keys[key] = row_number
        parsed.append(
            RouteQuestionSheetRow(
                route_code=route_code,
                block_code=block_code,
                question_number=question_number,
                question_en=_required_text(
                    row[3],
                    field_name="question_en",
                    row_number=row_number,
                    sheet_name="route_questions",
                ),
                question_translation_ru=_optional_text(row[4]),
                image_file=_optional_text(row[5]),
                is_active=_required_flag_01(
                    row[6],
                    field_name="is_active",
                    row_number=row_number,
                    sheet_name="route_questions",
                ),
            )
        )
    return parsed


def build_routes_import_payload(spreadsheet: Spreadsheet) -> RoutesImportPayload:
    """Load, validate, and normalize all routes worksheets."""
    routes_rows = load_worksheet_rows(spreadsheet, "routes")
    route_steps_rows = load_worksheet_rows(spreadsheet, "route_steps")
    route_news_rows = load_worksheet_rows(spreadsheet, "route_news")
    route_question_blocks_rows = load_worksheet_rows(spreadsheet, "route_question_blocks")
    route_questions_rows = load_worksheet_rows(spreadsheet, "route_questions")

    validate_headers("routes", routes_rows, ROUTES_HEADERS)
    validate_headers("route_steps", route_steps_rows, ROUTE_STEPS_HEADERS)
    validate_headers("route_news", route_news_rows, ROUTE_NEWS_HEADERS)
    validate_headers(
        "route_question_blocks",
        route_question_blocks_rows,
        ROUTE_QUESTION_BLOCKS_HEADERS,
    )
    validate_headers("route_questions", route_questions_rows, ROUTE_QUESTIONS_HEADERS)

    routes = _parse_routes_rows(routes_rows)
    if not routes:
        raise RuntimeError(
            "routes sheet has no route rows; refusing to active-sync empty routes content"
        )
    route_codes = {item.route_code for item in routes}
    steps = _parse_route_steps_rows(route_steps_rows, route_codes=route_codes)
    news = _parse_route_news_rows(route_news_rows, route_codes=route_codes)
    question_blocks = _parse_route_question_blocks_rows(
        route_question_blocks_rows,
        route_codes=route_codes,
    )
    route_block_keys = {(item.route_code, item.block_code) for item in question_blocks}
    questions = _parse_route_questions_rows(
        route_questions_rows,
        route_codes=route_codes,
        route_block_keys=route_block_keys,
    )
    return RoutesImportPayload(
        routes=routes,
        steps=steps,
        news=news,
        question_blocks=question_blocks,
        questions=questions,
    )


def _build_dry_run_stats(payload: RoutesImportPayload) -> RoutesImportStats:
    return RoutesImportStats(
        routes_read=len(payload.routes),
        routes_upserted=len(payload.routes),
        routes_active=sum(1 for row in payload.routes if row.is_active == 1),
        routes_inactivated=sum(1 for row in payload.routes if row.is_active == 0),
        steps_read=len(payload.steps),
        steps_upserted=len(payload.steps),
        steps_active=sum(1 for row in payload.steps if row.is_active == 1),
        steps_inactivated=sum(1 for row in payload.steps if row.is_active == 0),
        news_read=len(payload.news),
        news_upserted=len(payload.news),
        news_active=sum(1 for row in payload.news if row.is_active == 1),
        news_inactivated=sum(1 for row in payload.news if row.is_active == 0),
        question_blocks_read=len(payload.question_blocks),
        question_blocks_upserted=len(payload.question_blocks),
        question_blocks_active=sum(
            1 for row in payload.question_blocks if row.is_active == 1
        ),
        question_blocks_inactivated=sum(
            1 for row in payload.question_blocks if row.is_active == 0
        ),
        questions_read=len(payload.questions),
        questions_upserted=len(payload.questions),
        questions_active=sum(1 for row in payload.questions if row.is_active == 1),
        questions_inactivated=sum(1 for row in payload.questions if row.is_active == 0),
    )


def _apply_routes_import(
    conn: sqlite3.Connection,
    payload: RoutesImportPayload,
) -> RoutesImportStats:
    route_ids_by_code: dict[str, int] = {}
    for route in payload.routes:
        upsert_route(
            conn,
            route_code=route.route_code,
            route_order=route.route_order,
            title_ru=route.title_ru,
            title_en=route.title_en,
            briefing_ru=route.briefing_ru,
            briefing_en=route.briefing_en,
            image_file=route.image_file,
            is_active=route.is_active,
        )
        route_id = get_route_id_by_code(conn, route_code=route.route_code)
        if route_id is None:
            raise RuntimeError(
                f"Failed to resolve route id after upsert for route_id={route.route_code}"
            )
        route_ids_by_code[route.route_code] = route_id

    routes_inactivated = sum(1 for row in payload.routes if row.is_active == 0)
    routes_inactivated += deactivate_routes_absent(
        conn,
        route_codes={row.route_code for row in payload.routes},
    )

    steps_by_route: dict[str, set[int]] = defaultdict(set)
    for step in payload.steps:
        route_id = route_ids_by_code[step.route_code]
        upsert_route_step(
            conn,
            route_id=route_id,
            step_number=step.step_number,
            step_type=step.step_type,
            text_ru=step.text_ru,
            text_en=step.text_en,
            image_file=step.image_file,
            audio_file=step.audio_file,
            transcript_ru=step.transcript_ru,
            transcript_en=step.transcript_en,
            pilot_answer_ru=step.pilot_answer_ru,
            pilot_answer_en=step.pilot_answer_en,
            is_active=step.is_active,
        )
        steps_by_route[step.route_code].add(step.step_number)

    steps_inactivated = sum(1 for row in payload.steps if row.is_active == 0)
    for route in payload.routes:
        steps_inactivated += deactivate_route_steps_absent(
            conn,
            route_id=route_ids_by_code[route.route_code],
            step_numbers=steps_by_route.get(route.route_code, set()),
        )

    news_by_route: dict[str, set[str]] = defaultdict(set)
    for news_item in payload.news:
        route_id = route_ids_by_code[news_item.route_code]
        upsert_route_news(
            conn,
            route_id=route_id,
            news_code=news_item.news_code,
            news_order=news_item.news_order,
            image_file=news_item.image_file,
            audio_file=news_item.audio_file,
            transcript_ru=news_item.transcript_ru,
            transcript_en=news_item.transcript_en,
            is_active=news_item.is_active,
        )
        news_by_route[news_item.route_code].add(news_item.news_code)

    news_inactivated = sum(1 for row in payload.news if row.is_active == 0)
    for route in payload.routes:
        news_inactivated += deactivate_route_news_absent(
            conn,
            route_id=route_ids_by_code[route.route_code],
            news_codes=news_by_route.get(route.route_code, set()),
        )

    blocks_by_route: dict[str, set[str]] = defaultdict(set)
    block_ids_by_key: dict[tuple[str, str], int] = {}
    for block in payload.question_blocks:
        route_id = route_ids_by_code[block.route_code]
        upsert_route_question_block(
            conn,
            route_id=route_id,
            block_code=block.block_code,
            block_order=block.block_order,
            is_active=block.is_active,
        )
        block_id = get_question_block_id(
            conn,
            route_id=route_id,
            block_code=block.block_code,
        )
        if block_id is None:
            raise RuntimeError(
                "Failed to resolve route question block id after upsert for "
                f"route_id={block.route_code}, block_id={block.block_code}"
            )
        block_ids_by_key[(block.route_code, block.block_code)] = block_id
        blocks_by_route[block.route_code].add(block.block_code)

    question_blocks_inactivated = sum(1 for row in payload.question_blocks if row.is_active == 0)
    for route in payload.routes:
        question_blocks_inactivated += deactivate_route_question_blocks_absent(
            conn,
            route_id=route_ids_by_code[route.route_code],
            block_codes=blocks_by_route.get(route.route_code, set()),
        )

    questions_by_route_block: dict[tuple[str, str], set[int]] = defaultdict(set)
    block_ids_by_route: dict[str, set[int]] = defaultdict(set)
    for route_code, block_code in block_ids_by_key:
        block_ids_by_route[route_code].add(block_ids_by_key[(route_code, block_code)])

    questions_inactivated = sum(1 for row in payload.questions if row.is_active == 0)
    for route in payload.routes:
        questions_inactivated += deactivate_route_questions_absent_blocks(
            conn,
            route_id=route_ids_by_code[route.route_code],
            block_ids=block_ids_by_route.get(route.route_code, set()),
        )

    for question in payload.questions:
        route_id = route_ids_by_code[question.route_code]
        block_key = (question.route_code, question.block_code)
        block_id = block_ids_by_key.get(block_key)
        if block_id is None:
            raise RuntimeError(
                f"Missing block mapping for route_id={question.route_code}, "
                f"block_id={question.block_code}"
            )
        upsert_route_question(
            conn,
            route_id=route_id,
            block_id=block_id,
            question_number=question.question_number,
            question_en=question.question_en,
            question_translation_ru=question.question_translation_ru,
            image_file=question.image_file,
            is_active=question.is_active,
        )
        questions_by_route_block[block_key].add(question.question_number)

    for block in payload.question_blocks:
        block_key = (block.route_code, block.block_code)
        block_id = block_ids_by_key[block_key]
        questions_inactivated += deactivate_route_questions_absent(
            conn,
            route_id=route_ids_by_code[block.route_code],
            block_id=block_id,
            question_numbers=questions_by_route_block.get(block_key, set()),
        )

    return RoutesImportStats(
        routes_read=len(payload.routes),
        routes_upserted=len(payload.routes),
        routes_active=sum(1 for row in payload.routes if row.is_active == 1),
        routes_inactivated=routes_inactivated,
        steps_read=len(payload.steps),
        steps_upserted=len(payload.steps),
        steps_active=sum(1 for row in payload.steps if row.is_active == 1),
        steps_inactivated=steps_inactivated,
        news_read=len(payload.news),
        news_upserted=len(payload.news),
        news_active=sum(1 for row in payload.news if row.is_active == 1),
        news_inactivated=news_inactivated,
        question_blocks_read=len(payload.question_blocks),
        question_blocks_upserted=len(payload.question_blocks),
        question_blocks_active=sum(1 for row in payload.question_blocks if row.is_active == 1),
        question_blocks_inactivated=question_blocks_inactivated,
        questions_read=len(payload.questions),
        questions_upserted=len(payload.questions),
        questions_active=sum(1 for row in payload.questions if row.is_active == 1),
        questions_inactivated=questions_inactivated,
    )


def import_routes_from_spreadsheet(
    conn: sqlite3.Connection,
    spreadsheet: Spreadsheet,
    *,
    dry_run: bool = False,
) -> RoutesImportStats:
    """
    Run Routes import from spreadsheet with strict validation.

    Dry-run validates and builds summary without writing DB.
    """
    payload = build_routes_import_payload(spreadsheet)
    if dry_run:
        return _build_dry_run_stats(payload)
    return _apply_routes_import(conn, payload)
