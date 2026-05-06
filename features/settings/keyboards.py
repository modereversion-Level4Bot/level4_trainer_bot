"""Keyboard builders for settings feature."""

from __future__ import annotations

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from features.onboarding.keyboards import TIMEZONE_OPTIONS
from features.settings.texts import (
    daily_grammar_tip_button_text,
    delete_account_button_text,
    interface_language_button_text,
    location_button_text,
    management_button_text,
    main_menu_button_text,
    notification_sounds_button_text,
    normalize_language,
    progress_button_text,
    restart_button_text,
    reset_target_label,
    settings_account_section_button_text,
    settings_main_section_button_text,
    settings_notifications_section_button_text,
    timezone_auto_button_text,
    timezone_button_text,
    timezone_manual_button_text,
    training_reminders_button_text,
)


SETTINGS_CALLBACK_PREFIX = "settings:"

CB_SETTINGS_MAIN = "settings:main"
CB_SETTINGS_HOME = "settings:home"
CB_SETTINGS_SECTION_MAIN = "settings:section:main"
CB_SETTINGS_SECTION_NOTIFICATIONS = "settings:section:notifications"
CB_SETTINGS_SECTION_ACCOUNT = "settings:section:account"

CB_SETTINGS_LANGUAGE = "settings:language"
CB_SETTINGS_LANGUAGE_RU = "settings:language:ru"
CB_SETTINGS_LANGUAGE_EN = "settings:language:en"
CB_SETTINGS_LANGUAGE_BACK = "settings:language:back"

CB_SETTINGS_TIMEZONE = "settings:timezone"
CB_SETTINGS_TIMEZONE_AUTO = "settings:timezone:auto"
CB_SETTINGS_TIMEZONE_MANUAL = "settings:timezone:manual"
CB_SETTINGS_TIMEZONE_PICK_PREFIX = "settings:timezone:pick:"
CB_SETTINGS_TIMEZONE_BACK = "settings:timezone:back"
CB_SETTINGS_TIMEZONE_AUTO_BACK = "settings:timezone:auto:back"
CB_SETTINGS_TIMEZONE_MANUAL_BACK = "settings:timezone:manual:back"

CB_SETTINGS_DAILY = "settings:daily"
CB_SETTINGS_DAILY_ENABLE = "settings:daily:enable"
CB_SETTINGS_DAILY_DISABLE = "settings:daily:disable"
CB_SETTINGS_DAILY_TIME = "settings:daily:time"
CB_SETTINGS_DAILY_TIME_PICK_PREFIX = "settings:daily:time:pick:"
CB_SETTINGS_DAILY_TIME_CUSTOM = "settings:daily:time:custom"
CB_SETTINGS_DAILY_TIME_CUSTOM_CANCEL = "settings:daily:time:custom:cancel"
CB_SETTINGS_DAILY_BACK = "settings:daily:back"
CB_SETTINGS_DAILY_TIME_BACK = "settings:daily:time:back"

CB_SETTINGS_REMINDERS = "settings:reminders"
CB_SETTINGS_REMINDERS_ENABLE = "settings:reminders:enable"
CB_SETTINGS_REMINDERS_DISABLE = "settings:reminders:disable"
CB_SETTINGS_REMINDERS_TIME = "settings:reminders:time"
CB_SETTINGS_REMINDERS_TIME_PICK_PREFIX = "settings:reminders:time:pick:"
CB_SETTINGS_REMINDERS_TIME_CUSTOM = "settings:reminders:time:custom"
CB_SETTINGS_REMINDERS_TIME_CUSTOM_CANCEL = "settings:reminders:time:custom:cancel"
CB_SETTINGS_REMINDERS_BACK = "settings:reminders:back"
CB_SETTINGS_REMINDERS_TIME_BACK = "settings:reminders:time:back"

CB_SETTINGS_SOUND = "settings:sound"
CB_SETTINGS_SOUND_ENABLE = "settings:sound:enable"
CB_SETTINGS_SOUND_DISABLE = "settings:sound:disable"
CB_SETTINGS_SOUND_BACK = "settings:sound:back"

CB_SETTINGS_MANAGEMENT = "settings:management"

