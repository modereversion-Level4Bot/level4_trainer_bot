"""Handlers for Questions feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from core.guards import run_guard_chain
from core.safe_telegram import safe_answer_callback
from features.main_menu.keyboards import MENU_QUESTIONS_CALLBACK
from features.main_menu.service import (
    get_user_language_by_telegram_id,
    get_user_row_by_telegram_id,
)
from features.questions.keyboards import (
    CB_QUESTIONS_CONTINUE_PREFIX,
    CB_QUESTIONS_FINISH_PREFIX,
    CB_QUESTIONS_GO_LEVEL_PREFIX,
    CB_QUESTIONS_HOME,
    CB_QUESTIONS_LEVELS,
    CB_QUESTIONS_LEVEL_PREFIX,
    CB_QUESTIONS_NEXT_PREFIX,
    CB_QUESTIONS_PREV_PREFIX,
    CB_QUESTIONS_REPEAT_PREFIX,
    CB_QUESTIONS_START_PREFIX,
    CB_QUESTIONS_VIEW_PREFIX,
    QUESTIONS_CALLBACK_PREFIX,
    VIEW_BASE,
    VIEW_REVIEW,
)
from features.questions.service import (
    QuestionActionResult,
    continue_level,
    finish_current_question,
    go_home,
    go_to_next_question,
    go_to_previous_question,
    open_level_entry,
    show_level_completion,
    show_levels_or_empty,
    show_question_view,
    start_level_from_beginning,
)


QUESTIONS_HANDLER_GROUP = -1

def _parse_level(callback_data: str, prefix: str) -> int | None:
    if not callback_data.startswith(prefix):
        return None
    raw_level = callback_data[len(prefix) :].strip()
    if not raw_level:
        return None
    try:
        level = int(raw_level)
    except ValueError:
        return None
    if level not in {4, 5}:
        return None
    return level


def _parse_level_question(callback_data: str, prefix: str) -> tuple[int, int] | None:
    if not callback_data.startswith(prefix):
        return None
    raw_payload = callback_data[len(prefix) :].strip()
    if not raw_payload:
        return None
    parts = raw_payload.split(":")
    if len(parts) != 2:
        return None
    try:
        level = int(parts[0])
        question_number = int(parts[1])
    except ValueError:
        return None
    if level not in {4, 5} or question_number <= 0:
        return None
    return level, question_number


def _parse_view_payload(callback_data: str) -> tuple[int, int, str] | None:
    if not callback_data.startswith(CB_QUESTIONS_VIEW_PREFIX):
        return None
    raw_payload = callback_data[len(CB_QUESTIONS_VIEW_PREFIX) :].strip()
    if not raw_payload:
        return None
    parts = raw_payload.split(":")
    if len(parts) != 3:
        return None
    try:
        level = int(parts[0])
        question_number = int(parts[1])
    except ValueError:
        return None
    view_mode = parts[2].strip().lower()
    if level not in {4, 5} or question_number <= 0:
        return None
    return level, question_number, view_mode


async def _handle_action_result(
    *,
    query,
    bot,
    chat_id: int,
    user_id: int,
    language: str,
    result: QuestionActionResult,
) -> None:
    await safe_answer_callback(
        query,
        text=result.popup_text,
        show_alert=result.show_alert,
    )
    if result.status in {"level_unavailable", "question_unavailable"}:
        await show_levels_or_empty(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
        )


async def questions_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Questions callbacks and entry from main menu."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if query is None or user is None or chat is None:
        return

    callback_data = query.data or ""
    if callback_data != MENU_QUESTIONS_CALLBACK and not callback_data.startswith(
        QUESTIONS_CALLBACK_PREFIX
    ):
        return

    if not await run_guard_chain(update, context):
        await safe_answer_callback(query)
        return

    user_row = get_user_row_by_telegram_id(user.id)
    if user_row is None:
        await safe_answer_callback(query)
        return

    user_id = int(user_row["id"])
    language = get_user_language_by_telegram_id(user.id)

    if callback_data in {MENU_QUESTIONS_CALLBACK, CB_QUESTIONS_LEVELS}:
        await safe_answer_callback(query)
        await show_levels_or_empty(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
        )
        return

    if callback_data == CB_QUESTIONS_HOME:
        await safe_answer_callback(query)
        await go_home(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            telegram_id=user.id,
        )
        return

    level = _parse_level(callback_data, CB_QUESTIONS_LEVEL_PREFIX)
    if level is not None:
        result = await open_level_entry(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            level=level,
        )
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    continue_level_value = _parse_level(callback_data, CB_QUESTIONS_CONTINUE_PREFIX)
    if continue_level_value is not None:
        result = await continue_level(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            level=continue_level_value,
        )
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    start_level_value = _parse_level(callback_data, CB_QUESTIONS_START_PREFIX)
    if start_level_value is not None:
        result = await start_level_from_beginning(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            level=start_level_value,
        )
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    view_payload = _parse_view_payload(callback_data)
    if view_payload is not None:
        level_value, question_number, view_mode = view_payload
        result = await show_question_view(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            level=level_value,
            question_number=question_number,
            view_mode=view_mode,
            resend_audio=False,
        )
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    prev_payload = _parse_level_question(callback_data, CB_QUESTIONS_PREV_PREFIX)
    if prev_payload is not None:
        level_value, question_number = prev_payload
        result = await go_to_previous_question(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            level=level_value,
            question_number=question_number,
        )
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    next_payload = _parse_level_question(callback_data, CB_QUESTIONS_NEXT_PREFIX)
    if next_payload is not None:
        level_value, question_number = next_payload
        result = await go_to_next_question(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            level=level_value,
            question_number=question_number,
        )
        if result.status == "completed":
            await safe_answer_callback(
                query,
                text=result.popup_text,
                show_alert=result.show_alert,
            )
            await show_level_completion(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                level=level_value,
            )
            return
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    finish_payload = _parse_level_question(callback_data, CB_QUESTIONS_FINISH_PREFIX)
    if finish_payload is not None:
        level_value, question_number = finish_payload
        result = finish_current_question(
            user_id=user_id,
            language=language,
            level=level_value,
            question_number=question_number,
        )
        if result.status == "completed":
            await safe_answer_callback(
                query,
                text=result.popup_text,
                show_alert=result.show_alert,
            )
            await show_level_completion(
                bot=context.bot,
                chat_id=chat.id,
                user_id=user_id,
                language=language,
                level=level_value,
            )
            return
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    repeat_level_value = _parse_level(callback_data, CB_QUESTIONS_REPEAT_PREFIX)
    if repeat_level_value is not None:
        result = await start_level_from_beginning(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            level=repeat_level_value,
        )
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    go_level_value = _parse_level(callback_data, CB_QUESTIONS_GO_LEVEL_PREFIX)
    if go_level_value is not None:
        result = await open_level_entry(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            level=go_level_value,
        )
        await _handle_action_result(
            query=query,
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
            result=result,
        )
        return

    await safe_answer_callback(query)


def register_handlers(application: Application) -> None:
    """Register Questions callback router."""
    application.add_handler(
        CallbackQueryHandler(
            questions_callback_router,
            pattern=r"^(menu:questions|questions:)",
        ),
        group=QUESTIONS_HANDLER_GROUP,
    )
