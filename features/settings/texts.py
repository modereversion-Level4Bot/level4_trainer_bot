"""Texts for settings feature."""

from __future__ import annotations

from typing import Literal


Language = Literal["ru", "en"]
ResetTarget = Literal["grammar", "questions", "routes", "all"]


def normalize_language(language: str | None) -> Language:
    if language == "ru":
        return "ru"
    return "en"


def interface_language_name(language: str | None) -> str:
    return "Русский" if normalize_language(language) == "ru" else "English"


def interface_language_flag(language: str | None) -> str:
    return "🇷🇺" if normalize_language(language) == "ru" else "🇬🇧"


def _daily_tip_icon(enabled: bool) -> str:
    return "💡" if enabled else "💤"


def _reminders_icon(enabled: bool) -> str:
    return "⏰" if enabled else "⏸️"


def _sound_icon(enabled: bool) -> str:
    return "🔔" if enabled else "🔕"


def _daily_tip_value(language: str, enabled: bool, time_value: str | None) -> str:
    lang = normalize_language(language)
    if not enabled:
        return "Выключен" if lang == "ru" else "Disabled"
    base = "Включён" if lang == "ru" else "Enabled"
    if time_value:
        return f"{base} {time_value}"
    return base


def _reminders_value(language: str, enabled: bool, time_value: str | None) -> str:
    lang = normalize_language(language)
    if not enabled:
        return "Выключены" if lang == "ru" else "Disabled"
    base = "Включены" if lang == "ru" else "Enabled"
    if time_value:
        return f"{base} {time_value}"
    return base


def _sound_value(language: str, enabled: bool) -> str:
    if normalize_language(language) == "ru":
        return "Включены" if enabled else "Выключены"
    return "Enabled" if enabled else "Disabled"


def settings_main_screen(
    language: str,
    *,
    timezone_value: str,
    daily_tips_enabled: bool,
    daily_tip_time: str | None,
    training_reminders_enabled: bool,
    training_reminder_time: str | None,
    sound_enabled: bool,
) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            "⚙️ <b>Настройки</b>\n\n"
            f"{interface_language_flag(lang)} Язык интерфейса: <b>{interface_language_name(lang)}</b>\n"
            f"🌍 Часовой пояс: <b>{timezone_value}</b>\n"
            f"{_daily_tip_icon(daily_tips_enabled)} Совет по грамматике: <b>{_daily_tip_value(lang, daily_tips_enabled, daily_tip_time)}</b>\n"
            f"{_reminders_icon(training_reminders_enabled)} Напоминания о тренировке: <b>{_reminders_value(lang, training_reminders_enabled, training_reminder_time)}</b>\n"
            f"{_sound_icon(sound_enabled)} Звуковые оповещения: <b>{_sound_value(lang, sound_enabled)}</b>\n\n"
            "Выберите, что хотите изменить:"
        )
    return (
        "⚙️ <b>Settings</b>\n\n"
        f"{interface_language_flag(lang)} Interface language: <b>{interface_language_name(lang)}</b>\n"
        f"🌍 Time zone: <b>{timezone_value}</b>\n"
        f"{_daily_tip_icon(daily_tips_enabled)} Grammar tip: <b>{_daily_tip_value(lang, daily_tips_enabled, daily_tip_time)}</b>\n"
        f"{_reminders_icon(training_reminders_enabled)} Training reminders: <b>{_reminders_value(lang, training_reminders_enabled, training_reminder_time)}</b>\n"
        f"{_sound_icon(sound_enabled)} Sound notifications: <b>{_sound_value(lang, sound_enabled)}</b>\n\n"
        "Choose what you want to change:"
    )


def settings_language_screen(language: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            "🌐 <b>Язык интерфейса</b>\n\n"
            "Текущий язык: <b>Русский</b>\n\n"
            "Выберите язык:"
        )
    return (
        "🌐 <b>Interface language</b>\n\n"
        "Current language: <b>English</b>\n\n"
        "Choose language:"
    )


def settings_timezone_screen(language: str, timezone_value: str) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        return (
            "🌍 <b>Часовой пояс</b>\n\n"
            f"Текущий часовой пояс: <b>{timezone_value}</b>\n\n"
            "Чтобы напоминания приходили в нужное время, укажите ваш часовой пояс."
        )
    return (
        "🌍 <b>Time zone</b>\n\n"
        f"Current time zone: <b>{timezone_value}</b>\n\n"
        "To send reminders at the right time, please choose your time zone."
    )


