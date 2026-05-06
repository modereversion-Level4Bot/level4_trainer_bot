"""Texts for onboarding feature."""

from __future__ import annotations

from typing import Literal


Language = Literal["ru", "en"]


INTERFACE_LANGUAGE_NAMES = {
    "ru": "Русский",
    "en": "English",
}

INTERFACE_LANGUAGE_FLAGS = {
    "ru": "🇷🇺",
    "en": "🇬🇧",
}


def normalize_language(language: str | None) -> Language:
    if language == "ru":
        return "ru"
    return "en"


def interface_language_name(language: str | None) -> str:
    return INTERFACE_LANGUAGE_NAMES[normalize_language(language)]


def interface_language_flag(language: str | None) -> str:
    return INTERFACE_LANGUAGE_FLAGS[normalize_language(language)]


def interface_language_line(language: str | None) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return f"{interface_language_flag(lang)} Язык интерфейса: <b>{interface_language_name(lang)}</b>"
    return f"{interface_language_flag(lang)} Interface language: <b>{interface_language_name(lang)}</b>"


def back_button(language: str) -> str:
    return "⬅️ Назад" if normalize_language(language) == "ru" else "⬅️ Back"


def final_onboarding_button(language: str) -> str:
    return "🚀 Поехали!" if normalize_language(language) == "ru" else "🚀 Let’s go!"


def quick_setup_button(language: str) -> str:
    return "⚡ Быстрая настройка" if normalize_language(language) == "ru" else "⚡ Quick setup"


def custom_time_button(language: str) -> str:
    return "⏱️ Другое время" if normalize_language(language) == "ru" else "⏱️ Other time"


def cancel_button(language: str) -> str:
    return "❌ Отмена" if normalize_language(language) == "ru" else "❌ Cancel"


def location_button(language: str) -> str:
    return (
        "📍 Отправить геолокацию"
        if normalize_language(language) == "ru"
        else "📍 Send location"
    )


def daily_tip_enabled_text(language: str) -> str:
    return "Включён" if normalize_language(language) == "ru" else "Enabled"


def daily_tip_disabled_text(language: str) -> str:
    return "Выключен" if normalize_language(language) == "ru" else "Disabled"


def reminders_enabled_text(language: str) -> str:
    return "Включены" if normalize_language(language) == "ru" else "Enabled"


def reminders_disabled_text(language: str) -> str:
    return "Выключены" if normalize_language(language) == "ru" else "Disabled"


def sound_enabled_text(language: str) -> str:
    return "Включены" if normalize_language(language) == "ru" else "Enabled"


def sound_disabled_text(language: str) -> str:
    return "Выключены" if normalize_language(language) == "ru" else "Disabled"


def daily_tip_status_icon(enabled: bool) -> str:
    return "💡" if enabled else "💤"


def reminders_status_icon(enabled: bool) -> str:
    return "⏰" if enabled else "⏸️"


def sound_status_icon(enabled: bool) -> str:
    return "🔔" if enabled else "🔕"


def daily_tip_label(language: str) -> str:
    return "Совет по грамматике" if normalize_language(language) == "ru" else "Grammar tip"


def reminders_label(language: str) -> str:
    return (
        "Напоминания о тренировке"
        if normalize_language(language) == "ru"
        else "Training reminders"
    )


def sound_label(language: str) -> str:
    return "Звуковые оповещения" if normalize_language(language) == "ru" else "Sound notifications"


def format_daily_tips_value(
    language: str,
    enabled: bool,
    time_value: str | None,
) -> str:
    if not enabled:
        return daily_tip_disabled_text(language)
    if time_value:
        return f"{daily_tip_enabled_text(language)} {time_value}"
    return daily_tip_enabled_text(language)


def format_training_reminders_value(
    language: str,
    enabled: bool,
    time_value: str | None,
) -> str:
    if not enabled:
        return reminders_disabled_text(language)
    if time_value:
        return f"{reminders_enabled_text(language)} {time_value}"
    return reminders_enabled_text(language)


def format_sound_value(language: str, enabled: bool) -> str:
    if enabled:
        return sound_enabled_text(language)
    return sound_disabled_text(language)


def format_daily_tips_summary_line(
    language: str,
    enabled: bool,
    time_value: str | None,
) -> str:
    value = format_daily_tips_value(language, enabled, time_value)
    return f"{daily_tip_status_icon(enabled)} {daily_tip_label(language)}: <b>{value}</b>"


def format_training_reminders_summary_line(
    language: str,
    enabled: bool,
    time_value: str | None,
) -> str:
    value = format_training_reminders_value(language, enabled, time_value)
    return f"{reminders_status_icon(enabled)} {reminders_label(language)}: <b>{value}</b>"


