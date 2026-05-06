"""Keyboard builders for onboarding feature."""

from __future__ import annotations

from dataclasses import dataclass

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from features.onboarding.texts import (
    back_button,
    cancel_button,
    custom_time_button,
    final_onboarding_button,
    location_button,
    quick_setup_button,
)


ONBOARDING_CALLBACK_PREFIX = "onb:"

CB_LANGUAGE_PREFIX = "onb:lang:"
CB_TIMEZONE_AUTO = "onb:tz:auto"
CB_TIMEZONE_MANUAL = "onb:tz:manual"
CB_TIMEZONE_DEFAULT = "onb:tz:default"
CB_TIMEZONE_PICK_PREFIX = "onb:tz:pick:"

CB_DAILY_ENABLE = "onb:daily:enable"
CB_DAILY_DISABLE = "onb:daily:disable"
CB_DAILY_TIME_PREFIX = "onb:daily_time:"
CB_DAILY_TIME_CUSTOM = "onb:daily_time:custom"
CB_DAILY_CUSTOM_CANCEL = "onb:daily_custom:cancel"

CB_REMINDERS_ENABLE = "onb:reminders:enable"
CB_REMINDERS_DISABLE = "onb:reminders:disable"
CB_REMINDERS_TIME_PREFIX = "onb:reminders_time:"
CB_REMINDERS_TIME_CUSTOM = "onb:reminders_time:custom"
CB_REMINDERS_CUSTOM_CANCEL = "onb:reminders_custom:cancel"

CB_BACK_TO_LANGUAGE = "onb:back:language"
CB_BACK_TO_TIMEZONE = "onb:back:timezone"
CB_BACK_TO_TIMEZONE_MENU = "onb:back:timezone_menu"
CB_BACK_TO_DAILY = "onb:back:daily"
CB_BACK_TO_DAILY_TIME = "onb:back:daily_time"
CB_BACK_TO_REMINDERS = "onb:back:reminders"
CB_BACK_TO_REMINDERS_TIME = "onb:back:reminders_time"

CB_FINAL_TO_MENU = "onb:final:menu"


@dataclass(frozen=True, slots=True)
class TimezoneOption:
    code: str
    normalized_value: str
    ru_label: str
    en_label: str


TIMEZONE_OPTIONS: tuple[TimezoneOption, ...] = (
    TimezoneOption("utc", "UTC", "UTC", "UTC"),
    TimezoneOption(
        "kaliningrad",
        "Europe/Kaliningrad UTC+2",
        "UTC+2 — Калининград",
        "UTC+2 — Kaliningrad",
    ),
    TimezoneOption("moscow", "Europe/Moscow UTC+3", "UTC+3 — Москва", "UTC+3 — Moscow"),
    TimezoneOption("samara", "Europe/Samara UTC+4", "UTC+4 — Самара", "UTC+4 — Samara"),
    TimezoneOption(
        "yekaterinburg",
        "Asia/Yekaterinburg UTC+5",
        "UTC+5 — Екатеринбург",
        "UTC+5 — Yekaterinburg",
    ),
    TimezoneOption("omsk", "Asia/Omsk UTC+6", "UTC+6 — Омск", "UTC+6 — Omsk"),
    TimezoneOption(
        "krasnoyarsk",
        "Asia/Krasnoyarsk UTC+7",
        "UTC+7 — Красноярск",
        "UTC+7 — Krasnoyarsk",
    ),
    TimezoneOption("irkutsk", "Asia/Irkutsk UTC+8", "UTC+8 — Иркутск", "UTC+8 — Irkutsk"),
    TimezoneOption("yakutsk", "Asia/Yakutsk UTC+9", "UTC+9 — Якутск", "UTC+9 — Yakutsk"),
    TimezoneOption(
        "vladivostok",
        "Asia/Vladivostok UTC+10",
        "UTC+10 — Владивосток",
        "UTC+10 — Vladivostok",
    ),
    TimezoneOption(
        "magadan",
        "Asia/Magadan UTC+11",
        "UTC+11 — Магадан",
        "UTC+11 — Magadan",
    ),
    TimezoneOption(
        "kamchatka",
        "Asia/Kamchatka UTC+12",
        "UTC+12 — Камчатка",
        "UTC+12 — Kamchatka",
    ),
)


PRESET_TIME_OPTIONS = ("09:00", "12:00", "18:00", "21:00")


def timezone_by_code(code: str) -> TimezoneOption | None:
    for option in TIMEZONE_OPTIONS:
        if option.code == code:
            return option
    return None


