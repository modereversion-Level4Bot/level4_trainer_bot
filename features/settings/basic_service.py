"""Basic Settings flows: language and timezone."""

from __future__ import annotations

from datetime import datetime, timezone

import pytz
from telegram import Bot

from features.onboarding.keyboards import TIMEZONE_OPTIONS
from features.settings.keyboards import (
    build_settings_language_keyboard,
    build_settings_timezone_auto_keyboard,
    build_settings_timezone_keyboard,
    build_settings_timezone_manual_keyboard,
)
from features.settings.sections_service import (
    WAIT_SETTINGS_LOCATION,
    SettingsState,
    _render_settings_screen,
)
from features.settings.texts import (
    settings_language_screen,
    settings_timezone_auto_screen,
    settings_timezone_manual_screen,
    settings_timezone_screen,
)


def _normalized_timezone_lookup() -> dict[str, str]:
    lookup = {"UTC": "UTC"}
    for option in TIMEZONE_OPTIONS:
        timezone_name = option.normalized_value.split(" UTC")[0]
        lookup[timezone_name] = option.normalized_value
    return lookup


NORMALIZED_TIMEZONE_BY_NAME = _normalized_timezone_lookup()


def _format_offset(offset_seconds: int) -> str:
    sign = "+" if offset_seconds >= 0 else "-"
    total_minutes = abs(offset_seconds) // 60
    hours, minutes = divmod(total_minutes, 60)
    if minutes == 0:
        return f"{sign}{hours}"
    return f"{sign}{hours}:{minutes:02d}"


def normalize_timezone_value(timezone_name: str) -> str:
    if timezone_name in NORMALIZED_TIMEZONE_BY_NAME:
        return NORMALIZED_TIMEZONE_BY_NAME[timezone_name]
    try:
        tz = pytz.timezone(timezone_name)
    except Exception:
        return timezone_name
    now = datetime.now(timezone.utc).astimezone(tz)
    offset = now.utcoffset()
    if offset is None:
        return timezone_name
    return f"{timezone_name} UTC{_format_offset(int(offset.total_seconds()))}"


async def _show_language_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_language_screen(state.ui_language),
        reply_markup=build_settings_language_keyboard(state.ui_language),
    )


async def _show_timezone_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_timezone_screen(state.ui_language, state.timezone),
        reply_markup=build_settings_timezone_keyboard(state.ui_language),
    )


async def _show_timezone_auto_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_timezone_auto_screen(state.ui_language),
        reply_markup=build_settings_timezone_auto_keyboard(state.ui_language),
        waiting_state=WAIT_SETTINGS_LOCATION,
        needs_location_keyboard=True,
    )


async def _show_timezone_manual_screen(
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
        text=settings_timezone_manual_screen(state.ui_language, warning_text),
        reply_markup=build_settings_timezone_manual_keyboard(state.ui_language),
    )