def format_sound_summary_line(language: str, enabled: bool) -> str:
    value = format_sound_value(language, enabled)
    return f"{sound_status_icon(enabled)} {sound_label(language)}: <b>{value}</b>"


def onboarding_language_screen(language: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            "👋 Добро пожаловать в Level 4 Trainer!\n\n"
            "✈️ Бот для подготовки к сдаче на уровень английского языка по системе SELCAL.\n\n"
            "⚙️ Перед началом давайте настроим бот — это не займёт много времени.\n\n"
            "🌍 Выберите язык интерфейса:"
        )
    return (
        "👋 Welcome to Level 4 Trainer!\n\n"
        "✈️ A bot for preparing for your English level check in SELCAL format.\n\n"
        "⚙️ Let’s set up the bot first — it will only take a moment.\n\n"
        "🌍 Choose your interface language:"
    )


def onboarding_timezone_screen(language: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            f"{interface_language_line(lang)}\n\n"
            "🕐 Часовой пояс\n\n"
            "Чтобы напоминания приходили в нужное время, укажите ваш часовой пояс."
        )
    return (
        f"{interface_language_line(lang)}\n\n"
        "🕐 Time zone\n\n"
        "To send reminders at the right time, please choose your time zone."
    )


def onboarding_timezone_auto_screen(language: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            f"{interface_language_line(lang)}\n\n"
            "📍 Отправьте геолокацию, чтобы бот автоматически определил ваш часовой пояс.\n\n"
            "Геолокация используется только для выбора часового пояса."
        )
    return (
        f"{interface_language_line(lang)}\n\n"
        "📍 Send your location so the bot can detect your time zone automatically.\n\n"
        "Your location is used only to set your time zone."
    )


def onboarding_timezone_manual_screen(language: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            f"{interface_language_line(lang)}\n\n"
            "🌍 Выберите ваш часовой пояс:"
        )
    return (
        f"{interface_language_line(lang)}\n\n"
        "🌍 Choose your time zone:"
    )


def onboarding_daily_tip_screen(language: str, timezone_value: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            f"{interface_language_line(lang)}\n"
            f"🌍 Часовой пояс: <b>{timezone_value}</b>\n\n"
            "💡 Хотите получать ежедневный совет по грамматике?"
        )
    return (
        f"{interface_language_line(lang)}\n"
        f"🌍 Time zone: <b>{timezone_value}</b>\n\n"
        "💡 Would you like to receive a daily grammar tip?"
    )


def onboarding_daily_tip_time_screen(language: str, timezone_value: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            f"{interface_language_line(lang)}\n"
            f"🌍 Часовой пояс: <b>{timezone_value}</b>\n"
            f"💡 Совет по грамматике: <b>{daily_tip_enabled_text(lang)}</b>\n\n"
            "🕒 Выберите время для ежедневного совета:"
        )
    return (
        f"{interface_language_line(lang)}\n"
        f"🌍 Time zone: <b>{timezone_value}</b>\n"
        f"💡 Grammar tip: <b>{daily_tip_enabled_text(lang)}</b>\n\n"
        "🕒 Choose the time for your daily tip:"
    )


def onboarding_daily_tip_custom_time_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🕒 Введите время сообщением в формате ЧЧ:ММ.\n\nНапример: 19:30"
    return "🕒 Send the time in HH:MM format.\n\nExample: 19:30"


def onboarding_reminders_screen(
    language: str,
    timezone_value: str,
    daily_tips_enabled: bool,
    daily_tip_time: str | None,
) -> str:
    lang = normalize_language(language)
    daily_tip_line = format_daily_tips_summary_line(
        lang,
        enabled=daily_tips_enabled,
        time_value=daily_tip_time,
    )
    if lang == "ru":
        return (
            f"{interface_language_line(lang)}\n"
            f"🌍 Часовой пояс: <b>{timezone_value}</b>\n"
            f"{daily_tip_line}\n\n"
            "⏰ Хотите получать напоминания о тренировке?\n\n"
            "Бот напомнит о практике, если вы долго не заходите."
        )
    return (
        f"{interface_language_line(lang)}\n"
        f"🌍 Time zone: <b>{timezone_value}</b>\n"
        f"{daily_tip_line}\n\n"
        "⏰ Would you like to receive training reminders?\n\n"
        "The bot will remind you to practise if you have been inactive for a while."
    )


