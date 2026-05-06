"""Main/section-level callbacks for Settings."""

from __future__ import annotations

from telegram import CallbackQuery, Chat, User
from telegram.ext import ContextTypes

from core.safe_telegram import safe_answer_callback
from features.main_menu.service import show_main_menu
from features.settings.basic_service import _show_language_screen
from features.settings.keyboards import (
    CB_SETTINGS_HOME,
    CB_SETTINGS_LANGUAGE,
    CB_SETTINGS_MAIN,
    CB_SETTINGS_MANAGEMENT,
    CB_SETTINGS_SECTION_ACCOUNT,
    CB_SETTINGS_SECTION_MAIN,
    CB_SETTINGS_SECTION_NOTIFICATIONS,
)
from features.settings.sections_service import (
    SettingsState,
    _is_admin,
    _show_settings_account_section,
    _show_settings_main,
    _show_settings_main_section,
    _show_settings_notifications_section,
)
from features.settings.texts import management_todo_alert


async def handle_main_callbacks(
    *,
    callback_data: str,
    query: CallbackQuery,
    user: User,
    chat: Chat,
    state: SettingsState,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Handle top-level Settings callbacks and section navigation."""
    if callback_data == CB_SETTINGS_MAIN:
        await safe_answer_callback(query)
        await _show_settings_main(bot=context.bot, chat_id=chat.id, state=state, telegram_id=user.id)
        return True

    if callback_data == CB_SETTINGS_SECTION_MAIN:
        await safe_answer_callback(query)
        await _show_settings_main_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_SECTION_NOTIFICATIONS:
        await safe_answer_callback(query)
        await _show_settings_notifications_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_SECTION_ACCOUNT:
        await safe_answer_callback(query)
        await _show_settings_account_section(
            bot=context.bot,
            chat_id=chat.id,
            state=state,
            telegram_id=user.id,
        )
        return True

    if callback_data == CB_SETTINGS_HOME:
        await safe_answer_callback(query)
        await show_main_menu(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            telegram_id=user.id,
        )
        return True

    if callback_data == CB_SETTINGS_LANGUAGE:
        await safe_answer_callback(query)
        await _show_language_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_MANAGEMENT:
        if not _is_admin(state.telegram_id):
            await safe_answer_callback(query)
            return True
        await safe_answer_callback(
            query,
            text=management_todo_alert(state.ui_language),
            show_alert=True,
        )
        return True

    return False
