"""Level selection and completion flows for Questions feature."""

from __future__ import annotations

from telegram import Bot

from core.message_stack import render_main_ui
from db.connection import get_connection
from db.repositories.questions_repo import (
    count_active_questions_by_level,
    list_available_active_levels,
)
from features.main_menu.service import show_main_menu
from features.questions.audio_service import delete_user_audio
from features.questions.keyboards import (
    VIEW_BASE,
    build_completed_reentry_keyboard,
    build_continue_start_over_keyboard,
    build_empty_keyboard,
    build_level4_completion_keyboard,
    build_level5_completion_keyboard,
    build_levels_keyboard,
)
from features.questions.progress_service import (
    first_question_number,
    has_started_level,
    is_level_completed,
    load_level_questions_context,
    resolve_continue_question_number,
)
from features.questions.question_service import QuestionActionResult, show_question_view
from features.questions.texts import (
    continue_start_over_completed_text,
    continue_start_over_started_text,
    level4_completion_text,
    level5_completion_text,
    level_unavailable_alert,
    questions_empty_text,
    questions_levels_text,
)


async def show_levels_or_empty(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    clear_audio: bool = True,
) -> None:
    """Show level selection screen, or empty screen if no active content."""
    if clear_audio:
        await delete_user_audio(bot, chat_id, user_id=user_id)

    with get_connection() as conn:
        has_level4 = count_active_questions_by_level(conn, 4) > 0
        has_level5 = count_active_questions_by_level(conn, 5) > 0

    if not has_level4 and not has_level5:
        await render_main_ui(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            text=questions_empty_text(language),
            reply_markup=build_empty_keyboard(language),
            parse_mode="HTML",
        )
        return

    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=questions_levels_text(language),
        reply_markup=build_levels_keyboard(
            language,
            has_level4=has_level4,
            has_level5=has_level5,
        ),
        parse_mode="HTML",
    )


def _level_exists(level: int) -> bool:
    return int(level) in {4, 5}


async def open_level_entry(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    level: int,
) -> QuestionActionResult:
    """Open level entry point: continue/start-over prompt or first question."""
    if not _level_exists(level):
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )

    level_number = int(level)
    with get_connection() as conn:
        context = load_level_questions_context(conn, level_number)
        if context is None:
            return QuestionActionResult(
                status="level_unavailable",
                popup_text=level_unavailable_alert(language),
                show_alert=True,
            )
        started = has_started_level(conn, user_id, level_number)
        completed = is_level_completed(conn, user_id, context)
        first_number = first_question_number(context)

    await delete_user_audio(bot, chat_id, user_id=user_id)

    if started:
        if completed:
            entry_text = continue_start_over_completed_text(language, level_number)
            entry_keyboard = build_completed_reentry_keyboard(
                language,
                level=level_number,
            )
        else:
            entry_text = continue_start_over_started_text(language, level_number)
            entry_keyboard = build_continue_start_over_keyboard(
                language,
                level=level_number,
            )
        await render_main_ui(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            text=entry_text,
            reply_markup=entry_keyboard,
            parse_mode="HTML",
        )
        return QuestionActionResult(status="rendered")

    if first_number is None:
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )

    return await show_question_view(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        level=level_number,
        question_number=first_number,
        view_mode=VIEW_BASE,
        resend_audio=True,
    )


async def continue_level(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    level: int,
) -> QuestionActionResult:
    """Continue from current question, or first unresolved fallback."""
    if not _level_exists(level):
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )

    level_number = int(level)
    with get_connection() as conn:
        context = load_level_questions_context(conn, level_number)
        if context is None:
            return QuestionActionResult(
                status="level_unavailable",
                popup_text=level_unavailable_alert(language),
                show_alert=True,
            )
        target_question_number = resolve_continue_question_number(conn, user_id, context)

    if target_question_number is None:
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )

    await delete_user_audio(bot, chat_id, user_id=user_id)
    return await show_question_view(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        level=level_number,
        question_number=target_question_number,
        view_mode=VIEW_BASE,
        resend_audio=True,
    )


async def start_level_from_beginning(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    level: int,
) -> QuestionActionResult:
    """Open first question in level without clearing completed progress."""
    if not _level_exists(level):
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )

    level_number = int(level)
    with get_connection() as conn:
        context = load_level_questions_context(conn, level_number)
        if context is None:
            return QuestionActionResult(
                status="level_unavailable",
                popup_text=level_unavailable_alert(language),
                show_alert=True,
            )
        target_question_number = first_question_number(context)

    if target_question_number is None:
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )

    await delete_user_audio(bot, chat_id, user_id=user_id)
    return await show_question_view(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        level=level_number,
        question_number=target_question_number,
        view_mode=VIEW_BASE,
        resend_audio=True,
    )


async def show_level_completion(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    level: int,
) -> None:
    """Render completion screen for one level."""
    await delete_user_audio(bot, chat_id, user_id=user_id)

    with get_connection() as conn:
        available_levels = list_available_active_levels(conn)
    has_level5 = 5 in available_levels

    if int(level) == 4:
        await render_main_ui(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            text=level4_completion_text(language, has_level5=has_level5),
            reply_markup=build_level4_completion_keyboard(language, has_level5=has_level5),
            parse_mode="HTML",
        )
        return

    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=level5_completion_text(language),
        reply_markup=build_level5_completion_keyboard(language),
        parse_mode="HTML",
    )


async def go_home(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    telegram_id: int,
) -> None:
    """Leave Questions and return to main menu."""
    await delete_user_audio(bot, chat_id, user_id=user_id)
    await show_main_menu(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        telegram_id=telegram_id,
    )