CB_SETTINGS_RESET_PROGRESS = "settings:reset"
CB_SETTINGS_RESET_GRAMMAR = "settings:reset:grammar"
CB_SETTINGS_RESET_QUESTIONS = "settings:reset:questions"
CB_SETTINGS_RESET_ROUTES = "settings:reset:routes"
CB_SETTINGS_RESET_ALL = "settings:reset:all"
CB_SETTINGS_RESET_CONFIRM_PREFIX = "settings:reset:confirm:"
CB_SETTINGS_RESET_CANCEL = "settings:reset:cancel"
CB_SETTINGS_RESET_BACK = "settings:reset:back"

CB_SETTINGS_RESTART_ONBOARDING = "settings:restart"
CB_SETTINGS_RESTART_CONFIRM = "settings:restart:confirm"
CB_SETTINGS_RESTART_CANCEL = "settings:restart:cancel"

CB_SETTINGS_DELETE_ACCOUNT = "settings:delete"
CB_SETTINGS_DELETE_CONTINUE = "settings:delete:continue"
CB_SETTINGS_DELETE_CONFIRM = "settings:delete:confirm"
CB_SETTINGS_DELETE_CANCEL = "settings:delete:cancel"

RESET_TARGET_BY_CALLBACK = {
    CB_SETTINGS_RESET_GRAMMAR: "grammar",
    CB_SETTINGS_RESET_QUESTIONS: "questions",
    CB_SETTINGS_RESET_ROUTES: "routes",
    CB_SETTINGS_RESET_ALL: "all",
}

def timezone_value_by_code(code: str) -> str | None:
    for option in TIMEZONE_OPTIONS:
        if option.code == code:
            return option.normalized_value
    return None


def _back_text(language: str) -> str:
    _ = language
    return "⬅️"


def _home_text(language: str) -> str:
    _ = language
    return "🏠"


def _cancel_text(language: str) -> str:
    return "⛔ Отмена" if normalize_language(language) == "ru" else "⛔ Cancel"


def _yes_reset_text(language: str) -> str:
    return "♻️ Да, сбросить" if normalize_language(language) == "ru" else "♻️ Yes, reset"


def _restart_confirm_text(language: str) -> str:
    return "🔄 Перезапустить" if normalize_language(language) == "ru" else "🔄 Restart"


def _delete_continue_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Продолжить удаление"
    return "⚠️ Continue deletion"


def _delete_confirm_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🗑 Да, удалить аккаунт"
    return "🗑 Yes, delete account"


def build_settings_main_keyboard(language: str, *, is_admin: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                settings_main_section_button_text(language),
                callback_data=CB_SETTINGS_SECTION_MAIN,
            )
        ],
        [
            InlineKeyboardButton(
                settings_notifications_section_button_text(language),
                callback_data=CB_SETTINGS_SECTION_NOTIFICATIONS,
            )
        ],
        [
            InlineKeyboardButton(
                settings_account_section_button_text(language),
                callback_data=CB_SETTINGS_SECTION_ACCOUNT,
            )
        ],
    ]
    if is_admin:
        rows.append(
            [InlineKeyboardButton(management_button_text(language), callback_data=CB_SETTINGS_MANAGEMENT)]
        )
    rows.append([InlineKeyboardButton(main_menu_button_text(language), callback_data=CB_SETTINGS_HOME)])
    return InlineKeyboardMarkup(rows)


def build_settings_main_section_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    interface_language_button_text(language),
                    callback_data=CB_SETTINGS_LANGUAGE,
                )
            ],
            [
                InlineKeyboardButton(
                    timezone_button_text(language),
                    callback_data=CB_SETTINGS_TIMEZONE,
                )
            ],
            [
                InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_MAIN),
                InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
            ],
        ]
    )


def build_settings_notifications_section_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    notification_sounds_button_text(language),
                    callback_data=CB_SETTINGS_SOUND,
                )
            ],
            [
                InlineKeyboardButton(
                    daily_grammar_tip_button_text(language),
                    callback_data=CB_SETTINGS_DAILY,
                )
            ],
            [
                InlineKeyboardButton(
                    training_reminders_button_text(language),
                    callback_data=CB_SETTINGS_REMINDERS,
                )
            ],
            [
                InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_MAIN),
                InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
            ],
        ]
    )


