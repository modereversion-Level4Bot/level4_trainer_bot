"""Callback routing for Settings feature."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from core.safe_telegram import safe_answer_callback
from features.settings.callbacks_account import handle_account_callbacks
from features.settings.callbacks_basic import handle_basic_callbacks
from features.settings.callbacks_main import handle_main_callbacks
from features.settings.callbacks_notifications import handle_notifications_callbacks
from features.settings.keyboards import SETTINGS_CALLBACK_PREFIX
from features.settings.sections_service import _load_state_by_telegram_id, _resolve_default_language
from features.settings.texts import settings_state_not_found_alert


async def process_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Process settings callbacks. Returns True when callback belongs to settings flow."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if query is None or user is None or chat is None:
        return False

    callback_data = query.data or ""
    if not callback_data.startswith(SETTINGS_CALLBACK_PREFIX):
        return False

    state = _load_state_by_telegram_id(user.id)
    if state is None:
        fallback_lang = _resolve_default_language(user.language_code)
        await safe_answer_callback(
            query,
            text=settings_state_not_found_alert(fallback_lang),
            show_alert=True,
        )
        return True

    handlers = (
        handle_main_callbacks,
        handle_basic_callbacks,
        handle_notifications_callbacks,
        handle_account_callbacks,
    )
    for handler in handlers:
        handled = await handler(
            callback_data=callback_data,
            query=query,
            user=user,
            chat=chat,
            state=state,
            context=context,
        )
        if handled:
            return True

    await safe_answer_callback(query)
    return True
