"""Texts for main menu feature."""

from __future__ import annotations

from typing import Literal

from features.main_menu.context import MainMenuContext


Language = Literal["ru", "en"]


def normalize_language(language: str | None) -> Language:
    if language == "ru":
        return "ru"
    return "en"


def main_menu_text(language: str, context: MainMenuContext) -> str:
    """Build localized main menu text."""
    lang = normalize_language(language)

    if lang == "ru":
        _ = context
        return (
            "📱 <b>Level 4 Trainer</b>\n\n"
            "Интерактивный тренажёр для подготовки пилотов к экзамену по английскому языку SELCAL.\n\n"
            "<b>Выберите раздел для изучения:</b>"
        )

    _ = context
    return (
        "📱 <b>Level 4 Trainer</b>\n\n"
        "An interactive trainer for pilots preparing for the SELCAL English language exam.\n\n"
        "<b>Choose a section to study:</b>"
    )


def grammar_button_text(language: str) -> str:
    return "📘 Грамматика" if normalize_language(language) == "ru" else "📘 Grammar"


def questions_button_text(language: str) -> str:
    return "🎙 Вопросы" if normalize_language(language) == "ru" else "🎙 Questions"


def routes_button_text(language: str) -> str:
    return "🛫 Маршруты" if normalize_language(language) == "ru" else "🛫 Routes"


def exam_info_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "ℹ️ Как проходит экзамен"
    return "ℹ️ How the exam works"


def settings_button_text(language: str) -> str:
    return "⚙️ Настройки" if normalize_language(language) == "ru" else "⚙️ Settings"


def todo_section_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Раздел будет реализован в следующих задачах."
    return "This section will be implemented in future tasks."
