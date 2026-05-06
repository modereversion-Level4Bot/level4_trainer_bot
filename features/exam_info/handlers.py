"""Handlers for exam info feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from core.guards import run_guard_chain
from core.safe_telegram import safe_answer_callback
from features.exam_info.keyboards import (
    CB_EXAM_INFO_INTERVIEW,
    CB_EXAM_INFO_MAIN_MENU,
    CB_EXAM_INFO_OVERVIEW,
    CB_EXAM_INFO_POST_FLIGHT,
    CB_EXAM_INFO_ROLE_PLAY,
    EXAM_INFO_CALLBACK_PREFIX,
)
from features.exam_info.service import (
    show_exam_info_interview,
    show_exam_info_overview,
    show_exam_info_post_flight,
    show_exam_info_role_play,
)
from features.main_menu.service import (
    get_user_language_by_telegram_id,
    get_user_row_by_telegram_id,
    show_main_menu,
)


async def handle_exam_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback navigation inside exam info reference screens."""
    query = update.callback_query
    if query is None:
        return

    if not await run_guard_chain(update, context):
        await safe_answer_callback(query)
        return

    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None:
        await safe_answer_callback(query)
        return

    callback_data = query.data or ""
    if not callback_data.startswith(EXAM_INFO_CALLBACK_PREFIX):
        return

    await safe_answer_callback(query)
    language = get_user_language_by_telegram_id(user.id)
    user_row = get_user_row_by_telegram_id(user.id)
    if user_row is None:
        return
    user_id = int(user_row["id"])

    if callback_data == CB_EXAM_INFO_OVERVIEW:
        await show_exam_info_overview(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
        )
        return

    if callback_data == CB_EXAM_INFO_INTERVIEW:
        await show_exam_info_interview(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
        )
        return

    if callback_data == CB_EXAM_INFO_ROLE_PLAY:
        await show_exam_info_role_play(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
        )
        return

    if callback_data == CB_EXAM_INFO_POST_FLIGHT:
        await show_exam_info_post_flight(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            language=language,
        )
        return

    if callback_data == CB_EXAM_INFO_MAIN_MENU:
        await show_main_menu(
            bot=context.bot,
            chat_id=chat.id,
            user_id=user_id,
            telegram_id=user.id,
        )


def register_handlers(application: Application) -> None:
    """Register handlers for exam info feature."""
    application.add_handler(
        CallbackQueryHandler(handle_exam_info_callback, pattern=rf"^{EXAM_INFO_CALLBACK_PREFIX}")
    )
