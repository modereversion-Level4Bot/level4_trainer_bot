"""Service layer for main menu feature."""

from __future__ import annotations

import sqlite3

from telegram import Bot

from config import get_settings
from core.message_stack import render_main_ui
from db.connection import get_connection
from db.repositories.grammar_repo import (
    count_active_main_topics,
    count_studied_main_topics,
)
from db.repositories.questions_repo import (
    count_active_exam_questions,
    count_completed_exam_questions,
)
from db.repositories.routes_repo import count_active_routes, count_completed_routes
from db.repositories.users_repo import (
    get_user_with_onboarding_by_user_id,
    update_onboarding_settings,
)
from features.main_menu.context import MainMenuContext
from features.main_menu.keyboards import build_main_menu_keyboard
from features.main_menu.texts import main_menu_text


def _default_language_by_telegram_code(telegram_language_code: str | None) -> str:
    if not telegram_language_code:
        return "en"
    lowered = telegram_language_code.lower()
    if lowered.startswith("ru"):
        return "ru"
    if lowered.startswith("en"):
        return "en"
    return "en"


def _ensure_initial_language(
    user_id: int,
    telegram_language_code: str | None,
    current_language: str | None,
) -> str:
    if current_language in {"ru", "en"}:
        return current_language
    resolved = _default_language_by_telegram_code(telegram_language_code)
    with get_connection() as conn:
        update_onboarding_settings(conn, user_id=user_id, language=resolved)
    return resolved


def _resolve_language(row) -> str:
    if row is None:
        return "en"
    return _ensure_initial_language(
        user_id=row["id"],
        telegram_language_code=row["language_code"],
        current_language=row["interface_language"],
    )


def _is_admin(telegram_id: int) -> bool:
    settings = get_settings()
    return telegram_id in settings.admin_ids


def get_user_row_by_telegram_id(telegram_id: int) -> sqlite3.Row | None:
    """Load user row joined with onboarding state by Telegram ID."""
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT
                u.id,
                u.telegram_id,
                u.language_code,
                o.interface_language
            FROM users AS u
            LEFT JOIN user_onboarding_state AS o ON o.user_id = u.id
            WHERE u.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchone()


def _bounded_progress(completed: int, total: int) -> int:
    if completed < 0:
        return 0
    if completed > total:
        return total
    return completed


def build_main_menu_context(user_id: int, telegram_id: int) -> MainMenuContext:
    """Build progress and visibility context for main menu rendering."""
    with get_connection() as conn:
        grammar_total = count_active_main_topics(conn)
        grammar_completed = count_studied_main_topics(conn, user_id=user_id)
        questions_total = count_active_exam_questions(conn)
        questions_completed = count_completed_exam_questions(conn, user_id=user_id)
        routes_total = count_active_routes(conn)
        routes_completed = count_completed_routes(conn, user_id=user_id)

    grammar_completed = _bounded_progress(grammar_completed, grammar_total)
    questions_completed = _bounded_progress(questions_completed, questions_total)
    routes_completed = _bounded_progress(routes_completed, routes_total)

    return MainMenuContext(
        grammar_total=grammar_total,
        grammar_completed=grammar_completed,
        questions_total=questions_total,
        questions_completed=questions_completed,
        routes_total=routes_total,
        routes_completed=routes_completed,
        has_grammar_content=grammar_total > 0,
        has_questions_content=questions_total > 0,
        is_admin=_is_admin(telegram_id),
        bot_version=get_settings().bot_version,
    )


def get_user_language_by_telegram_id(telegram_id: int) -> str:
    """Return interface language for current user."""
    row = get_user_row_by_telegram_id(telegram_id)
    if row is None:
        return "en"
    return _ensure_initial_language(
        user_id=row["id"],
        telegram_language_code=row["language_code"],
        current_language=row["interface_language"],
    )


async def render_main_menu(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    context: MainMenuContext,
) -> None:
    """Render main menu using one-main-message strategy."""
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=main_menu_text(language, context=context),
        reply_markup=build_main_menu_keyboard(language, context=context),
    )


async def show_main_menu(
    bot: Bot,
    chat_id: int,
    user_id: int,
    telegram_id: int,
) -> None:
    """Render main menu in the current main UI message."""
    with get_connection() as conn:
        row = get_user_with_onboarding_by_user_id(conn, user_id)

    language = _resolve_language(row)
    context = build_main_menu_context(user_id=user_id, telegram_id=telegram_id)
    await render_main_menu(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        context=context,
    )