def onboarding_reminders_time_screen(
    language: str,
    timezone_value: str,
    daily_tips_enabled: bool,
    daily_tip_time: str | None,
) -> str:
    lang = normalize_language(language)
    daily_tip_line = format_daily_tips_summary_line(
        lang,
        enabled=daily_tips_enabled,
        time_value=daily_tip_time,
    )
    reminders_line = format_training_reminders_summary_line(
        lang,
        enabled=True,
        time_value=None,
    )
    if lang == "ru":
        return (
            f"{interface_language_line(lang)}\n"
            f"🌍 Часовой пояс: <b>{timezone_value}</b>\n"
            f"{daily_tip_line}\n"
            f"{reminders_line}\n\n"
            "🕒 Выберите время для напоминаний:"
        )
    return (
        f"{interface_language_line(lang)}\n"
        f"🌍 Time zone: <b>{timezone_value}</b>\n"
        f"{daily_tip_line}\n"
        f"{reminders_line}\n\n"
        "🕒 Choose the time for reminders:"
    )


def onboarding_reminders_custom_time_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🕒 Введите время сообщением в формате ЧЧ:ММ.\n\nНапример: 19:30"
    return "🕒 Send the time in HH:MM format.\n\nExample: 19:30"


def onboarding_final_screen(
    language: str,
    timezone_value: str,
    daily_tips_enabled: bool,
    daily_tip_time: str | None,
    training_reminders_enabled: bool,
    training_reminder_time: str | None,
    sound_enabled: bool,
) -> str:
    lang = normalize_language(language)
    daily_tips_line = format_daily_tips_summary_line(
        lang,
        enabled=daily_tips_enabled,
        time_value=daily_tip_time,
    )
    reminders_line = format_training_reminders_summary_line(
        lang,
        enabled=training_reminders_enabled,
        time_value=training_reminder_time,
    )
    sound_line = format_sound_summary_line(lang, enabled=sound_enabled)

    if lang == "ru":
        return (
            "✅ Настройка завершена.\n\n"
            f"{interface_language_line(lang)}\n"
            f"🌍 Часовой пояс: <b>{timezone_value}</b>\n"
            f"{daily_tips_line}\n"
            f"{reminders_line}\n"
            f"{sound_line}\n\n"
            "⚙️ Настройки можно изменить в любое время!\n\n"
            "Всё готово — можно приступать к занятиям! ✈️"
        )

    return (
        "✅ Setup completed.\n\n"
        f"{interface_language_line(lang)}\n"
        f"🌍 Time zone: <b>{timezone_value}</b>\n"
        f"{daily_tips_line}\n"
        f"{reminders_line}\n"
        f"{sound_line}\n\n"
        "⚙️ Settings can be changed at any time!\n\n"
        "Everything is ready — let’s start training! ✈️"
    )


def toast_language_set(language: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return "✅ Язык установлен: 🇷🇺 Русский"
    return "✅ Language set: 🇬🇧 English"


def toast_default_settings_applied(language: str) -> str:
    if normalize_language(language) == "ru":
        return "✅ Быстрая настройка применена"
    return "✅ Quick setup applied"


def toast_timezone_set(language: str, timezone_value: str) -> str:
    if normalize_language(language) == "ru":
        return f"✅ Часовой пояс установлен: {timezone_value}"
    return f"✅ Time zone set: {timezone_value}"


def toast_daily_tips_disabled(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🚫 Советы дня выключены"
    return "🚫 Daily tips disabled"


def toast_daily_tips_enabled(language: str, time_value: str) -> str:
    if normalize_language(language) == "ru":
        return f"✅ Советы дня включены: {time_value}"
    return f"✅ Daily tips enabled: {time_value}"


def toast_reminders_disabled(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🚫 Напоминания выключены"
    return "🚫 Training reminders disabled"


def toast_reminders_enabled(language: str, time_value: str) -> str:
    if normalize_language(language) == "ru":
        return f"✅ Напоминания включены: {time_value}"
    return f"✅ Training reminders enabled: {time_value}"


def alert_timezone_detection_failed(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Не удалось определить часовой пояс. Выберите вручную."
    return "⚠️ Could not detect the time zone. Please choose it manually."


def alert_invalid_time(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Время нужно указать в формате ЧЧ:ММ.\n\nНапример: 19:30"
    return "⚠️ Time must be in HH:MM format.\n\nExample: 19:30"


def alert_state_not_found(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Профиль пользователя не найден. Нажмите /start еще раз."
    return "⚠️ User profile was not found. Please use /start again."


def alert_unknown_timezone_option(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Неизвестный вариант часового пояса."
    return "⚠️ Unknown time zone option."


def alert_unsupported_time_option(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Недопустимое значение времени."
    return "⚠️ Unsupported time value."


def location_keyboard_prompt(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📍 Отправьте геолокацию"
    return "📍 Use the button below to send your location."
