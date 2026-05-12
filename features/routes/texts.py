"""Texts for routes feature."""

from __future__ import annotations

from typing import Literal


Language = Literal["ru", "en"]


def normalize_language(language: str | None) -> Language:
    if language == "ru":
        return "ru"
    return "en"


def routes_list_title(language: str) -> str:
    return "🛫 Маршруты" if normalize_language(language) == "ru" else "🛫 Routes"


def routes_list_description(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Тренировка радиообмена в формате pilot-controller."
    return "Pilot-controller communication practice."


def routes_progress_line(language: str, *, completed: int, total: int) -> str:
    if normalize_language(language) == "ru":
        return f"📈 Прогресс: пройдено {completed} из {total}"
    return f"📈 Progress: completed {completed} of {total}"


def routes_page_line(language: str, *, page: int, total_pages: int) -> str:
    if normalize_language(language) == "ru":
        return f"📄 Страница {page} из {total_pages}"
    return f"📄 Page {page} of {total_pages}"


def routes_choose_line(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Выберите маршрут:"
    return "Choose a route:"


def routes_list_text(
    language: str,
    *,
    completed: int,
    total: int,
    page: int,
    total_pages: int,
) -> str:
    return (
        f"{routes_list_title(language)}\n\n"
        f"{routes_list_description(language)}\n\n"
        f"{routes_progress_line(language, completed=completed, total=total)}\n"
        f"{routes_page_line(language, page=page, total_pages=total_pages)}\n\n"
        f"{routes_choose_line(language)}"
    )


def routes_empty_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🛫 Маршруты пока недоступны."
    return "🛫 Routes are not available yet."


def route_briefing_text(language: str, *, briefing_text: str) -> str:
    return f"🛫 Briefing\n\n{briefing_text}"


def stale_routes_navigation_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Маршрут или страница устарели. Открываю актуальный список."
    return "Route or page is stale. Opening the current routes list."


def route_scenario_placeholder_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Сценарий маршрута будет доступен на следующем этапе."
    return "Route scenario will be available in the next phase."


def route_news_placeholder_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Новости маршрута будут доступны на следующем этапе."
    return "Route news will be available in the next phase."


def route_questions_placeholder_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Вопросы по маршруту будут доступны на следующем этапе."
    return "Route questions will be available in the next phase."


def route_no_news_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "В этом маршруте пока нет новостей."
    return "This route has no news yet."


def route_no_questions_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "В этом маршруте пока нет вопросов."
    return "This route has no questions yet."


def route_no_news_and_questions_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Для этого маршрута пока нет новостей и вопросов."
    return "This route has no news or questions yet."


def route_no_steps_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "В этом маршруте пока нет шагов."
    return "This route has no steps yet."


def route_step_transcript_label(language: str, *, step_type: str) -> str:
    if step_type == "atis":
        return "📄 ATIS:"
    if step_type == "atc_command":
        if normalize_language(language) == "ru":
            return "📄 Команда:"
        return "📄 Command:"
    if normalize_language(language) == "ru":
        return "📄 Подсказка:"
    return "📄 Hint:"


def route_step_pilot_answer_label(language: str) -> str:
    _ = language
    return "💬 Pilot:"


def route_step_text(
    language: str,
    *,
    step_text: str,
    transcript_text: str | None,
    show_transcript: bool,
    step_type: str,
    pilot_answer_text: str | None,
    show_pilot_answer: bool,
) -> str:
    parts: list[str] = [step_text]
    if show_transcript and transcript_text:
        parts.extend(
            [
                "",
                route_step_transcript_label(language, step_type=step_type),
                transcript_text,
            ]
        )
    if show_pilot_answer and pilot_answer_text:
        parts.extend(
            [
                "",
                route_step_pilot_answer_label(language),
                pilot_answer_text,
            ]
        )
    return "\n".join(parts)


def route_show_atis_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📄 Показать ATIS"
    return "📄 Show ATIS"


def route_hide_atis_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📄 Скрыть ATIS"
    return "📄 Hide ATIS"


def route_show_command_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📄 Показать команду"
    return "📄 Show command"


def route_hide_command_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📄 Скрыть команду"
    return "📄 Hide command"


def route_show_hint_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📄 Показать подсказку"
    return "📄 Show hint"


def route_hide_hint_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📄 Скрыть подсказку"
    return "📄 Hide hint"


def route_show_answer_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "💬 Показать ответ"
    return "💬 Show answer"


def route_hide_answer_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "💬 Скрыть ответ"
    return "💬 Hide answer"


def route_interrupt_title(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⚠️ Прервать тренировку?"
    return "⚠️ Interrupt training?"


def route_interrupt_body(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Прогресс по маршруту не будет засчитан."
    return "Route progress will not be saved."


def route_interrupt_text(language: str) -> str:
    return f"{route_interrupt_title(language)}\n\n{route_interrupt_body(language)}"


def route_interrupt_stay_button(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⛔ Остаться"
    return "⛔ Stay"


def route_interrupt_yes_button(language: str) -> str:
    if normalize_language(language) == "ru":
        return "✅ Прервать"
    return "✅ Interrupt"


def route_stale_session_alert(language: str) -> str:
    if normalize_language(language) == "ru":
        return "Сессия маршрута устарела. Открываю список маршрутов."
    return "Route session is stale. Opening routes list."


def route_news_text(
    language: str,
    *,
    transcript_text: str | None,
    show_transcript: bool,
) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        parts: list[str] = [
            "📰 Новости",
            "",
            "Прослушайте новость по этому маршруту.",
        ]
        if show_transcript and transcript_text:
            parts.extend(
                [
                    "",
                    "📄 Текст новости:",
                    transcript_text,
                ]
            )
        return "\n".join(parts)

    parts = [
        "📰 News",
        "",
        "Listen to the news related to this route.",
    ]
    if show_transcript and transcript_text:
        parts.extend(
            [
                "",
                "📄 News transcript:",
                transcript_text,
            ]
        )
    return "\n".join(parts)


def route_news_list_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📰 Новости маршрута\n\nВыберите новость:"
    return "📰 Route news\n\nChoose a news item:"


def route_news_item_button_text(language: str, *, news_order: int) -> str:
    _ = language
    return f"📰 News {news_order}"


def route_question_blocks_list_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "❓ Вопросы маршрута\n\nВыберите блок вопросов:"
    return "❓ Route questions\n\nChoose a question block:"


def route_question_block_button_text(language: str, *, block_order: int) -> str:
    if normalize_language(language) == "ru":
        return f"Блок {block_order}"
    return f"Block {block_order}"


def route_news_show_transcript_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "📄 Показать текст новости"
    return "📄 Show transcript"


def route_news_hide_transcript_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🙈 Скрыть текст новости"
    return "🙈 Hide transcript"


def route_questions_screen_text(
    language: str,
    *,
    current_index: int,
    total_questions: int,
    question_en: str,
    show_ru_translation: bool,
    question_translation_ru: str | None,
) -> str:
    lang = normalize_language(language)
    if lang == "ru":
        parts: list[str] = [
            f"❓ Вопрос {current_index} из {total_questions}",
            "",
            question_en,
        ]
        if show_ru_translation and question_translation_ru:
            parts.extend(
                [
                    "",
                    "🌐 Перевод:",
                    question_translation_ru,
                ]
            )
        return "\n".join(parts)

    return f"❓ Question {current_index} of {total_questions}\n\n{question_en}"


def route_question_translate_button_text(language: str, *, open_translation: bool) -> str:
    if normalize_language(language) != "ru":
        return ""
    if open_translation:
        return "🙈 Скрыть перевод"
    return "🌐 Перевести вопрос"


def route_question_finish_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "✅ Завершить"
    return "✅ Finish"


def route_to_route_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⬅️ К маршруту"
    return "⬅️ To route"


def route_to_news_list_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⬅️ К списку новостей"
    return "⬅️ To news list"


def route_to_blocks_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "⬅️ К блокам"
    return "⬅️ To blocks"


def route_another_route_button_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return "🛫 Другой маршрут"
    return "🛫 Another route"


def route_full_completion_text(language: str, *, route_title: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "✅ Маршрут пройден\n\n"
            "Вы завершили тренировку маршрута:\n"
            f"{route_title}\n\n"
            "Маршруты — это тренировка устойчивого радиообмена.\n"
            "Регулярная практика помогает быстрее понимать диспетчера и увереннее отвечать."
        )
    return (
        "✅ Route completed\n\n"
        "You have completed the route:\n"
        f"{route_title}\n\n"
        "Routes help you practise stable pilot-controller communication.\n"
        "Regular practice improves listening and response confidence."
    )


def route_free_completion_text(language: str) -> str:
    if normalize_language(language) == "ru":
        return (
            "✅ Тренировка завершена\n\n"
            "Это была свободная тренировка.\n"
            "Прогресс маршрута не засчитан."
        )
    return (
        "✅ Training completed\n\n"
        "This was free practice.\n"
        "Route progress was not counted."
    )