def build_settings_account_section_keyboard(language: str, *, is_admin: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(progress_button_text(language), callback_data=CB_SETTINGS_RESET_PROGRESS),
            InlineKeyboardButton(restart_button_text(language), callback_data=CB_SETTINGS_RESTART_ONBOARDING),
        ]
    ]
    if not is_admin:
        rows.append(
            [InlineKeyboardButton(delete_account_button_text(language), callback_data=CB_SETTINGS_DELETE_ACCOUNT)]
        )
    rows.append(
        [
            InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_MAIN),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_settings_language_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data=CB_SETTINGS_LANGUAGE_RU),
                InlineKeyboardButton("🇬🇧 English", callback_data=CB_SETTINGS_LANGUAGE_EN),
            ],
            [
                InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_LANGUAGE_BACK),
                InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
            ],
        ]
    )


def build_settings_timezone_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    timezone_auto_button_text(language),
                    callback_data=CB_SETTINGS_TIMEZONE_AUTO,
                )
            ],
            [
                InlineKeyboardButton(
                    timezone_manual_button_text(language),
                    callback_data=CB_SETTINGS_TIMEZONE_MANUAL,
                )
            ],
            [
                InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_TIMEZONE_BACK),
                InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
            ],
        ]
    )


def build_settings_timezone_auto_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_TIMEZONE_AUTO_BACK),
                InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
            ]
        ]
    )


def build_settings_location_reply_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(text=location_button_text(language), request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def build_settings_timezone_manual_keyboard(language: str) -> InlineKeyboardMarkup:
    lang = normalize_language(language)
    rows: list[list[InlineKeyboardButton]] = []
    for option in TIMEZONE_OPTIONS:
        rows.append(
            [
                InlineKeyboardButton(
                    option.ru_label if lang == "ru" else option.en_label,
                    callback_data=f"{CB_SETTINGS_TIMEZONE_PICK_PREFIX}{option.code}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_TIMEZONE_MANUAL_BACK),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_settings_daily_keyboard(language: str, *, enabled: bool) -> InlineKeyboardMarkup:
    lang = normalize_language(language)
    if enabled:
        toggle_text = "🚫 Выключить" if lang == "ru" else "🚫 Disable"
        time_text = "🕒 Изменить время" if lang == "ru" else "🕒 Change time"
        rows = [
            [InlineKeyboardButton(time_text, callback_data=CB_SETTINGS_DAILY_TIME)],
            [InlineKeyboardButton(toggle_text, callback_data=CB_SETTINGS_DAILY_DISABLE)],
        ]
    else:
        toggle_text = "✅ Включить" if lang == "ru" else "✅ Enable"
        rows = [
            [InlineKeyboardButton(toggle_text, callback_data=CB_SETTINGS_DAILY_ENABLE)],
        ]
    rows.append(
        [
            InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_DAILY_BACK),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_settings_daily_time_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🌄 09:00", callback_data=f"{CB_SETTINGS_DAILY_TIME_PICK_PREFIX}09:00"),
            InlineKeyboardButton("🌇 12:00", callback_data=f"{CB_SETTINGS_DAILY_TIME_PICK_PREFIX}12:00"),
        ],
        [
            InlineKeyboardButton("🌆 18:00", callback_data=f"{CB_SETTINGS_DAILY_TIME_PICK_PREFIX}18:00"),
            InlineKeyboardButton("🌃 21:00", callback_data=f"{CB_SETTINGS_DAILY_TIME_PICK_PREFIX}21:00"),
        ],
    ]
    other_text = "⏱️ Другое время" if normalize_language(language) == "ru" else "⏱️ Other time"
    rows.append([InlineKeyboardButton(other_text, callback_data=CB_SETTINGS_DAILY_TIME_CUSTOM)])
    rows.append(
        [
            InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_DAILY_TIME_BACK),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_settings_daily_custom_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(_cancel_text(language), callback_data=CB_SETTINGS_DAILY_TIME_CUSTOM_CANCEL),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ]]
    )


def build_settings_reminders_keyboard(language: str, *, enabled: bool) -> InlineKeyboardMarkup:
    lang = normalize_language(language)
    if enabled:
        toggle_text = "🚫 Выключить" if lang == "ru" else "🚫 Disable"
        time_text = "🕒 Изменить время" if lang == "ru" else "🕒 Change time"
        rows = [
            [InlineKeyboardButton(time_text, callback_data=CB_SETTINGS_REMINDERS_TIME)],
            [InlineKeyboardButton(toggle_text, callback_data=CB_SETTINGS_REMINDERS_DISABLE)],
        ]
    else:
        toggle_text = "✅ Включить" if lang == "ru" else "✅ Enable"
        rows = [[InlineKeyboardButton(toggle_text, callback_data=CB_SETTINGS_REMINDERS_ENABLE)]]
    rows.append(
        [
            InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_REMINDERS_BACK),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_settings_reminders_time_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🌄 09:00", callback_data=f"{CB_SETTINGS_REMINDERS_TIME_PICK_PREFIX}09:00"),
            InlineKeyboardButton("🌇 12:00", callback_data=f"{CB_SETTINGS_REMINDERS_TIME_PICK_PREFIX}12:00"),
        ],
        [
            InlineKeyboardButton("🌆 18:00", callback_data=f"{CB_SETTINGS_REMINDERS_TIME_PICK_PREFIX}18:00"),
            InlineKeyboardButton("🌃 21:00", callback_data=f"{CB_SETTINGS_REMINDERS_TIME_PICK_PREFIX}21:00"),
        ],
    ]
    other_text = "⏱️ Другое время" if normalize_language(language) == "ru" else "⏱️ Other time"
    rows.append([InlineKeyboardButton(other_text, callback_data=CB_SETTINGS_REMINDERS_TIME_CUSTOM)])
    rows.append(
        [
            InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_REMINDERS_TIME_BACK),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_settings_reminders_custom_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(_cancel_text(language), callback_data=CB_SETTINGS_REMINDERS_TIME_CUSTOM_CANCEL),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ]]
    )


