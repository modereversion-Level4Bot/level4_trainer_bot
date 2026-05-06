"""Handlers for clean chat guard."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from core.safe_telegram import safe_delete_message
from features.clean_chat.service import should_cleanup_private_user_message


# This group runs after feature handlers and cleans user input messages.
CLEAN_CHAT_HANDLER_GROUP = 100


async def cleanup_incoming_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Delete incoming private user messages after feature processing."""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not should_cleanup_private_user_message(message=message, chat=chat, user=user):
        return

    await safe_delete_message(
        bot=context.bot,
        chat_id=chat.id,
        message_id=message.message_id,
    )


def register_handlers(application: Application) -> None:
    """Register clean chat guard for all incoming private messages."""
    application.add_handler(
        MessageHandler(filters.ChatType.PRIVATE & ~filters.StatusUpdate.ALL, cleanup_incoming_message),
        group=CLEAN_CHAT_HANDLER_GROUP,
    )