def settings_timezone_auto_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🌍 <b>Часовой пояс</b>\n\n"
            "📍 Отправьте геолокацию, чтобы бот автоматически определил ваш часовой пояс.\n\n"
            "Геолокация используется только для выбора часового пояса."
        )
    return (
        "🌍 <b>Time zone</b>\n\n"
        "📍 Send your location so the bot can detect your time zone automatically.\n\n"
        "Your location is used only to set your time zone."
    )


def settings_timezone_manual_screen(language: str, warning_text: str | None = None) -> str:
    lang = normalize_language(language)
    base = (
        "🌍 <b>Выберите ваш часовой пояс</b>"
        if lang == "ru"
        else "🌍 <b>Choose your time zone</b>"
    )
    if warning_text:
        return f"{warning_text}\n\n{base}"
    return base


def settings_daily_tip_screen(language: str, enabled: bool, time_value: str | None) -> str:
    lang = normalize_language(language)
    status = _daily_tip_value(lang, enabled, time_value)
    if lang == "ru":
        title = "💡 <b>Совет по грамматике</b>" if enabled else "💤 <b>Совет по грамматике</b>"
        return (
            f"{title}\n\n"
            f"Текущий статус: <b>{status}</b>\n\n"
            "Ежедневный совет помогает коротко повторять грамматику."
        )
    title = "💡 <b>Grammar tip</b>" if enabled else "💤 <b>Grammar tip</b>"
    return (
        f"{title}\n\n"
        f"Current status: <b>{status}</b>\n\n"
        "A daily tip helps you review grammar in short sessions."
    )


def settings_daily_tip_time_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🕒 <b>Время совета по грамматике</b>\n\n"
            "Выберите время для ежедневного совета:"
        )
    return (
        "🕒 <b>Daily tip time</b>\n\n"
        "Choose the time for your daily tip:"
    )


def settings_daily_tip_custom_time_screen(language: str, warning_text: str | None = None) -> str:
    if normalize_language(language) == "ru":
        base = "🕒 Введите время сообщением в формате ЧЧ:ММ.\n\nНапример: 19:30"
    else:
        base = "🕒 Send the time in HH:MM format.\n\nExample: 19:30"
    if warning_text:
        return f"{warning_text}\n\n{base}"
    return base


def settings_reminders_screen(language: str, enabled: bool, time_value: str | None) -> str:
    lang = normalize_language(language)
    status = _reminders_value(lang, enabled, time_value)
    if lang == "ru":
        title = (
            "⏰ <b>Напоминания о тренировке</b>"
            if enabled
            else "⏸️ <b>Напоминания о тренировке</b>"
        )
        return (
            f"{title}\n\n"
            f"Текущий статус: <b>{status}</b>\n\n"
            "Бот напомнит о практике, если вы долго не заходите."
        )
    title = "⏰ <b>Training reminders</b>" if enabled else "⏸️ <b>Training reminders</b>"
    return (
        f"{title}\n\n"
        f"Current status: <b>{status}</b>\n\n"
        "The bot will remind you to practise if you have been inactive for a while."
    )


def settings_reminders_time_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🕒 <b>Время напоминаний</b>\n\n"
            "Выберите время для напоминаний:"
        )
    return (
        "🕒 <b>Reminder time</b>\n\n"
        "Choose the time for reminders:"
    )


def settings_reminders_custom_time_screen(language: str, warning_text: str | None = None) -> str:
    if normalize_language(language) == "ru":
        base = "🕒 Введите время сообщением в формате ЧЧ:ММ.\n\nНапример: 19:30"
    else:
        base = "🕒 Send the time in HH:MM format.\n\nExample: 19:30"
    if warning_text:
        return f"{warning_text}\n\n{base}"
    return base


