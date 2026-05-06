"""Notification-related callbacks for Settings."""

from __future__ import annotations

from telegram import CallbackQuery, Chat, User
from telegram.ext import ContextTypes

from core.safe_telegram import safe_answer_callback
from features.onboarding.keyboards import PRESET_TIME_OPTIONS
from features.settings.keyboards import (
    CB_SETTINGS_DAILY,
    CB_SETTINGS_DAILY_BACK,
    CB_SETTINGS_DAILY_DISABLE,
    CB_SETTINGS_DAILY_ENABLE,
    CB_SETTINGS_DAILY_TIME,
    CB_SETTINGS_DAILY_TIME_BACK,
    CB_SETTINGS_DAILY_TIME_CUSTOM,
    CB_SETTINGS_DAILY_TIME_CUSTOM_CANCEL,
    CB_SETTINGS_DAILY_TIME_PICK_PREFIX,
    CB_SETTINGS_REMINDERS,
    CB_SETTINGS_REMINDERS_BACK,
    CB_SETTINGS_REMINDERS_DISABLE,
    CB_SETTINGS_REMINDERS_ENABLE,
    CB_SETTINGS_REMINDERS_TIME,
    CB_SETTINGS_REMINDERS_TIME_BACK,
    CB_SETTINGS_REMINDERS_TIME_CUSTOM,
    CB_SETTINGS_REMINDERS_TIME_CUSTOM_CANCEL,
    CB_SETTINGS_REMINDERS_TIME_PICK_PREFIX,
    CB_SETTINGS_SOUND,
    CB_SETTINGS_SOUND_BACK,
    CB_SETTINGS_SOUND_DISABLE,
    CB_SETTINGS_SOUND_ENABLE,
)
from features.settings.notifications_service import (
    _show_daily_custom_time_screen,
    _show_daily_screen,
    _show_daily_time_screen,
    _show_reminders_custom_time_screen,
    _show_reminders_screen,
    _show_reminders_time_screen,
    _show_sound_screen,
)
from features.settings.sections_service import (
    DEFAULT_SCHEDULE_TIME,
    SettingsState,
    _load_state_by_user_id,
    _show_settings_notifications_section,
    _update_state,
)
from features.settings.texts import (
    alert_unsupported_time_option,
    toast_daily_tips_disabled,
    toast_daily_tips_enabled,
    toast_reminders_disabled,
    toast_reminders_enabled,
    toast_sound_disabled,
    toast_sound_enabled,
)


async def handle_notifications_callbacks(
    *,
    callback_data: str,
    query: CallbackQuery,
    user: User,
    chat: Chat,
    state: SettingsState,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Handle notifications/sound/daily/reminders callback branches."""
    _ = user

    if callback_data == CB_SETTINGS_DAILY:
        await safe_answer_callback(query)
        await _show_daily_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_DAILY_BACK:
        await safe_answer_callback(query)
        await _show_settings_notifications_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_DAILY_ENABLE:
        resolved_time = state.daily_tip_time or DEFAULT_SCHEDULE_TIME
        _update_state(
            state.user_id,
            daily_tips_enabled=True,
            daily_tip_time=resolved_time,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_daily_tips_enabled(state.ui_language, resolved_time),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_daily_screen(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    if callback_data == CB_SETTINGS_DAILY_DISABLE:
        _update_state(
            state.user_id,
            daily_tips_enabled=False,
            daily_tip_time=None,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_daily_tips_disabled(state.ui_language),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_daily_screen(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    if callback_data == CB_SETTINGS_DAILY_TIME:
        await safe_answer_callback(query)
        await _show_daily_time_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_DAILY_TIME_BACK:
        await safe_answer_callback(query)
        await _show_settings_notifications_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_DAILY_TIME_CUSTOM:
        await safe_answer_callback(query)
        await _show_daily_custom_time_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_DAILY_TIME_CUSTOM_CANCEL:
        await safe_answer_callback(query)
        await _show_daily_time_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data.startswith(CB_SETTINGS_DAILY_TIME_PICK_PREFIX):
        selected_time = callback_data.removeprefix(CB_SETTINGS_DAILY_TIME_PICK_PREFIX)
        if selected_time not in PRESET_TIME_OPTIONS:
            await safe_answer_callback(
                query,
                text=alert_unsupported_time_option(state.ui_language),
                show_alert=True,
            )
            return True
        _update_state(
            state.user_id,
            daily_tips_enabled=True,
            daily_tip_time=selected_time,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_daily_tips_enabled(state.ui_language, selected_time),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_daily_screen(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    if callback_data == CB_SETTINGS_REMINDERS:
        await safe_answer_callback(query)
        await _show_reminders_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_REMINDERS_BACK:
        await safe_answer_callback(query)
        await _show_settings_notifications_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_REMINDERS_ENABLE:
        resolved_time = state.training_reminder_time or DEFAULT_SCHEDULE_TIME
        _update_state(
            state.user_id,
            training_reminders_enabled=True,
            training_reminder_time=resolved_time,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_reminders_enabled(state.ui_language, resolved_time),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_reminders_screen(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    if callback_data == CB_SETTINGS_REMINDERS_DISABLE:
        _update_state(
            state.user_id,
            training_reminders_enabled=False,
            training_reminder_time=None,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_reminders_disabled(state.ui_language),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_reminders_screen(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    if callback_data == CB_SETTINGS_REMINDERS_TIME:
        await safe_answer_callback(query)
        await _show_reminders_time_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_REMINDERS_TIME_BACK:
        await safe_answer_callback(query)
        await _show_settings_notifications_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_REMINDERS_TIME_CUSTOM:
        await safe_answer_callback(query)
        await _show_reminders_custom_time_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_REMINDERS_TIME_CUSTOM_CANCEL:
        await safe_answer_callback(query)
        await _show_reminders_time_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data.startswith(CB_SETTINGS_REMINDERS_TIME_PICK_PREFIX):
        selected_time = callback_data.removeprefix(CB_SETTINGS_REMINDERS_TIME_PICK_PREFIX)
        if selected_time not in PRESET_TIME_OPTIONS:
            await safe_answer_callback(
                query,
                text=alert_unsupported_time_option(state.ui_language),
                show_alert=True,
            )
            return True
        _update_state(
            state.user_id,
            training_reminders_enabled=True,
            training_reminder_time=selected_time,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_reminders_enabled(state.ui_language, selected_time),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_reminders_screen(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    if callback_data == CB_SETTINGS_SOUND:
        await safe_answer_callback(query)
        await _show_sound_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_SOUND_BACK:
        await safe_answer_callback(query)
        await _show_settings_notifications_section(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_SOUND_ENABLE:
        _update_state(state.user_id, sound_enabled=True, waiting_state=None)
        await safe_answer_callback(
            query,
            text=toast_sound_enabled(state.ui_language),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_sound_screen(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    if callback_data == CB_SETTINGS_SOUND_DISABLE:
        _update_state(state.user_id, sound_enabled=False, waiting_state=None)
        await safe_answer_callback(
            query,
            text=toast_sound_disabled(state.ui_language),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_sound_screen(bot=context.bot, chat_id=chat.id, state=refreshed)
        return True

    return False
