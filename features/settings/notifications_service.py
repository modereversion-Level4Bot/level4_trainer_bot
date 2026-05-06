"""Notifications-related Settings flows."""

from __future__ import annotations

import re

from telegram import Bot

from features.settings.keyboards import (
    build_settings_daily_custom_keyboard,
    build_settings_daily_keyboard,
    build_settings_daily_time_keyboard,
    build_settings_reminders_custom_keyboard,
    build_settings_reminders_keyboard,
    build_settings_reminders_time_keyboard,
    build_settings_sound_keyboard,
)
from features.settings.sections_service import (
    WAIT_SETTINGS_DAILY_CUSTOM,
    WAIT_SETTINGS_REMINDERS_CUSTOM,
    SettingsState,
    _render_settings_screen,
)
from features.settings.texts import (
    settings_daily_tip_custom_time_screen,
    settings_daily_tip_screen,
    settings_daily_tip_time_screen,
    settings_reminders_custom_time_screen,
    settings_reminders_screen,
    settings_reminders_time_screen,
    settings_sound_screen,
)


TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _is_valid_time(value: str) -> bool:
    return bool(TIME_PATTERN.match(value.strip()))


async def _show_daily_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_daily_tip_screen(
            state.ui_language,
            enabled=state.daily_tips_enabled,
            time_value=state.daily_tip_time,
        ),
        reply_markup=build_settings_daily_keyboard(state.ui_language, enabled=state.daily_tips_enabled),
    )


async def _show_daily_time_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_daily_tip_time_screen(state.ui_language),
        reply_markup=build_settings_daily_time_keyboard(state.ui_language),
    )


async def _show_daily_custom_time_screen(
    bot: Bot,
    chat_id: int,
    state: SettingsState,
    *,
    warning_text: str | None = None,
) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_daily_tip_custom_time_screen(state.ui_language, warning_text),
        reply_markup=build_settings_daily_custom_keyboard(state.ui_language),
        waiting_state=WAIT_SETTINGS_DAILY_CUSTOM,
    )


async def _show_reminders_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_reminders_screen(
            state.ui_language,
            enabled=state.training_reminders_enabled,
            time_value=state.training_reminder_time,
        ),
        reply_markup=build_settings_reminders_keyboard(
            state.ui_language,
            enabled=state.training_reminders_enabled,
        ),
    )


async def _show_reminders_time_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_reminders_time_screen(state.ui_language),
        reply_markup=build_settings_reminders_time_keyboard(state.ui_language),
    )


async def _show_reminders_custom_time_screen(
    bot: Bot,
    chat_id: int,
    state: SettingsState,
    *,
    warning_text: str | None = None,
) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_reminders_custom_time_screen(state.ui_language, warning_text),
        reply_markup=build_settings_reminders_custom_keyboard(state.ui_language),
        waiting_state=WAIT_SETTINGS_REMINDERS_CUSTOM,
    )


async def _show_sound_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_sound_screen(state.ui_language, state.sound_enabled),
        reply_markup=build_settings_sound_keyboard(state.ui_language, enabled=state.sound_enabled),
    )