def settings_sound_screen(language: str, enabled: bool) -> str:
    lang = normalize_language(language)
    title = "🔔 <b>Звуковые оповещения</b>" if enabled and lang == "ru" else (
        "🔕 <b>Звуковые оповещения</b>" if lang == "ru" else (
            "🔔 <b>Sound notifications</b>" if enabled else "🔕 <b>Sound notifications</b>"
        )
    )
    if lang == "ru":
        return (
            f"{title}\n\n"
            f"Текущий статус: <b>{_sound_value(lang, enabled)}</b>\n\n"
            "Если звук включен, советы дня и напоминания приходят со звуком.\n"
            "Если выключен — они приходят тихо."
        )
    return (
        f"{title}\n\n"
        f"Current status: <b>{_sound_value(lang, enabled)}</b>\n\n"
        "If sound is enabled, daily tips and reminders arrive with sound.\n"
        "If disabled, they arrive silently."
    )


def settings_reset_progress_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "♻️ <b>Сбросить прогресс</b>\n\n"
            "Что хотите сбросить?"
        )
    return (
        "♻️ <b>Reset progress</b>\n\n"
        "What do you want to reset?"
    )


def reset_target_label(language: str, target: ResetTarget) -> str:
    lang = normalize_language(language)
    labels_ru = {
        "grammar": "📘 Грамматика",
        "questions": "🎙 Вопросы",
        "routes": "🛫 Маршруты",
        "all": "⚠️ Весь прогресс",
    }
    labels_en = {
        "grammar": "📘 Grammar",
        "questions": "🎙 Questions",
        "routes": "🛫 Routes",
        "all": "⚠️ All progress",
    }
    return labels_ru[target] if lang == "ru" else labels_en[target]


def settings_reset_confirm_screen(language: str, target: ResetTarget) -> str:
    lang = normalize_language(language)
    if target == "all":
        if lang == "ru":
            return (
                "⚠️ <b>Подтвердите сброс</b>\n\n"
                "Будет удалён весь учебный прогресс:\n"
                "• грамматика\n"
                "• вопросы\n"
                "• маршруты\n\n"
                "Настройки бота сохранятся.\n\n"
                "Это действие нельзя отменить."
            )
        return (
            "⚠️ <b>Confirm reset</b>\n\n"
            "All learning progress will be deleted:\n"
            "• grammar\n"
            "• questions\n"
            "• routes\n\n"
            "Bot settings will be preserved.\n\n"
            "This action cannot be undone."
        )

    if lang == "ru":
        return (
            "⚠️ <b>Подтвердите сброс</b>\n\n"
            "Будет удалён прогресс раздела:\n"
            f"{reset_target_label(lang, target)}\n\n"
            "Это действие нельзя отменить."
        )
    return (
        "⚠️ <b>Confirm reset</b>\n\n"
        "Progress will be deleted for:\n"
        f"{reset_target_label(lang, target)}\n\n"
        "This action cannot be undone."
    )


def settings_restart_onboarding_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🔄 <b>Перезапустить онбординг</b>\n\n"
            "Вы заново пройдёте начальную настройку:\n\n"
            "• язык интерфейса\n"
            "• часовой пояс\n"
            "• советы по грамматике\n"
            "• напоминания\n\n"
            "Учебный прогресс сохранится."
        )
    return (
        "🔄 <b>Restart onboarding</b>\n\n"
        "You will go through the initial setup again:\n\n"
        "• interface language\n"
        "• time zone\n"
        "• grammar tips\n"
        "• reminders\n\n"
        "Learning progress will be preserved."
    )


def settings_delete_account_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🗑 <b>Удалить аккаунт</b>\n\n"
            "Будут удалены:\n\n"
            "• ваши настройки\n"
            "• ваш прогресс\n"
            "• история активности\n"
            "• данные аккаунта в боте\n\n"
            "Это действие нельзя отменить."
        )
    return (
        "🗑 <b>Delete account</b>\n\n"
        "The following data will be deleted:\n\n"
        "• your settings\n"
        "• your progress\n"
        "• activity history\n"
        "• bot account data\n\n"
        "This action cannot be undone."
    )


def settings_delete_account_confirm_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "⚠️ <b>Подтвердите удаление аккаунта</b>\n\n"
            "Если вы удалите аккаунт, бот забудет ваши настройки и прогресс.\n\n"
            "Для повторного использования нужно будет пройти онбординг заново."
        )
    return (
        "⚠️ <b>Confirm account deletion</b>\n\n"
        "If you delete your account, the bot will forget your settings and progress.\n\n"
        "To use the bot again, you will need to complete onboarding again."
    )


