"""Message input handlers for Settings flows."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from core.timezones import detect_timezone_name
from features.settings.basic_service import (
    _show_timezone_manual_screen,
    normalize_timezone_value,
)
from features.settings.notifications_service import (
    _is_valid_time,
    _show_daily_custom_time_screen,
    _show_reminders_custom_time_screen,
)
from features.settings.sections_service import (
    SettingsState,
    WAIT_SETTINGS_DAILY_CUSTOM,
    WAIT_SETTINGS_LOCATION,
    WAIT_SETTINGS_REMINDERS_CUSTOM,
    _load_state_by_telegram_id,
    _load_state_by_user_id,
    _remove_location_reply_keyboard,
    _show_settings_main,
    _show_settings_main_section,
    _update_state,
)
from features.settings.texts import warning_invalid_time, warning_timezone_detection_failed


async def process_settings_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Process location message for timezone auto-detection in settings."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if user is None or chat is None or message is None or message.location is None:
        return False

    state = _load_state_by_telegram_id(user.id)
    if state is None:
        return False
    if state.waiting_state != WAIT_SETTINGS_LOCATION:
        return False

    detected = detect_timezone_name(
        latitude=message.location.latitude,
        longitude=message.location.longitude,
    )
    await _remove_location_reply_keyboard(bot=context.bot, chat_id=chat.id, user_id=state.user_id)

    if not detected:
        await _show_timezone_manual_screen(
            bot=context.bot,
            chat_id=chat.id,
            state=state,
            warning_text=warning_timezone_detection_failed(state.ui_language),
        )
        return True

    timezone_value = normalize_timezone_value(detected)
    _update_state(
        state.user_id,
        timezone=timezone_value,
        waiting_state=None,
    )
    refreshed = _load_state_by_user_id(state.user_id)
    if refreshed is not None:
        await _show_settings_main_section(bot=context.bot, chat_id=chat.id, state=refreshed)
    return True


async def process_settings_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Process custom HH:MM input for settings schedules."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if user is None or chat is None or message is None:
        return False

    text_value = (message.text or "").strip()
    if not text_value:
        return False

    state = _load_state_by_telegram_id(user.id)
    if state is None:
        return False
    if state.waiting_state not in {WAIT_SETTINGS_DAILY_CUSTOM, WAIT_SETTINGS_REMINDERS_CUSTOM}:
        return False

    if not _is_valid_time(text_value):
        warning_text = warning_invalid_time(state.ui_language)
        if state.waiting_state == WAIT_SETTINGS_DAILY_CUSTOM:
            await _show_daily_custom_time_screen(
                bot=context.bot,
                chat_id=chat.id,
                state=state,
                warning_text=warning_text,
            )
        else:
            await _show_reminders_custom_time_screen(
                bot=context.bot,
                chat_id=chat.id,
                state=state,
                warning_text=warning_text,
            )
        return True

    if state.waiting_state == WAIT_SETTINGS_DAILY_CUSTOM:
        _update_state(
            state.user_id,
            daily_tips_enabled=True,
            daily_tip_time=text_value,
            waiting_state=None,
        )
    else:
        _update_state(
            state.user_id,
            training_reminders_enabled=True,
            training_reminder_time=text_value,
            waiting_state=None,
        )
    refreshed = _load_state_by_user_id(state.user_id)
    if refreshed is not None:
        await _show_settings_main(
            bot=context.bot,
            chat_id=chat.id,
            state=refreshed,
            telegram_id=user.id,
        )
    return True
