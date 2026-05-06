"""Settings section rendering and shared state helpers."""

from __future__ import annotations

from dataclasses import dataclass

from telegram import Bot, ReplyKeyboardRemove

from config import get_settings
from core.message_stack import (
    clear_service_layers,
    load_stack,
    register_service_layer,
    render_main_ui,
)
from core.safe_telegram import safe_delete_message, safe_send_message
from db.connection import get_connection
from db.repositories.settings_repo import update_settings_fields
from db.repositories.users_repo import (
    get_user_with_onboarding_by_telegram_id,
    get_user_with_onboarding_by_user_id,
)
from features.settings.keyboards import (
    build_settings_account_section_keyboard,
    build_settings_location_reply_keyboard,
    build_settings_main_keyboard,
    build_settings_main_section_keyboard,
    build_settings_notifications_section_keyboard,
)
from features.settings.texts import settings_main_screen


WAIT_SETTINGS_LOCATION = "settings_waiting_location"
WAIT_SETTINGS_DAILY_CUSTOM = "settings_waiting_daily_custom_time"
WAIT_SETTINGS_REMINDERS_CUSTOM = "settings_waiting_reminders_custom_time"

SETTINGS_WAITING_CUSTOM_STATES = {WAIT_SETTINGS_DAILY_CUSTOM, WAIT_SETTINGS_REMINDERS_CUSTOM}
DEFAULT_SCHEDULE_TIME = "21:00"


@dataclass(slots=True)
class SettingsState:
    user_id: int
    telegram_id: int
    telegram_language_code: str | None
    language: str | None
    timezone: str
    daily_tips_enabled: bool
    daily_tip_time: str | None
    training_reminders_enabled: bool
    training_reminder_time: str | None
    sound_enabled: bool
    waiting_state: str | None

    @property
    def ui_language(self) -> str:
        if self.language in {"ru", "en"}:
            return self.language
        if (self.telegram_language_code or "").lower().startswith("ru"):
            return "ru"
        return "en"


def _resolve_default_language(telegram_language_code: str | None) -> str:
    if not telegram_language_code:
        return "en"
    lowered = telegram_language_code.lower()
    if lowered.startswith("ru"):
        return "ru"
    if lowered.startswith("en"):
        return "en"
    return "en"


def _row_to_state(row) -> SettingsState:
    return SettingsState(
        user_id=row["id"],
        telegram_id=row["telegram_id"],
        telegram_language_code=row["language_code"],
        language=row["interface_language"],
        timezone=row["timezone"] or "UTC",
        daily_tips_enabled=bool(row["daily_tips_enabled"]),
        daily_tip_time=row["daily_tip_time"],
        training_reminders_enabled=bool(row["training_reminders_enabled"]),
        training_reminder_time=row["training_reminder_time"],
        sound_enabled=bool(row["sound_enabled"]),
        waiting_state=row["waiting_state"],
    )


def _ensure_language(state: SettingsState) -> SettingsState:
    if state.language in {"ru", "en"}:
        return state

    resolved = _resolve_default_language(state.telegram_language_code)
    with get_connection() as conn:
        update_settings_fields(conn, state.user_id, interface_language=resolved)
    state.language = resolved
    return state


def _load_state_by_telegram_id(telegram_id: int) -> SettingsState | None:
    with get_connection() as conn:
        row = get_user_with_onboarding_by_telegram_id(conn, telegram_id)
    if row is None:
        return None
    return _ensure_language(_row_to_state(row))


def _load_state_by_user_id(user_id: int) -> SettingsState | None:
    with get_connection() as conn:
        row = get_user_with_onboarding_by_user_id(conn, user_id)
    if row is None:
        return None
    return _ensure_language(_row_to_state(row))


def _update_state(user_id: int, **fields) -> None:
    with get_connection() as conn:
        update_settings_fields(conn, user_id, **fields)


