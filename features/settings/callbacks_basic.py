"""Language/timezone callbacks for Settings."""

from __future__ import annotations

from telegram import CallbackQuery, Chat, User
from telegram.ext import ContextTypes

from core.safe_telegram import safe_answer_callback
from features.settings.basic_service import (
    _show_timezone_auto_screen,
    _show_timezone_manual_screen,
    _show_timezone_screen,
)
from features.settings.keyboards import (
    CB_SETTINGS_LANGUAGE_BACK,
    CB_SETTINGS_LANGUAGE_EN,
    CB_SETTINGS_LANGUAGE_RU,
    CB_SETTINGS_TIMEZONE,
    CB_SETTINGS_TIMEZONE_AUTO,
    CB_SETTINGS_TIMEZONE_AUTO_BACK,
    CB_SETTINGS_TIMEZONE_BACK,
    CB_SETTINGS_TIMEZONE_MANUAL,
    CB_SETTINGS_TIMEZONE_MANUAL_BACK,
    CB_SETTINGS_TIMEZONE_PICK_PREFIX,
    timezone_value_by_code,
)
from features.settings.sections_service import (
    SettingsState,
    _load_state_by_user_id,
    _show_settings_main_section,
    _update_state,
)
from features.settings.texts import (
    alert_unknown_timezone_option,
    toast_language_set,
    toast_timezone_set,
)


async def handle_basic_callbacks(
    *,
    callback_data: str,
    query: CallbackQuery,
    user: User,
    chat: Chat,
    state: SettingsState,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Handle language and timezone callback branches."""
    _ = user

    if callback_data == CB_SETTINGS_LANGUAGE_BACK:
        await safe_answer_callback(query)
        await _show_settings_main_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data in {CB_SETTINGS_LANGUAGE_RU, CB_SETTINGS_LANGUAGE_EN}:
        selected_language = "ru" if callback_data == CB_SETTINGS_LANGUAGE_RU else "en"
        _update_state(state.user_id, interface_language=selected_language, waiting_state=None)
        await safe_answer_callback(
            query,
            text=toast_language_set(selected_language),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is None:
            return True
        await _show_settings_main_section(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    if callback_data == CB_SETTINGS_TIMEZONE:
        await safe_answer_callback(query)
        await _show_timezone_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_TIMEZONE_BACK:
        await safe_answer_callback(query)
        await _show_settings_main_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_TIMEZONE_AUTO:
        await safe_answer_callback(query)
        await _show_timezone_auto_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_TIMEZONE_AUTO_BACK:
        await safe_answer_callback(query)
        await _show_settings_main_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_TIMEZONE_MANUAL:
        await safe_answer_callback(query)
        await _show_timezone_manual_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_TIMEZONE_MANUAL_BACK:
        await safe_answer_callback(query)
        await _show_settings_main_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data.startswith(CB_SETTINGS_TIMEZONE_PICK_PREFIX):
        code = callback_data.removeprefix(CB_SETTINGS_TIMEZONE_PICK_PREFIX)
        timezone_value = timezone_value_by_code(code)
        if timezone_value is None:
            await safe_answer_callback(
                query,
                text=alert_unknown_timezone_option(state.ui_language),
                show_alert=True,
            )
            return True
        _update_state(state.user_id, timezone=timezone_value, waiting_state=None)
        await safe_answer_callback(
            query,
            text=toast_timezone_set(state.ui_language, timezone_value),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_settings_main_section(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    return False
