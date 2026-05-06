"""Handlers for /start command."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from core.guards import run_guard_chain
from db.connection import get_connection
from db.repositories.users_repo import get_user_by_telegram_id
from features.start.service import handle_start_flow


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Initialize user and route to onboarding/menu."""
    if not await run_guard_chain(update, context):
        return

    telegram_user = update.effective_user
    chat = update.effective_chat
    if telegram_user is None or chat is None:
        return

    with get_connection() as conn:
        user_row = get_user_by_telegram_id(conn, telegram_user.id)

    if user_row is None:
        return

    await handle_start_flow(
        bot=context.bot,
        chat_id=chat.id,
        user_id=user_row["id"],
        telegram_id=telegram_user.id,
        telegram_language_code=telegram_user.language_code,
    )


def register_handlers(application: Application) -> None:
    """Register handlers for start feature."""
    application.add_handler(CommandHandler("start", start_command))