def build_settings_sound_keyboard(language: str, *, enabled: bool) -> InlineKeyboardMarkup:
    lang = normalize_language(language)
    if enabled:
        toggle_text = "🚫 Выключить звук" if lang == "ru" else "🚫 Disable sound"
        toggle_callback = CB_SETTINGS_SOUND_DISABLE
    else:
        toggle_text = "✅ Включить звук" if lang == "ru" else "✅ Enable sound"
        toggle_callback = CB_SETTINGS_SOUND_ENABLE
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(toggle_text, callback_data=toggle_callback)],
            [
                InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_SOUND_BACK),
                InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
            ],
        ]
    )


def build_settings_reset_progress_keyboard(language: str) -> InlineKeyboardMarkup:
    lang = normalize_language(language)
    rows = [
        [
            InlineKeyboardButton(reset_target_label(lang, "grammar"), callback_data=CB_SETTINGS_RESET_GRAMMAR),
            InlineKeyboardButton(reset_target_label(lang, "questions"), callback_data=CB_SETTINGS_RESET_QUESTIONS),
            InlineKeyboardButton(reset_target_label(lang, "routes"), callback_data=CB_SETTINGS_RESET_ROUTES),
        ],
        [InlineKeyboardButton(reset_target_label(lang, "all"), callback_data=CB_SETTINGS_RESET_ALL)],
        [
            InlineKeyboardButton(_back_text(language), callback_data=CB_SETTINGS_RESET_BACK),
            InlineKeyboardButton(_home_text(language), callback_data=CB_SETTINGS_HOME),
        ],
    ]
    return InlineKeyboardMarkup(rows)


def build_settings_reset_confirm_keyboard(language: str, target: str) -> InlineKeyboardMarkup:
    confirm_callback = f"{CB_SETTINGS_RESET_CONFIRM_PREFIX}{target}"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(_cancel_text(language), callback_data=CB_SETTINGS_RESET_CANCEL),
                InlineKeyboardButton(_yes_reset_text(language), callback_data=confirm_callback),
            ]
        ]
    )


def build_settings_restart_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(_cancel_text(language), callback_data=CB_SETTINGS_RESTART_CANCEL),
                InlineKeyboardButton(_restart_confirm_text(language), callback_data=CB_SETTINGS_RESTART_CONFIRM),
            ]
        ]
    )


def build_settings_delete_account_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(_cancel_text(language), callback_data=CB_SETTINGS_DELETE_CANCEL)],
            [InlineKeyboardButton(_delete_continue_text(language), callback_data=CB_SETTINGS_DELETE_CONTINUE)],
        ]
    )


def build_settings_delete_account_confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(_cancel_text(language), callback_data=CB_SETTINGS_DELETE_CANCEL)],
            [InlineKeyboardButton(_delete_confirm_text(language), callback_data=CB_SETTINGS_DELETE_CONFIRM)],
        ]
    )