def build_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data=f"{CB_LANGUAGE_PREFIX}ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data=f"{CB_LANGUAGE_PREFIX}en"),
            ],
        ]
    )


def build_timezone_choice_keyboard(language: str) -> InlineKeyboardMarkup:
    if language == "ru":
        auto_text = "📍 Автоматически"
        manual_text = "🕒 Выбрать вручную"
    else:
        auto_text = "📍 Automatically"
        manual_text = "🕒 Choose manually"

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(auto_text, callback_data=CB_TIMEZONE_AUTO),
                InlineKeyboardButton(manual_text, callback_data=CB_TIMEZONE_MANUAL),
            ],
            [InlineKeyboardButton(quick_setup_button(language), callback_data=CB_TIMEZONE_DEFAULT)],
            [InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_LANGUAGE)],
        ]
    )


def build_timezone_auto_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_TIMEZONE)],
        ]
    )


def build_location_reply_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text=location_button(language), request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def build_timezone_manual_keyboard(language: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for option in TIMEZONE_OPTIONS:
        rows.append(
            [
                InlineKeyboardButton(
                    option.ru_label if language == "ru" else option.en_label,
                    callback_data=f"{CB_TIMEZONE_PICK_PREFIX}{option.code}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_TIMEZONE)])
    return InlineKeyboardMarkup(rows)


def build_daily_tip_choice_keyboard(language: str) -> InlineKeyboardMarkup:
    if language == "ru":
        enable_text = "✅ Включить"
        disable_text = "🚫 Не включать"
    else:
        enable_text = "✅ Enable"
        disable_text = "🚫 Do not enable"

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(enable_text, callback_data=CB_DAILY_ENABLE),
                InlineKeyboardButton(disable_text, callback_data=CB_DAILY_DISABLE),
            ],
            [InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_TIMEZONE_MENU)],
        ]
    )


def build_daily_tip_time_keyboard(language: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton("🌄 09:00", callback_data=f"{CB_DAILY_TIME_PREFIX}09:00"),
            InlineKeyboardButton("🌇 12:00", callback_data=f"{CB_DAILY_TIME_PREFIX}12:00"),
        ],
        [
            InlineKeyboardButton("🌆 18:00", callback_data=f"{CB_DAILY_TIME_PREFIX}18:00"),
            InlineKeyboardButton("🌃 21:00", callback_data=f"{CB_DAILY_TIME_PREFIX}21:00"),
        ],
    ]
    rows.append(
        [
            InlineKeyboardButton(
                custom_time_button(language),
                callback_data=CB_DAILY_TIME_CUSTOM,
            )
        ]
    )
    rows.append([InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_DAILY)])
    return InlineKeyboardMarkup(rows)


def build_daily_tip_custom_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(cancel_button(language), callback_data=CB_DAILY_CUSTOM_CANCEL)],
            [InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_DAILY_TIME)],
        ]
    )


def build_reminders_choice_keyboard(language: str) -> InlineKeyboardMarkup:
    if language == "ru":
        enable_text = "✅ Включить"
        disable_text = "🚫 Не включать"
    else:
        enable_text = "✅ Enable"
        disable_text = "🚫 Do not enable"

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(enable_text, callback_data=CB_REMINDERS_ENABLE),
                InlineKeyboardButton(disable_text, callback_data=CB_REMINDERS_DISABLE),
            ],
            [InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_DAILY)],
        ]
    )


def build_reminders_time_keyboard(language: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton("🌄 09:00", callback_data=f"{CB_REMINDERS_TIME_PREFIX}09:00"),
            InlineKeyboardButton("🌇 12:00", callback_data=f"{CB_REMINDERS_TIME_PREFIX}12:00"),
        ],
        [
            InlineKeyboardButton("🌆 18:00", callback_data=f"{CB_REMINDERS_TIME_PREFIX}18:00"),
            InlineKeyboardButton("🌃 21:00", callback_data=f"{CB_REMINDERS_TIME_PREFIX}21:00"),
        ],
    ]
    rows.append(
        [
            InlineKeyboardButton(
                custom_time_button(language),
                callback_data=CB_REMINDERS_TIME_CUSTOM,
            )
        ]
    )
    rows.append([InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_REMINDERS)])
    return InlineKeyboardMarkup(rows)


def build_reminders_custom_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(cancel_button(language), callback_data=CB_REMINDERS_CUSTOM_CANCEL)],
            [InlineKeyboardButton(back_button(language), callback_data=CB_BACK_TO_REMINDERS_TIME)],
        ]
    )


def build_final_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(final_onboarding_button(language), callback_data=CB_FINAL_TO_MENU)]]
    )
