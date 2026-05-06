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
        text = (
            "📘 <b>Грамматика</b>\n\n"
            "Короткие и понятные темы, которые помогут увереннее отвечать на экзаменационные вопросы.\n\n"
            f"📈 Прогресс <b>{completed} из {total}</b>\n"
        )
        if total_pages > 1:
            text += f"\n📄 Страница <b>{page} из {total_pages}</b>\n"
        text += "\nВыберите тему:"
        return text

    text = (
        "📘 <b>Grammar</b>\n\n"
        "Short and clear grammar topics to help you answer exam questions more confidently.\n\n"
        f"📈 Progress <b>{completed} of {total}</b>\n"
    )
    if total_pages > 1:
        text += f"\n📄 Page <b>{page} of {total_pages}</b>\n"
    text += "\nChoose a topic:"
    return text


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
        text = (
            "📎 <b>Дополнительные материалы</b>\n\n"
            "Эти темы помогут повторить полезные правила, но не входят в основной прогресс грамматики.\n"
        )
        if total_pages > 1:
            text += f"\n📄 Страница <b>{page} из {total_pages}</b>\n"
        text += "\nВыберите тему:"
        return text

    text = (
        "📎 <b>Additional materials</b>\n\n"
        "These topics help you review useful rules, but they are not included in the main grammar progress.\n"
    )
    if total_pages > 1:
        text += f"\n📄 Page <b>{page} of {total_pages}</b>\n"
    text += "\nChoose a topic:"
    return text


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
        return "📎 Дополнительно"
    return "📎 Additional"


def back_button_text(language: str) -> str:
    _ = language
    return "◀️"


def pagination_next_button_text(language: str) -> str:
    _ = language
    return "▶️"


def to_grammar_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⬅️ К грамматике"
    return "⬅️ To Grammar"


def topic_list_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📁 Темы"
    return "📁 Topics"


def back_to_topic_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⬅️ К теме"
    return "⬅️ To topic"


def previous_topic_button_text(language: str) -> str:
    _ = language
    return "⬅️"


def next_topic_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Следующая ➡️"
    return "Next ➡️"


def main_menu_button_text(language: str) -> str:
    _ = language
    return "🏠"


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
            "Результат:\n\n"
            f"✅ Правильных ответов: <b>{correct}</b>\n"
            f"❌ Ошибок: <b>{wrong}</b>"
        )
        if mark_applied:
            text += "\n\nТема отмечена как изученная."
        return text

    text = (
        "🎉 <b>Excellent!</b>\n\n"
        "You have mastered the material perfectly.\n\n"
        "Result:\n\n"
        f"✅ Correct answers: <b>{correct}</b>\n"
        f"❌ Mistakes: <b>{wrong}</b>"
    )
    if mark_applied:
        text += "\n\nThe topic has been marked as studied."
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
            "Результат:\n\n"
            f"✅ Правильных ответов: <b>{correct}</b>\n"
            f"❌ Ошибок: <b>{wrong}</b>"
        )
        if mark_applied:
            text += "\n\nТема отмечена как изученная."
        return text

    text = (
        "✅ <b>Good result</b>\n\n"
        "You can repeat the training or continue with other topics.\n\n"
        "Result:\n\n"
        f"✅ Correct answers: <b>{correct}</b>\n"
        f"❌ Mistakes: <b>{wrong}</b>"
    )
    if mark_applied:
        text += "\n\nThe topic has been marked as studied."
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
            "Результат:\n\n"
            f"✅ Правильных ответов: <b>{correct}</b>\n"
            f"❌ Ошибок: <b>{wrong}</b>"
        )
    return (
        "📘 <b>It is better to review the material</b>\n\n"
        "There were quite a few mistakes. It is better to return to the topic and repeat the training.\n\n"
        "Result:\n\n"
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
        return "📁 Темы"
    return "📁 Topics"