def _waiting_state_by_telegram_id(telegram_id: int) -> str | None:
    state = _load_state_by_telegram_id(telegram_id)
    if state is None:
        return None
    return state.waiting_state


def is_settings_waiting_for_location(telegram_id: int) -> bool:
    return _waiting_state_by_telegram_id(telegram_id) == WAIT_SETTINGS_LOCATION


def is_settings_waiting_for_custom_time(telegram_id: int) -> bool:
    return _waiting_state_by_telegram_id(telegram_id) in SETTINGS_WAITING_CUSTOM_STATES


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_ids


async def _remove_location_reply_keyboard(bot: Bot, chat_id: int, user_id: int) -> None:
    stack = load_stack(user_id)
    if not stack.service_layer_message_ids:
        return

    await clear_service_layers(bot=bot, chat_id=chat_id, user_id=user_id)
    removed_message = await safe_send_message(
        bot=bot,
        chat_id=chat_id,
        text=".",
        reply_markup=ReplyKeyboardRemove(),
        disable_notification=True,
    )
    if removed_message is not None:
        await safe_delete_message(
            bot=bot,
            chat_id=chat_id,
            message_id=removed_message.message_id,
        )


async def _show_location_reply_keyboard(bot: Bot, chat_id: int, user_id: int, language: str) -> None:
    await clear_service_layers(bot=bot, chat_id=chat_id, user_id=user_id)
    prompt = await safe_send_message(
        bot=bot,
        chat_id=chat_id,
        text="📍 Отправьте геолокацию" if language == "ru" else "📍 Send location",
        reply_markup=build_settings_location_reply_keyboard(language),
    )
    if prompt is not None:
        register_service_layer(user_id=user_id, message_id=prompt.message_id)


async def _render_settings_screen(
    bot: Bot,
    chat_id: int,
    state: SettingsState,
    text: str,
    reply_markup,
    *,
    waiting_state: str | None = None,
    needs_location_keyboard: bool = False,
) -> None:
    if not needs_location_keyboard:
        await _remove_location_reply_keyboard(bot=bot, chat_id=chat_id, user_id=state.user_id)

    _update_state(state.user_id, waiting_state=waiting_state)
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=state.user_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    if needs_location_keyboard:
        await _show_location_reply_keyboard(
            bot=bot,
            chat_id=chat_id,
            user_id=state.user_id,
            language=state.ui_language,
        )


def _settings_summary_text(state: SettingsState) -> str:
    return settings_main_screen(
        state.ui_language,
        timezone_value=state.timezone,
        daily_tips_enabled=state.daily_tips_enabled,
        daily_tip_time=state.daily_tip_time,
        training_reminders_enabled=state.training_reminders_enabled,
        training_reminder_time=state.training_reminder_time,
        sound_enabled=state.sound_enabled,
    )


async def show_settings_main(
    bot: Bot,
    chat_id: int,
    user_id: int,
    telegram_id: int,
) -> None:
    state = _load_state_by_user_id(user_id)
    if state is None:
        return
    await _show_settings_main(bot=bot, chat_id=chat_id, state=state, telegram_id=telegram_id)


async def _show_settings_main(bot: Bot, chat_id: int, state: SettingsState, telegram_id: int) -> None:
    is_admin = _is_admin(telegram_id)
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=_settings_summary_text(state),
        reply_markup=build_settings_main_keyboard(state.ui_language, is_admin=is_admin),
    )


async def _show_settings_main_section(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=_settings_summary_text(state),
        reply_markup=build_settings_main_section_keyboard(state.ui_language),
    )


async def _show_settings_notifications_section(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=_settings_summary_text(state),
        reply_markup=build_settings_notifications_section_keyboard(state.ui_language),
    )


async def _show_settings_account_section(
    bot: Bot,
    chat_id: int,
    state: SettingsState,
    *,
    telegram_id: int,
) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=_settings_summary_text(state),
        reply_markup=build_settings_account_section_keyboard(
            state.ui_language,
            is_admin=_is_admin(telegram_id),
        ),
    )
