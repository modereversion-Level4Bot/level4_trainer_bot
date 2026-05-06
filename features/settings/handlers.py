"""Handlers for settings feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters

from core.guards import run_guard_chain
from core.safe_telegram import safe_answer_callback
from features.main_menu.keyboards import MENU_SETTINGS_CALLBACK
from features.main_menu.service import get_user_row_by_telegram_id
from features.settings.service import (
    is_settings_waiting_for_custom_time,
    is_settings_waiting_for_location,
    process_settings_callback,
    process_settings_location,
    process_settings_text,
    show_settings_main,
)


SETTINGS_HANDLER_GROUP = -1


async def settings_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route settings callback actions."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if query is None or user is None or chat is None:
        return

    if not await run_guard_chain(update, context):
        await safe_answer_callback(query)
        return

    if query.data == MENU_SETTINGS_CALLBACK:
        user_row = get_user_row_by_telegram_id(user.id)
        if user_row is None:
            await safe_answer_callback(query)
            return
        await safe_answer_callback(query)
        await show_settings_main(
            bot=context.bot,
            chat_id=chat.id,
            user_id=int(user_row["id"]),
            telegram_id=user.id,
        )
        return

    _ = await process_settings_callback(update, context)


async def settings_location_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process settings location input in waiting state."""
    user = update.effective_user
    if user is None:
        return
    if not is_settings_waiting_for_location(user.id):
        return
    if not await run_guard_chain(update, context):
        return
    _ = await process_settings_location(update, context)


async def settings_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process settings custom-time text input in waiting state."""
    user = update.effective_user
    if user is None:
        return
    if not is_settings_waiting_for_custom_time(user.id):
        return
    if not await run_guard_chain(update, context):
        return
    _ = await process_settings_text(update, context)


def register_handlers(application: Application) -> None:
    """Register settings handlers."""
    application.add_handler(
        CallbackQueryHandler(
            settings_callback_router,
            pattern=r"^(menu:settings|settings:)",
        ),
        group=SETTINGS_HANDLER_GROUP,
    )
    application.add_handler(
        MessageHandler(filters.LOCATION, settings_location_router),
        group=SETTINGS_HANDLER_GROUP,
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, settings_text_router),
        group=SETTINGS_HANDLER_GROUP,
    )
