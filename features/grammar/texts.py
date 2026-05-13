"""Texts for grammar feature."""

from __future__ import annotations

from typing import Literal


Language = Literal["ru", "en"]


def normalize_language(language: str | None) -> Language:
    if language == "ru":
        return "ru"
    return "en"


def grammar_list_text(
    language: str,
    *,
    completed: int,
    total: int,
    page: int = 1,
    total_pages: int = 1,
) -> str:
    if normalize_language(language) == "ru":
        return (
            "📘 <b>Грамматика</b>\n\n"
            "Основные темы и тренировки к ним, которые помогают освоить и закрепить базовые грамматические навыки.\n\n"
            f"📈 Изучено <b>{completed}</b> из <b>{total}</b>\n\n"
            "<b>Выберите тему для изучения:</b>"
        )

    return (
        "📘 <b>Grammar</b>\n\n"
        "Core topics and related exercises that help you build and reinforce essential grammar skills.\n\n"
        f"📈 Studied <b>{completed}</b> of <b>{total}</b>\n\n"
        "<b>Choose a topic to study:</b>"
    )


def grammar_no_topics_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "📘 <b>Грамматика</b>\n\n"
            "Пока нет доступных тем грамматики."
        )
    return (
        "📘 <b>Grammar</b>\n\n"
        "No grammar topics are available yet."
    )


def extra_materials_text(
    language: str,
    *,
    page: int = 1,
    total_pages: int = 1,
) -> str:
    if normalize_language(language) == "ru":
        return (
            "📎 <b>Дополнительные материалы</b>\n\n"
            "Дополнительные темы и тренировки к ним, которые помогают освоить и закрепить базовые грамматические навыки.\n\n"
            "<b>Выберите тему для изучения:</b>"
        )

    return (
        "📎 <b>Additional materials</b>\n\n"
        "Additional topics and related exercises that help you build and reinforce essential grammar skills.\n\n"
        "<b>Choose a topic to study:</b>"
    )


def topic_text(language: str, *, title: str, simple_explanation: str) -> str:
    return f"📕 <b>{title}</b>\n\n{simple_explanation}"


def details_text(language: str, *, title: str, detailed_explanation: str) -> str:
    _ = language
    return f"📖 <b>{title}</b>\n\n{detailed_explanation}"


def missing_topic_description_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Описание темы пока не добавлено."
    return "Topic description has not been added yet."


def details_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📖 Подробнее"
    return "📖 Details"


def start_training_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🎯 Тренировка"
    return "🎯 Training"


def extra_materials_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📎 Дополнительные материалы"
    return "📎 Additional materials"


def back_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "◀️ Назад"
    return "◀️ Back"


def pagination_next_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Дальше ▶️"
    return "Next ▶️"


def to_grammar_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📘 Назад в грамматику"
    return "📘 Back to Grammar"


def topic_list_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📂 К списку тем"
    return "📂 Topic list"


def back_to_topic_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⤵️ Назад к теме"
    return "⤵️ Back to topic"


def previous_topic_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "◀️ Предыдущая"
    return "◀️ Previous"


def next_topic_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Следующая ▶️"
    return "Next ▶️"


def main_menu_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🏠 В главное меню"
    return "🏠 Main menu"


def unavailable_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Материал недоступен."
    return "Material is unavailable."


def training_no_questions_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Для этой темы пока нет вопросов."
    return "There are no questions for this topic yet."


def training_session_expired_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Тренировка устарела. Начните её заново."
    return "The training session has expired. Please start it again."


def training_question_unavailable_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Вопрос недоступен."
    return "Question is unavailable."


def training_question_text(
    language: str,
    *,
    topic_title: str,
    question_index: int,
    total_questions: int,
    question_text: str,
) -> str:
    if normalize_language(language) == "ru":
        return (
            f"🎯 <b>Тренировка: {topic_title}</b>\n\n"
            f"Вопрос <b>{question_index} из {total_questions}</b>\n\n"
            f"{question_text}\n\n"
            "Выберите правильный ответ:"
        )

    return (
        f"🎯 <b>Training: {topic_title}</b>\n\n"
        f"Question <b>{question_index} of {total_questions}</b>\n\n"
        f"{question_text}\n\n"
        "Choose the correct answer:"
    )


def training_correct_popup_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "✅ Правильно!"
    return "✅ Correct!"


def training_incorrect_popup_text(language: str, explanation: str | None) -> str:
    cleaned_explanation = (explanation or "").strip()
    if normalize_language(language) == "ru":
        if not cleaned_explanation:
            return "❌ Неверно!"
        return f"❌ Неверно!\n\n{cleaned_explanation}"
    if not cleaned_explanation:
        return "❌ Incorrect!"
    return f"❌ Incorrect!\n\n{cleaned_explanation}"


def training_result_excellent_text(
    language: str,
    *,
    correct: int,
    wrong: int,
    total: int,
    mark_applied: bool,
) -> str:
    _ = total
    if normalize_language(language) == "ru":
        text = (
            "🎉 <b>Превосходно!</b>\n\n"
            "Вы безупречно освоили материал.\n\n"
            f"✅ Правильных ответов: <b>{correct}</b>\n"
            f"❌ Ошибок: <b>{wrong}</b>"
        )
        if mark_applied:
            text += "\n\nТема добавлена в прогресс"
        return text

    text = (
        "🎉 <b>Excellent!</b>\n\n"
        "You have mastered the material perfectly.\n\n"
        f"✅ Correct answers: <b>{correct}</b>\n"
        f"❌ Mistakes: <b>{wrong}</b>"
    )
    if mark_applied:
        text += "\n\nTopic added to progress"
    return text


def training_result_good_text(
    language: str,
    *,
    correct: int,
    wrong: int,
    total: int,
    mark_applied: bool,
) -> str:
    _ = total
    if normalize_language(language) == "ru":
        text = (
            "✅ <b>Хороший результат</b>\n\n"
            "Можно повторить тренировку или перейти к другим темам.\n\n"
            f"✅ Правильных ответов: <b>{correct}</b>\n"
            f"❌ Ошибок: <b>{wrong}</b>"
        )
        if mark_applied:
            text += "\n\nТема добавлена в прогресс"
        return text

    text = (
        "✅ <b>Good result</b>\n\n"
        "You can repeat the training or continue with other topics.\n\n"
        f"✅ Correct answers: <b>{correct}</b>\n"
        f"❌ Mistakes: <b>{wrong}</b>"
    )
    if mark_applied:
        text += "\n\nTopic added to progress"
    return text


def training_result_weak_text(
    language: str,
    *,
    correct: int,
    wrong: int,
    total: int,
) -> str:
    _ = total
    if normalize_language(language) == "ru":
        return (
            "📘 <b>Стоит повторить материал</b>\n\n"
            "Ошибок получилось многовато. Лучше ещё раз вернуться к теме и пройти тренировку повторно.\n\n"
            f"✅ Правильных ответов: <b>{correct}</b>\n"
            f"❌ Ошибок: <b>{wrong}</b>"
        )
    return (
        "📘 <b>It is better to review the material</b>\n\n"
        "There were quite a few mistakes. It is better to return to the topic and repeat the training.\n\n"
        f"✅ Correct answers: <b>{correct}</b>\n"
        f"❌ Mistakes: <b>{wrong}</b>"
    )


def training_topic_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⬅️ К теме"
    return "⬅️ To topic"


def repeat_training_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🔂 Повторить"
    return "🔂 Repeat"


def review_topic_again_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📕 Изучить"
    return "📕 Review"


def training_topic_list_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📂 К списку тем"
    return "📂 Topic list"
