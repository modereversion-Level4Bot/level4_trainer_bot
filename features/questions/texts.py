"""Texts for questions feature."""

from __future__ import annotations

from typing import Literal


Language = Literal["ru", "en"]


def normalize_language(language: str | None) -> Language:
    if language == "ru":
        return "ru"
    return "en"


def main_menu_button_text(language: str) -> str:
    _ = language
    return "🏠"


def levels_button_text(language: str) -> str:
    return "🎙 Уровни" if normalize_language(language) == "ru" else "🎙 Levels"


def back_button_text(language: str) -> str:
    _ = language
    return "⬅️"


def level_button_text(level: int) -> str:
    return f"{level}️⃣ Level {level}"


def continue_button_text(language: str) -> str:
    return "▶️ Продолжить" if normalize_language(language) == "ru" else "▶️ Continue"


def start_over_button_text(language: str) -> str:
    return "🔄 Сначала" if normalize_language(language) == "ru" else "🔄 Start over"


def take_again_button_text(language: str) -> str:
    return "🔄 Заново" if normalize_language(language) == "ru" else "🔄 Take again"


def previous_button_text(language: str) -> str:
    _ = language
    return "⬅️"


def next_button_text(language: str) -> str:
    _ = language
    return "➡️"


def finish_button_text(language: str) -> str:
    return "✅ Завершить" if normalize_language(language) == "ru" else "✅ Finish"


def question_review_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📚 Разбор вопроса"
    return "📚 Question review"


def back_to_question_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🎧 К вопросу"
    return "🎧 To question"


def repeat_level_button_text(language: str, level: int) -> str:
    _ = level
    return "🔄 Заново" if normalize_language(language) == "ru" else "🔄 Take again"


def go_to_level5_button_text(language: str) -> str:
    _ = language
    return "5️⃣ Level 5"


def questions_levels_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🎙 <b>Вопросы</b>\n\n"
            "Выберите уровень для тренировки устной части экзамена.\n\n"
            "Вопросы нужно слушать, читать и отвечать на них вслух самостоятельно."
        )
    return (
        "🎙 <b>Questions</b>\n\n"
        "Choose a level to practise the speaking part of the exam.\n\n"
        "Listen to the questions, read them, and try to answer aloud by yourself."
    )


def questions_empty_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "🎙 <b>Вопросы</b>\n\n"
            "Раздел пока готовится.\n\n"
            "Скоро здесь появятся экзаменационные вопросы для тренировки устной части."
        )
    return (
        "🎙 <b>Questions</b>\n\n"
        "This section is being prepared.\n\n"
        "Exam questions for speaking practice will appear here soon."
    )


def continue_start_over_started_text(language: str, level: int) -> str:
    if normalize_language(language) == "ru":
        return (
            f"🎙 <b>Level {level}</b>\n\n"
            "Вы уже начали тренировку этого уровня.\n\n"
            "Хотите продолжить с текущего вопроса или начать сначала?"
        )
    return (
        f"🎙 <b>Level {level}</b>\n\n"
        "You have already started this level.\n\n"
        "Would you like to continue from your current question or start from the beginning?"
    )


def continue_start_over_completed_text(language: str, level: int) -> str:
    if normalize_language(language) == "ru":
        return (
            f"🎙 <b>Level {level}</b>\n\n"
            "Вы уже завершили этот уровень.\n\n"
            "Хотите пройти его заново?"
        )
    return (
        f"🎙 <b>Level {level}</b>\n\n"
        "You have already completed this level.\n\n"
        "Would you like to take it again?"
    )


def question_base_text(
    language: str,
    *,
    level: int,
    current: int,
    total: int,
    question_en: str,
) -> str:
    if normalize_language(language) == "ru":
        return (
            f"🎙 <b>Level {level} — Вопрос {current} из {total}</b>\n\n"
            "Прослушайте или прочитайте вопрос и попробуйте ответить вслух.\n\n"
            "<b>Вопрос:</b>\n"
            f"{question_en}"
        )
    return (
        f"🎙 <b>Level {level} — Question {current} of {total}</b>\n\n"
        "Listen to or read the question and try to answer aloud.\n\n"
        "<b>Question:</b>\n"
        f"{question_en}"
    )


def question_review_text(
    language: str,
    *,
    level: int,
    current: int,
    total: int,
    question_en: str,
    question_translation_ru: str,
    sample_answer_en: str,
    sample_answer_translation_ru: str,
) -> str:
    is_ru = normalize_language(language) == "ru"
    lines: list[str] = [
        (
            f"🎙 <b>Level {level} — Вопрос {current} из {total}</b>"
            if is_ru
            else f"🎙 <b>Level {level} — Question {current} of {total}</b>"
        ),
        "",
        "<b>Вопрос:</b>" if is_ru else "<b>Question:</b>",
        question_en,
    ]

    if is_ru and question_translation_ru:
        lines.extend(
            [
                "",
                "<b>Перевод вопроса:</b>",
                question_translation_ru,
            ]
        )

    if sample_answer_en:
        lines.extend(
            [
                "",
                "<b>Пример ответа:</b>" if is_ru else "<b>Sample answer:</b>",
                sample_answer_en,
            ]
        )

    if is_ru and sample_answer_translation_ru:
        lines.extend(
            [
                "",
                "<b>Перевод ответа:</b>",
                sample_answer_translation_ru,
            ]
        )

    return "\n".join(lines)


def level4_completion_text(language: str, *, has_level5: bool) -> str:
    if normalize_language(language) == "ru":
        if has_level5:
            return (
                "✅ <b>Level 4 завершён</b>\n\n"
                "Вы прошли все доступные вопросы Level 4.\n\n"
                "Можно повторить уровень, вернуться к списку уровней или перейти к Level 5."
            )
        return (
            "✅ <b>Level 4 завершён</b>\n\n"
            "Вы прошли все доступные вопросы Level 4.\n\n"
            "Можно повторить уровень или вернуться к списку уровней."
        )
    if has_level5:
        return (
            "✅ <b>Level 4 completed</b>\n\n"
            "You have completed all available Level 4 questions.\n\n"
            "You can repeat this level, return to the level list, or continue to Level 5."
        )
    return (
        "✅ <b>Level 4 completed</b>\n\n"
        "You have completed all available Level 4 questions.\n\n"
        "You can repeat this level or return to the level list."
    )


def level5_completion_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "✅ <b>Level 5 завершён</b>\n\n"
            "Вы прошли все доступные вопросы Level 5.\n\n"
            "Можно повторить уровень или вернуться к списку уровней."
        )
    return (
        "✅ <b>Level 5 completed</b>\n\n"
        "You have completed all available Level 5 questions.\n\n"
        "You can repeat this level or return to the level list."
    )


def level_unavailable_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Материал обновился. Этот уровень сейчас недоступен."
    return "The content has been updated. This level is currently unavailable."


def question_unavailable_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Материал обновился. Открою список уровней."
    return "The content has been updated. I’ll open the level list."
