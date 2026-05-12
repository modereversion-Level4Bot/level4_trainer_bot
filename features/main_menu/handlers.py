"""Handlers for main menu feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from core.guards import run_guard_chain
from core.safe_telegram import safe_answer_callback
from features.main_menu.keyboards import MENU_ROUTES_CALLBACK
from features.main_menu.service import (
    get_user_language_by_telegram_id,
    get_user_row_by_telegram_id,
)
from features.main_menu.texts import todo_section_alert
from features.routes.service import is_routes_ui_enabled, show_routes_list


async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle main menu temporary TODO actions (except Settings)."""
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

    if query.data != MENU_ROUTES_CALLBACK:
        return

    language = get_user_language_by_telegram_id(user.id)
    if not is_routes_ui_enabled():
        await safe_answer_callback(
            query,
            text=todo_section_alert(language),
            show_alert=True,
        )
        return

    user_row = get_user_row_by_telegram_id(user.id)
    if user_row is None:
        await safe_answer_callback(query)
        return

    await safe_answer_callback(query)
    await show_routes_list(
        bot=context.bot,
        chat_id=chat.id,
        user_id=int(user_row["id"]),
        language=language,
        page=1,
    )


def register_handlers(application: Application) -> None:
    """Register main menu handlers."""
    application.add_handler(
        CallbackQueryHandler(handle_main_menu_callback, pattern=r"^menu:routes$")
    )