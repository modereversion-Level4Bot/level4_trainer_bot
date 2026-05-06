"""Service layer for onboarding feature."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

import pytz
from telegram import Bot, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from core.message_stack import (
    clear_service_layers,
    load_stack,
    register_service_layer,
    render_main_ui,
)
from core.safe_telegram import safe_answer_callback, safe_delete_message, safe_send_message
from core.timezones import detect_timezone_name
from db.connection import get_connection
from db.repositories.users_repo import (
    apply_default_onboarding_settings,
    get_user_with_onboarding_by_telegram_id,
    get_user_with_onboarding_by_user_id,
    update_onboarding_settings,
)
from features.main_menu.service import show_main_menu
from features.onboarding.keyboards import (
    CB_BACK_TO_DAILY,
    CB_BACK_TO_DAILY_TIME,
    CB_BACK_TO_LANGUAGE,
    CB_BACK_TO_REMINDERS,
    CB_BACK_TO_REMINDERS_TIME,
    CB_BACK_TO_TIMEZONE,
    CB_BACK_TO_TIMEZONE_MENU,
    CB_DAILY_CUSTOM_CANCEL,
    CB_DAILY_DISABLE,
    CB_DAILY_ENABLE,
    CB_DAILY_TIME_CUSTOM,
    CB_DAILY_TIME_PREFIX,
    CB_FINAL_TO_MENU,
    CB_LANGUAGE_PREFIX,
    CB_REMINDERS_CUSTOM_CANCEL,
    CB_REMINDERS_DISABLE,
    CB_REMINDERS_ENABLE,
    CB_REMINDERS_TIME_CUSTOM,
    CB_REMINDERS_TIME_PREFIX,
    CB_TIMEZONE_AUTO,
    CB_TIMEZONE_DEFAULT,
    CB_TIMEZONE_MANUAL,
    CB_TIMEZONE_PICK_PREFIX,
    PRESET_TIME_OPTIONS,
    TIMEZONE_OPTIONS,
    build_daily_tip_choice_keyboard,
    build_daily_tip_custom_keyboard,
    build_daily_tip_time_keyboard,
    build_final_keyboard,
    build_language_keyboard,
    build_location_reply_keyboard,
    build_reminders_choice_keyboard,
    build_reminders_custom_keyboard,
    build_reminders_time_keyboard,
    build_timezone_auto_keyboard,
    build_timezone_choice_keyboard,
    build_timezone_manual_keyboard,
    timezone_by_code,
)
from features.onboarding.texts import (
    alert_state_not_found,
    alert_invalid_time,
    alert_unknown_timezone_option,
    alert_unsupported_time_option,
    alert_timezone_detection_failed,
    location_keyboard_prompt,
    normalize_language,
    onboarding_daily_tip_custom_time_screen,
    onboarding_daily_tip_screen,
    onboarding_daily_tip_time_screen,
    onboarding_final_screen,
    onboarding_language_screen,
    onboarding_reminders_custom_time_screen,
    onboarding_reminders_screen,
    onboarding_reminders_time_screen,
    onboarding_timezone_auto_screen,
    onboarding_timezone_manual_screen,
    onboarding_timezone_screen,
    toast_daily_tips_disabled,
    toast_daily_tips_enabled,
    toast_default_settings_applied,
    toast_language_set,
    toast_reminders_disabled,
    toast_reminders_enabled,
    toast_timezone_set,
)


STEP_LANGUAGE = "language_select"
STEP_TIMEZONE_MENU = "timezone_menu"
STEP_TIMEZONE_AUTO = "timezone_auto"
STEP_TIMEZONE_MANUAL = "timezone_manual"
STEP_DAILY = "daily_tips"
STEP_DAILY_TIME = "daily_tips_time"
STEP_REMINDERS = "training_reminders"
STEP_REMINDERS_TIME = "training_reminders_time"
STEP_FINAL = "final"

WAIT_LOCATION = "waiting_location"
WAIT_DAILY_CUSTOM = "waiting_daily_custom_time"
WAIT_REMINDERS_CUSTOM = "waiting_reminders_custom_time"

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


@dataclass(slots=True)
class OnboardingState:
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
    onboarding_completed: bool
    onboarding_step: str
    waiting_state: str | None

    @property
    def ui_language(self) -> str:
        if self.language in {"ru", "en"}:
            return self.language
        if (self.telegram_language_code or "").lower().startswith("ru"):
            return "ru"
        return "en"


def _row_to_state(row) -> OnboardingState:
    return OnboardingState(
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
        onboarding_completed=bool(row["onboarding_completed"]),
        onboarding_step=row["onboarding_step"] or STEP_LANGUAGE,
        waiting_state=row["waiting_state"],
    )


def _load_state_by_telegram_id(telegram_id: int) -> OnboardingState | None:
    with get_connection() as conn:
        row = get_user_with_onboarding_by_telegram_id(conn, telegram_id)
    if row is None:
        return None
    return _row_to_state(row)


def _load_state_by_user_id(user_id: int) -> OnboardingState | None:
    with get_connection() as conn:
        row = get_user_with_onboarding_by_user_id(conn, user_id)
    if row is None:
        return None
    return _row_to_state(row)


def _resolve_initial_language(telegram_language_code: str | None) -> str:
    if not telegram_language_code:
        return "en"
    lowered = telegram_language_code.lower()
    if lowered.startswith("ru"):
        return "ru"
    if lowered.startswith("en"):
        return "en"
    return "en"


def ensure_initial_language(user_id: int, telegram_language_code: str | None) -> str:
    """Persist initial interface language from Telegram language code if needed."""
    with get_connection() as conn:
        row = get_user_with_onboarding_by_user_id(conn, user_id)
        if row is None:
            return _resolve_initial_language(telegram_language_code)

        current_language = row["interface_language"]
        resolved_language = (
            current_language
            if current_language in {"ru", "en"}
            else _resolve_initial_language(telegram_language_code)
        )
        if current_language not in {"ru", "en"}:
            update_onboarding_settings(conn, user_id=user_id, language=resolved_language)
    return resolved_language


def _update_state(user_id: int, **fields) -> None:
    with get_connection() as conn:
        update_onboarding_settings(conn, user_id=user_id, **fields)


def _normalized_timezone_lookup() -> dict[str, str]:
    lookup = {"UTC": "UTC"}
    for option in TIMEZONE_OPTIONS:
        zone_name = option.normalized_value.split(" UTC")[0]
        lookup[zone_name] = option.normalized_value
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


async def _remove_location_reply_keyboard(
    bot: Bot,
    chat_id: int,
    user_id: int,
) -> None:
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


async def _show_location_reply_keyboard(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
) -> None:
    await clear_service_layers(bot=bot, chat_id=chat_id, user_id=user_id)
    prompt_message = await safe_send_message(
        bot=bot,
        chat_id=chat_id,
        text=location_keyboard_prompt(language),
        reply_markup=build_location_reply_keyboard(language),
    )
    if prompt_message is not None:
        register_service_layer(user_id=user_id, message_id=prompt_message.message_id)


async def _render_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    text: str,
    reply_markup,
    *,
    onboarding_step: str,
    waiting_state: str | None = None,
    needs_location_keyboard: bool = False,
) -> None:
    if not needs_location_keyboard:
        await _remove_location_reply_keyboard(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
        )

    _update_state(
        user_id=user_id,
        onboarding_step=onboarding_step,
        waiting_state=waiting_state,
    )
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )

    if needs_location_keyboard:
        await _show_location_reply_keyboard(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
        )


async def show_language_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
) -> None:
    lang = normalize_language(language)
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=onboarding_language_screen(lang),
        reply_markup=build_language_keyboard(),
        onboarding_step=STEP_LANGUAGE,
    )


async def show_timezone_screen(bot: Bot, chat_id: int, user_id: int, language: str) -> None:
    lang = normalize_language(language)
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=onboarding_timezone_screen(lang),
        reply_markup=build_timezone_choice_keyboard(lang),
        onboarding_step=STEP_TIMEZONE_MENU,
    )


async def show_timezone_auto_screen(bot: Bot, chat_id: int, user_id: int, language: str) -> None:
    lang = normalize_language(language)
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=onboarding_timezone_auto_screen(lang),
        reply_markup=build_timezone_auto_keyboard(lang),
        onboarding_step=STEP_TIMEZONE_AUTO,
        waiting_state=WAIT_LOCATION,
        needs_location_keyboard=True,
    )


async def show_timezone_manual_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    *,
    warning_text: str | None = None,
) -> None:
    lang = normalize_language(language)
    text = onboarding_timezone_manual_screen(lang)
    if warning_text:
        text = f"{warning_text}\n\n{text}"
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=text,
        reply_markup=build_timezone_manual_keyboard(lang),
        onboarding_step=STEP_TIMEZONE_MANUAL,
    )


async def show_daily_tips_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    timezone_value: str,
) -> None:
    lang = normalize_language(language)
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=onboarding_daily_tip_screen(lang, timezone_value=timezone_value),
        reply_markup=build_daily_tip_choice_keyboard(lang),
        onboarding_step=STEP_DAILY,
    )


async def show_daily_tips_time_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    timezone_value: str,
) -> None:
    lang = normalize_language(language)
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=onboarding_daily_tip_time_screen(lang, timezone_value=timezone_value),
        reply_markup=build_daily_tip_time_keyboard(lang),
        onboarding_step=STEP_DAILY_TIME,
    )


async def show_daily_tips_custom_time_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    *,
    warning_text: str | None = None,
) -> None:
    lang = normalize_language(language)
    text = onboarding_daily_tip_custom_time_screen(lang)
    if warning_text:
        text = f"{warning_text}\n\n{text}"
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=text,
        reply_markup=build_daily_tip_custom_keyboard(lang),
        onboarding_step=STEP_DAILY_TIME,
        waiting_state=WAIT_DAILY_CUSTOM,
    )


async def show_reminders_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    timezone_value: str,
    daily_tips_enabled: bool,
    daily_tip_time: str | None,
) -> None:
    lang = normalize_language(language)
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=onboarding_reminders_screen(
            lang,
            timezone_value=timezone_value,
            daily_tips_enabled=daily_tips_enabled,
            daily_tip_time=daily_tip_time,
        ),
        reply_markup=build_reminders_choice_keyboard(lang),
        onboarding_step=STEP_REMINDERS,
    )


async def show_reminders_time_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    timezone_value: str,
    daily_tips_enabled: bool,
    daily_tip_time: str | None,
) -> None:
    lang = normalize_language(language)
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=onboarding_reminders_time_screen(
            lang,
            timezone_value=timezone_value,
            daily_tips_enabled=daily_tips_enabled,
            daily_tip_time=daily_tip_time,
        ),
        reply_markup=build_reminders_time_keyboard(lang),
        onboarding_step=STEP_REMINDERS_TIME,
    )


async def show_reminders_custom_time_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    *,
    warning_text: str | None = None,
) -> None:
    lang = normalize_language(language)
    text = onboarding_reminders_custom_time_screen(lang)
    if warning_text:
        text = f"{warning_text}\n\n{text}"
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=text,
        reply_markup=build_reminders_custom_keyboard(lang),
        onboarding_step=STEP_REMINDERS_TIME,
        waiting_state=WAIT_REMINDERS_CUSTOM,
    )


async def show_final_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    timezone_value: str,
    daily_tips_enabled: bool,
    daily_tip_time: str | None,
    training_reminders_enabled: bool,
    training_reminder_time: str | None,
    sound_enabled: bool,
) -> None:
    lang = normalize_language(language)
    await _render_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=lang,
        text=onboarding_final_screen(
            lang,
            timezone_value=timezone_value,
            daily_tips_enabled=daily_tips_enabled,
            daily_tip_time=daily_tip_time,
            training_reminders_enabled=training_reminders_enabled,
            training_reminder_time=training_reminder_time,
            sound_enabled=sound_enabled,
        ),
        reply_markup=build_final_keyboard(lang),
        onboarding_step=STEP_FINAL,
    )


async def show_current_onboarding_screen(
    bot: Bot,
    chat_id: int,
    user_id: int,
    telegram_id: int,
) -> None:
    """Render current onboarding step for user."""
    state = _load_state_by_user_id(user_id)
    if state is None:
        return

    if state.onboarding_completed:
        await show_main_menu(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            telegram_id=telegram_id,
        )
        return

    # Keep all onboarding screens in the explicitly selected interface language.
    language = normalize_language(state.language)
    if state.language not in {"ru", "en"} or state.onboarding_step == STEP_LANGUAGE:
        await show_language_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
        )
        return

    if state.waiting_state == WAIT_DAILY_CUSTOM:
        await show_daily_tips_custom_time_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
        )
        return
    if state.waiting_state == WAIT_REMINDERS_CUSTOM:
        await show_reminders_custom_time_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
        )
        return

    if state.onboarding_step == STEP_TIMEZONE_MENU:
        await show_timezone_screen(bot=bot, chat_id=chat_id, user_id=user_id, language=language)
        return
    if state.onboarding_step == STEP_TIMEZONE_AUTO:
        await show_timezone_auto_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
        )
        return
    if state.onboarding_step == STEP_TIMEZONE_MANUAL:
        await show_timezone_manual_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
        )
        return
    if state.onboarding_step == STEP_DAILY:
        await show_daily_tips_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            timezone_value=state.timezone,
        )
        return
    if state.onboarding_step == STEP_DAILY_TIME:
        await show_daily_tips_time_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            timezone_value=state.timezone,
        )
        return
    if state.onboarding_step == STEP_REMINDERS:
        await show_reminders_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=state.daily_tips_enabled,
            daily_tip_time=state.daily_tip_time,
        )
        return
    if state.onboarding_step == STEP_REMINDERS_TIME:
        await show_reminders_time_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=state.daily_tips_enabled,
            daily_tip_time=state.daily_tip_time,
        )
        return

    await show_final_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        timezone_value=state.timezone,
        daily_tips_enabled=state.daily_tips_enabled,
        daily_tip_time=state.daily_tip_time,
        training_reminders_enabled=state.training_reminders_enabled,
        training_reminder_time=state.training_reminder_time,
        sound_enabled=state.sound_enabled,
    )


async def _handle_back_callback(
    callback_data: str,
    bot: Bot,
    chat_id: int,
    state: OnboardingState,
) -> None:
    language = normalize_language(state.language)
    if callback_data == CB_BACK_TO_LANGUAGE:
        await show_language_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=state.user_id,
            language=language,
        )
    elif callback_data in {CB_BACK_TO_TIMEZONE, CB_BACK_TO_TIMEZONE_MENU}:
        await show_timezone_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=state.user_id,
            language=language,
        )
    elif callback_data == CB_BACK_TO_DAILY:
        await show_daily_tips_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
        )
    elif callback_data == CB_BACK_TO_DAILY_TIME:
        await show_daily_tips_time_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
        )
    elif callback_data == CB_BACK_TO_REMINDERS:
        await show_reminders_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=state.daily_tips_enabled,
            daily_tip_time=state.daily_tip_time,
        )
    elif callback_data == CB_BACK_TO_REMINDERS_TIME:
        await show_reminders_time_screen(
            bot=bot,
            chat_id=chat_id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=state.daily_tips_enabled,
            daily_tip_time=state.daily_tip_time,
        )


def _is_valid_time(value: str) -> bool:
    return bool(TIME_PATTERN.match(value.strip()))


async def process_onboarding_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Process onboarding callback actions. Returns True if handled."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if query is None or user is None or chat is None:
        return False

    callback_data = query.data or ""
    if not callback_data.startswith("onb:"):
        return False

    state = _load_state_by_telegram_id(user.id)
    if state is None:
        fallback_lang = "ru" if (user.language_code or "").lower().startswith("ru") else "en"
        await safe_answer_callback(
            query,
            text=alert_state_not_found(fallback_lang),
            show_alert=True,
        )
        return True

    if state.onboarding_completed:
        await safe_answer_callback(query)
        await show_main_menu(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            telegram_id=state.telegram_id,
        )
        return True

    if callback_data.startswith(CB_LANGUAGE_PREFIX):
        selected_language = normalize_language(callback_data.split(":")[-1])
        _update_state(
            state.user_id,
            language=selected_language,
            onboarding_step=STEP_TIMEZONE_MENU,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_language_set(selected_language),
            show_alert=False,
        )
        await show_timezone_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=selected_language,
        )
        return True

    # Keep all onboarding screens in the explicitly selected interface language.
    language = normalize_language(state.language)

    if callback_data in {
        CB_BACK_TO_LANGUAGE,
        CB_BACK_TO_TIMEZONE,
        CB_BACK_TO_TIMEZONE_MENU,
        CB_BACK_TO_DAILY,
        CB_BACK_TO_DAILY_TIME,
        CB_BACK_TO_REMINDERS,
        CB_BACK_TO_REMINDERS_TIME,
    }:
        await safe_answer_callback(query)
        await _handle_back_callback(
            callback_data=callback_data,
            bot=context.bot,
            chat_id=chat.id,
            state=state,
        )
        return True

    if callback_data == CB_TIMEZONE_AUTO:
        await safe_answer_callback(query)
        await show_timezone_auto_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
        )
        return True

    if callback_data == CB_TIMEZONE_MANUAL:
        await safe_answer_callback(query)
        await show_timezone_manual_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
        )
        return True

    if callback_data == CB_TIMEZONE_DEFAULT:
        with get_connection() as conn:
            apply_default_onboarding_settings(conn, user_id=state.user_id)
        await safe_answer_callback(
            query,
            text=toast_default_settings_applied(language),
            show_alert=False,
        )
        refreshed_state = _load_state_by_user_id(state.user_id)
        if refreshed_state is None:
            return True
        await show_final_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=refreshed_state.user_id,
            language=normalize_language(refreshed_state.language),
            timezone_value=refreshed_state.timezone,
            daily_tips_enabled=refreshed_state.daily_tips_enabled,
            daily_tip_time=refreshed_state.daily_tip_time,
            training_reminders_enabled=refreshed_state.training_reminders_enabled,
            training_reminder_time=refreshed_state.training_reminder_time,
            sound_enabled=refreshed_state.sound_enabled,
        )
        return True

    if callback_data.startswith(CB_TIMEZONE_PICK_PREFIX):
        code = callback_data.removeprefix(CB_TIMEZONE_PICK_PREFIX)
        option = timezone_by_code(code)
        if option is None:
            await safe_answer_callback(
                query,
                text=alert_unknown_timezone_option(language),
                show_alert=True,
            )
            return True
        _update_state(
            state.user_id,
            timezone=option.normalized_value,
            onboarding_step=STEP_DAILY,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_timezone_set(language, option.normalized_value),
            show_alert=False,
        )
        await show_daily_tips_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=option.normalized_value,
        )
        return True

    if callback_data == CB_DAILY_ENABLE:
        _update_state(
            state.user_id,
            daily_tips_enabled=True,
            onboarding_step=STEP_DAILY_TIME,
            waiting_state=None,
        )
        await safe_answer_callback(query)
        await show_daily_tips_time_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
        )
        return True

    if callback_data == CB_DAILY_DISABLE:
        _update_state(
            state.user_id,
            daily_tips_enabled=False,
            daily_tip_time=None,
            onboarding_step=STEP_REMINDERS,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_daily_tips_disabled(language),
            show_alert=False,
        )
        await show_reminders_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=False,
            daily_tip_time=None,
        )
        return True

    if callback_data == CB_DAILY_TIME_CUSTOM:
        await safe_answer_callback(query)
        await show_daily_tips_custom_time_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
        )
        return True

    if callback_data.startswith(CB_DAILY_TIME_PREFIX):
        selected_time = callback_data.removeprefix(CB_DAILY_TIME_PREFIX)
        if selected_time not in PRESET_TIME_OPTIONS:
            await safe_answer_callback(
                query,
                text=alert_unsupported_time_option(language),
                show_alert=True,
            )
            return True

        _update_state(
            state.user_id,
            daily_tips_enabled=True,
            daily_tip_time=selected_time,
            onboarding_step=STEP_REMINDERS,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_daily_tips_enabled(language, selected_time),
            show_alert=False,
        )
        await show_reminders_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=True,
            daily_tip_time=selected_time,
        )
        return True

    if callback_data == CB_DAILY_CUSTOM_CANCEL:
        await safe_answer_callback(query)
        await show_daily_tips_time_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
        )
        return True

    if callback_data == CB_REMINDERS_ENABLE:
        _update_state(
            state.user_id,
            training_reminders_enabled=True,
            onboarding_step=STEP_REMINDERS_TIME,
            waiting_state=None,
        )
        await safe_answer_callback(query)
        await show_reminders_time_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=state.daily_tips_enabled,
            daily_tip_time=state.daily_tip_time,
        )
        return True

    if callback_data == CB_REMINDERS_DISABLE:
        _update_state(
            state.user_id,
            training_reminders_enabled=False,
            training_reminder_time=None,
            sound_enabled=True,
            onboarding_step=STEP_FINAL,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_reminders_disabled(language),
            show_alert=False,
        )
        await show_final_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=state.daily_tips_enabled,
            daily_tip_time=state.daily_tip_time,
            training_reminders_enabled=False,
            training_reminder_time=None,
            sound_enabled=True,
        )
        return True

    if callback_data == CB_REMINDERS_TIME_CUSTOM:
        await safe_answer_callback(query)
        await show_reminders_custom_time_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
        )
        return True

    if callback_data.startswith(CB_REMINDERS_TIME_PREFIX):
        selected_time = callback_data.removeprefix(CB_REMINDERS_TIME_PREFIX)
        if selected_time not in PRESET_TIME_OPTIONS:
            await safe_answer_callback(
                query,
                text=alert_unsupported_time_option(language),
                show_alert=True,
            )
            return True

        _update_state(
            state.user_id,
            training_reminders_enabled=True,
            training_reminder_time=selected_time,
            sound_enabled=True,
            onboarding_step=STEP_FINAL,
            waiting_state=None,
        )
        await safe_answer_callback(
            query,
            text=toast_reminders_enabled(language, selected_time),
            show_alert=False,
        )
        await show_final_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=state.daily_tips_enabled,
            daily_tip_time=state.daily_tip_time,
            training_reminders_enabled=True,
            training_reminder_time=selected_time,
            sound_enabled=True,
        )
        return True

    if callback_data == CB_REMINDERS_CUSTOM_CANCEL:
        await safe_answer_callback(query)
        await show_reminders_time_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=language,
            timezone_value=state.timezone,
            daily_tips_enabled=state.daily_tips_enabled,
            daily_tip_time=state.daily_tip_time,
        )
        return True

    if callback_data == CB_FINAL_TO_MENU:
        _update_state(
            state.user_id,
            onboarding_completed=True,
            onboarding_step=STEP_FINAL,
            waiting_state=None,
            sound_enabled=True,
        )
        await safe_answer_callback(query)
        await _remove_location_reply_keyboard(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
        )
        await show_main_menu(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            telegram_id=state.telegram_id,
        )
        return True

    await safe_answer_callback(query)
    return True


async def process_onboarding_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Process location messages for timezone detection."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if user is None or chat is None or message is None:
        return False
    if message.location is None:
        return False

    state = _load_state_by_telegram_id(user.id)
    if state is None or state.onboarding_completed:
        return False

    if state.waiting_state != WAIT_LOCATION:
        return True

    detected = detect_timezone_name(
        latitude=message.location.latitude,
        longitude=message.location.longitude,
    )
    await _remove_location_reply_keyboard(
        bot=context.bot,
        chat_id=chat.id,
        user_id=state.user_id,
    )

    if not detected:
        await show_timezone_manual_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=normalize_language(state.language),
            warning_text=alert_timezone_detection_failed(normalize_language(state.language)),
        )
        return True

    normalized_timezone = normalize_timezone_value(detected)
    _update_state(
        state.user_id,
        timezone=normalized_timezone,
        onboarding_step=STEP_DAILY,
        waiting_state=None,
    )
    await show_daily_tips_screen(
        bot=context.bot,
        chat_id=chat.id,
        user_id=state.user_id,
        language=normalize_language(state.language),
        timezone_value=normalized_timezone,
    )
    return True


async def process_onboarding_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Process custom time input messages for onboarding."""
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message
    if user is None or chat is None or message is None:
        return False

    text_value = (message.text or "").strip()
    if not text_value:
        return False

    state = _load_state_by_telegram_id(user.id)
    if state is None or state.onboarding_completed:
        return False

    if state.waiting_state not in {WAIT_DAILY_CUSTOM, WAIT_REMINDERS_CUSTOM}:
        return True

    if not _is_valid_time(text_value):
        ui_language = normalize_language(state.language)
        if state.waiting_state == WAIT_DAILY_CUSTOM:
            await show_daily_tips_custom_time_screen(
                bot=context.bot,
                chat_id=chat.id,
                user_id=state.user_id,
                language=ui_language,
                warning_text=alert_invalid_time(ui_language),
            )
        else:
            await show_reminders_custom_time_screen(
                bot=context.bot,
                chat_id=chat.id,
                user_id=state.user_id,
                language=ui_language,
                warning_text=alert_invalid_time(ui_language),
            )
        return True

    if state.waiting_state == WAIT_DAILY_CUSTOM:
        ui_language = normalize_language(state.language)
        _update_state(
            state.user_id,
            daily_tips_enabled=True,
            daily_tip_time=text_value,
            onboarding_step=STEP_REMINDERS,
            waiting_state=None,
        )
        await show_reminders_screen(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            language=ui_language,
            timezone_value=state.timezone,
            daily_tips_enabled=True,
            daily_tip_time=text_value,
        )
        return True

    ui_language = normalize_language(state.language)
    _update_state(
        state.user_id,
        training_reminders_enabled=True,
        training_reminder_time=text_value,
        sound_enabled=True,
        onboarding_step=STEP_FINAL,
        waiting_state=None,
    )
    await show_final_screen(
        bot=context.bot,
        chat_id=chat.id,
        user_id=state.user_id,
        language=ui_language,
        timezone_value=state.timezone,
        daily_tips_enabled=state.daily_tips_enabled,
        daily_tip_time=state.daily_tip_time,
        training_reminders_enabled=True,
        training_reminder_time=text_value,
        sound_enabled=True,
    )
    return True
