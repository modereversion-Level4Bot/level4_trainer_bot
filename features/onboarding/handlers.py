"""Handlers for onboarding feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from core.guards import run_guard_chain
from core.safe_telegram import safe_answer_callback
from features.onboarding.keyboards import ONBOARDING_CALLBACK_PREFIX
from features.onboarding.service import (
    process_onboarding_callback,
    process_onboarding_location,
    process_onboarding_text,
)


async def onboarding_callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await run_guard_chain(update, context):
        query = update.callback_query
        if query is not None:
            await safe_answer_callback(query)
        return
    _ = await process_onboarding_callback(update, context)


async def onboarding_location_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await run_guard_chain(update, context):
        return
    _ = await process_onboarding_location(update, context)


async def onboarding_text_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if not await run_guard_chain(update, context):
        return
    _ = await process_onboarding_text(update, context)


def register_handlers(application: Application) -> None:
    """Register onboarding handlers."""
    application.add_handler(
        CallbackQueryHandler(
            onboarding_callback_router,
            pattern=rf"^{ONBOARDING_CALLBACK_PREFIX}",
        )
    )
    application.add_handler(MessageHandler(filters.LOCATION, onboarding_location_router))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_text_router)
    )
