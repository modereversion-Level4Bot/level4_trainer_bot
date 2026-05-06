"""Texts for main menu feature."""

from __future__ import annotations

from typing import Literal

from features.main_menu.context import MainMenuContext


Language = Literal["ru", "en"]


def normalize_language(language: str | None) -> Language:
    if language == "ru":
        return "ru"
    return "en"


def _normalize_version(bot_version: str) -> str:
    normalized = (bot_version or "").strip()
    if not normalized:
        return "0.0"
    if normalized.lower().startswith("v"):
        normalized = normalized[1:].strip()
    return normalized or "0.0"


def main_menu_text(language: str, context: MainMenuContext) -> str:
    """Build localized main menu text."""
    lang = normalize_language(language)
    version = _normalize_version(context.bot_version)

    if lang == "ru":
        text = (
            "✈️ Level 4 Trainer\n\n"
            "Тренажёр ICAO English для пилотов.\n\n"
            "Грамматика, экзаменационные вопросы и маршруты в формате пилот-диспетчер\n\n"
            "Ваш текущий прогресс:\n\n"
            f"📘 Грамматика — изучено {context.grammar_completed} из {context.grammar_total}\n"
            f"🎙 Вопросы — пройдено {context.questions_completed} из {context.questions_total}\n"
            f"🛫 Маршруты — пройдено {context.routes_completed} из {context.routes_total}\n"
        )
        if context.is_admin:
            text += f"\n🟢 Работает\n🎮 v {version}\n"
        text += "\nВыберите раздел для тренировки:"
        return text

    text = (
        "✈️ Level 4 Trainer\n\n"
        "ICAO English trainer for pilots.\n\n"
        "Grammar, exam questions, and pilot-controller routes.\n\n"
        "Your current progress:\n\n"
        f"📘 Grammar — studied {context.grammar_completed} of {context.grammar_total}\n"
        f"🎙 Questions — completed {context.questions_completed} of {context.questions_total}\n"
        f"🛫 Routes — completed {context.routes_completed} of {context.routes_total}\n"
    )
    if context.is_admin:
        text += f"\n🟢 Running\n🎮 v {version}\n"
    text += "\nChoose a section to train:"
    return text


def grammar_button_text(language: str) -> str:
    return "📘 Грамматика" if normalize_language(language) == "ru" else "📘 Grammar"


def questions_button_text(language: str) -> str:
    return "🎙 Вопросы" if normalize_language(language) == "ru" else "🎙 Questions"


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