def settings_account_deleted_screen(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "✅ <b>Аккаунт удалён</b>\n\n"
            "Ваши данные в боте удалены.\n\n"
            "Чтобы начать заново, отправьте /start."
        )
    return (
        "✅ <b>Account deleted</b>\n\n"
        "Your bot data has been deleted.\n\n"
        "To start again, send /start."
    )


def toast_language_set(selected_language: str) -> str:
    if normalize_language(selected_language) == "ru":
        return "✅ Язык установлен: Русский"
    return "✅ Language set: English"


def toast_timezone_set(language: str, timezone_value: str) -> str:
    if normalize_language(language) == "ru":
        return f"✅ Часовой пояс установлен: {timezone_value}"
    return f"✅ Time zone set: {timezone_value}"


def toast_daily_tips_enabled(language: str, time_value: str) -> str:
    if normalize_language(language) == "ru":
        return f"✅ Советы дня включены: {time_value}"
    return f"✅ Daily tips enabled: {time_value}"


def toast_daily_tips_disabled(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🚫 Советы дня выключены"
    return "🚫 Daily tips disabled"


def toast_reminders_enabled(language: str, time_value: str) -> str:
    if normalize_language(language) == "ru":
        return f"✅ Напоминания включены: {time_value}"
    return f"✅ Training reminders enabled: {time_value}"


def toast_reminders_disabled(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🚫 Напоминания выключены"
    return "🚫 Training reminders disabled"


def toast_sound_enabled(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🔔 Звуковые оповещения включены"
    return "🔔 Sound notifications enabled"


def toast_sound_disabled(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🔕 Звуковые оповещения выключены"
    return "🔕 Sound notifications disabled"


def toast_progress_reset(language: str) -> str:
    if normalize_language(language) == "ru":
        return "✅ Прогресс сброшен"
    return "✅ Progress reset"


def warning_timezone_detection_failed(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Не удалось определить часовой пояс. Выберите его вручную."
    return "⚠️ Could not detect the time zone. Please choose it manually."


def warning_invalid_time(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Время нужно указать в формате ЧЧ:ММ.\n\nНапример: 19:30"
    return "⚠️ Time must be in HH:MM format.\n\nExample: 19:30"


def alert_unknown_timezone_option(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Неизвестный вариант часового пояса."
    return "⚠️ Unknown time zone option."


def alert_unsupported_time_option(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Недопустимое значение времени."
    return "⚠️ Unsupported time value."


def alert_admin_delete_forbidden(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Администраторский аккаунт нельзя удалить через настройки."
    return "⚠️ An administrator account cannot be deleted from settings."


def location_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📍 Отправить геолокацию"
    return "📍 Send location"


def main_menu_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🏠 Главное меню"
    return "🏠 Main menu"


def management_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🛠 Управление"
    return "🛠 Management"


def settings_main_section_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🧭 Основные"
    return "🧭 Main"


def settings_notifications_section_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🔔 Уведомления"
    return "🔔 Notifications"


def settings_account_section_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "👤 Аккаунт"
    return "👤 Account"


def interface_language_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🌐 Язык интерфейса"
    return "🌐 Interface language"


def timezone_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🌍 Часовой пояс"
    return "🌍 Time zone"


def timezone_auto_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📍 Автоматически"
    return "📍 Automatically"


def timezone_manual_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🕒 Вручную"
    return "🕒 Manually"


def notification_sounds_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🔊 Звуки уведомлений"
    return "🔊 Notification sounds"


def daily_grammar_tip_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "💡 Совет дня по грамматике"
    return "💡 Daily grammar tip"


def training_reminders_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⏰ Напоминания о тренировках"
    return "⏰ Training reminders"


def progress_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "♻️ Прогресс"
    return "♻️ Progress"


def restart_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🔄 Перезапуск"
    return "🔄 Restart"


def delete_account_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🗑 Удалить аккаунт"
    return "🗑 Delete account"


def settings_state_not_found_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Профиль пользователя не найден. Нажмите /start еще раз."
    return "⚠️ User profile was not found. Please use /start again."


def management_todo_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Раздел будет реализован в следующих задачах."
    return "This section will be implemented in future tasks."
