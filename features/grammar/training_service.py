"""Training flow logic for grammar feature."""

from __future__ import annotations

from dataclasses import dataclass
import json

from telegram import Update
from telegram.ext import ContextTypes

from core.message_stack import render_main_ui
from db.connection import get_connection
from db.repositories.grammar_repo import (
    get_question_by_topic_and_number,
    get_topic_by_number,
    list_extra_topics,
    list_main_topics,
    list_questions_for_training,
    mark_grammar_topic_studied,
)
from db.repositories.grammar_training_repo import (
    get_training_session_by_id,
    update_training_session_progress,
    upsert_training_session,
)
from features.grammar.formatting import (
    _localized_value,
    _sanitize_dynamic_html,
    _strip_leading_icon,
    _truncate_popup_text,
)
from features.grammar.keyboards import (
    grammar_training_question_keyboard,
    grammar_training_result_keyboard,
)
from features.grammar.pagination import (
    _build_topic_navigation_context,
    _to_non_negative_int,
    _to_positive_int,
)
from features.grammar.texts import (
    normalize_language,
    training_correct_popup_text,
    training_incorrect_popup_text,
    training_question_text,
    training_question_unavailable_alert,
    training_result_excellent_text,
    training_result_good_text,
    training_result_weak_text,
    training_session_expired_alert,
)
from features.main_menu.service import get_user_language_by_telegram_id


GRAMMAR_TRAINING_LIMIT = 10


@dataclass(slots=True)
class TrainingAnswerOutcome:
    status: str
    popup_text: str
    show_alert: bool
    session: dict[str, object] | None = None
    result_kind: str | None = None
    mark_applied: bool = False


def _topic_is_extra(topic: dict[str, object]) -> bool:
    return str(topic.get("topic_type") or "").strip().lower() == "extra"


def _load_question_numbers_from_session(session: dict[str, object]) -> list[int]:
    raw_value = session.get("question_numbers_json")
    if raw_value is None:
        return []
    try:
        decoded = json.loads(str(raw_value))
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    if not isinstance(decoded, list):
        return []

    numbers: list[int] = []
    for item in decoded:
        try:
            number = int(item)
        except (TypeError, ValueError):
            continue
        if number > 0:
            numbers.append(number)
    return numbers


def _is_extra_topic_type(topic_type: object) -> bool:
    return str(topic_type or "").strip().lower() == "extra"


def _resolve_result_kind(*, total_questions: int, wrong_count: int) -> str:
    if wrong_count == 0:
        return "excellent"
    if wrong_count < (total_questions / 2):
        return "good"
    return "weak"


def _build_answer_buttons(question: dict[str, object], language: str) -> list[str]:
    _ = language
    answers: list[str] = []
    for index in range(1, 4):
        answer_value = str(question.get(f"answer_{index}") or "").strip() or "—"
        answers.append(answer_value)
    return answers


def create_new_training_session(
    user_id: int,
    topic_number: int,
    *,
    source_page: int,
    is_extra: bool | None = None,
) -> tuple[str, dict[str, object] | None]:
    """Create new training session for user and topic."""
    safe_page = _to_positive_int(source_page, fallback=1)
    with get_connection() as conn:
        topic = get_topic_by_number(conn, topic_number)
        if topic is None:
            return "topic_unavailable", None

        topic_is_extra = _topic_is_extra(topic)
        if is_extra is not None and topic_is_extra != is_extra:
            return "topic_unavailable", None

        questions = list_questions_for_training(
            conn,
            topic_number=topic_number,
            limit=GRAMMAR_TRAINING_LIMIT,
        )
        question_numbers = [
            _to_positive_int(row.get("question_number"), fallback=0)
            for row in questions
            if _to_positive_int(row.get("question_number"), fallback=0) > 0
        ]
        if not question_numbers:
            return "no_questions", None

        session_row = upsert_training_session(
            conn,
            user_id=user_id,
            topic_number=topic_number,
            topic_type="extra" if topic_is_extra else "main",
            source_page=safe_page,
            question_numbers=question_numbers,
        )
    return "ok", dict(session_row)


async def show_training_question(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict[str, object],
    session: dict[str, object],
) -> bool:
    """Render current training question from active session."""
    chat = update.effective_chat
    if chat is None:
        return False

    user_id = int(user["id"])
    telegram_id = int(user["telegram_id"])
    language = get_user_language_by_telegram_id(telegram_id)
    lang = normalize_language(language)

    session_id = _to_positive_int(session.get("id"), fallback=0)
    topic_number = _to_positive_int(session.get("topic_number"), fallback=0)
    source_page = _to_positive_int(session.get("source_page"), fallback=1)
    current_index = _to_non_negative_int(session.get("current_index"), fallback=0)
    question_numbers = _load_question_numbers_from_session(session)
    if session_id <= 0 or topic_number <= 0 or not question_numbers:
        return False

    if current_index < 0 or current_index >= len(question_numbers):
        return False

    question_number = question_numbers[current_index]
    with get_connection() as conn:
        topic = get_topic_by_number(conn, topic_number)
        if topic is None:
            return False
        question = get_question_by_topic_and_number(
            conn,
            topic_number=topic_number,
            question_number=question_number,
        )
        if question is None:
            return False

    title = _localized_value(
        lang,
        ru_value=topic.get("title_ru"),  # type: ignore[arg-type]
        en_value=topic.get("title_en"),  # type: ignore[arg-type]
        default_value=f"Topic {topic_number}",
    )
    header_title = _sanitize_dynamic_html(_strip_leading_icon(title))
    question_text_value = str(question.get("question") or "").strip()
    if not question_text_value.strip():
        return False
    question_text_value = _sanitize_dynamic_html(question_text_value)

    answers = _build_answer_buttons(question, lang)
    total_questions = max(1, len(question_numbers))
    await render_main_ui(
        bot=context.bot,
        chat_id=chat.id,
        user_id=user_id,
        text=training_question_text(
            lang,
            topic_title=header_title,
            question_index=current_index + 1,
            total_questions=total_questions,
            question_text=question_text_value,
        ),
        reply_markup=grammar_training_question_keyboard(
            lang,
            session_id=session_id,
            topic_number=topic_number,
            source_page=source_page,
            is_extra=_is_extra_topic_type(session.get("topic_type")),
            answers=answers,
        ),
        parse_mode="HTML",
    )
    return True


def process_answer(
    *,
    user_id: int,
    language: str,
    session_id: int,
    answer_number: int,
) -> TrainingAnswerOutcome:
    """Process one training answer and update session state."""
    lang = normalize_language(language)
    if answer_number not in {1, 2, 3}:
        return TrainingAnswerOutcome(
            status="question_unavailable",
            popup_text=training_question_unavailable_alert(lang),
            show_alert=True,
        )

    with get_connection() as conn:
        row = get_training_session_by_id(conn, session_id=session_id, user_id=user_id)
        if row is None:
            return TrainingAnswerOutcome(
                status="session_expired",
                popup_text=training_session_expired_alert(lang),
                show_alert=True,
            )

        session = dict(row)
        if _to_positive_int(session.get("is_finished"), fallback=0) == 1:
            return TrainingAnswerOutcome(
                status="session_expired",
                popup_text=training_session_expired_alert(lang),
                show_alert=True,
            )

        question_numbers = _load_question_numbers_from_session(session)
        current_index = _to_non_negative_int(session.get("current_index"), fallback=0)
        if not question_numbers or current_index < 0 or current_index >= len(question_numbers):
            return TrainingAnswerOutcome(
                status="session_expired",
                popup_text=training_session_expired_alert(lang),
                show_alert=True,
            )

        topic_number = _to_positive_int(session.get("topic_number"), fallback=0)
        if topic_number <= 0:
            return TrainingAnswerOutcome(
                status="session_expired",
                popup_text=training_session_expired_alert(lang),
                show_alert=True,
            )

        question_number = question_numbers[current_index]
        question = get_question_by_topic_and_number(
            conn,
            topic_number=topic_number,
            question_number=question_number,
        )
        if question is None:
            return TrainingAnswerOutcome(
                status="question_unavailable",
                popup_text=training_question_unavailable_alert(lang),
                show_alert=True,
            )

        correct_answer = _to_positive_int(question.get("correct_answer"), fallback=0)
        correct_count = _to_positive_int(session.get("correct_count"), fallback=0)
        wrong_count = _to_positive_int(session.get("wrong_count"), fallback=0)

        if answer_number == correct_answer:
            correct_count += 1
            popup_text = training_correct_popup_text(lang)
            show_alert = False
        else:
            wrong_count += 1
            wrong_explanation = _localized_value(
                lang,
                ru_value=question.get("wrong_explanation_ru"),  # type: ignore[arg-type]
                en_value=question.get("wrong_explanation_en"),  # type: ignore[arg-type]
                default_value="",
            )
            popup_text = training_incorrect_popup_text(lang, wrong_explanation)
            show_alert = True

        next_index = current_index + 1
        is_finished = next_index >= len(question_numbers)
        update_training_session_progress(
            conn,
            session_id=session_id,
            current_index=next_index,
            correct_count=correct_count,
            wrong_count=wrong_count,
            is_finished=is_finished,
        )

        result_kind: str | None = None
        mark_applied = False
        if is_finished:
            result_kind = _resolve_result_kind(
                total_questions=len(question_numbers),
                wrong_count=wrong_count,
            )
            topic_type = str(session.get("topic_type") or "").strip().lower()
            if topic_type == "main" and result_kind in {"excellent", "good"}:
                mark_grammar_topic_studied(conn, user_id=user_id, topic_number=topic_number)
                mark_applied = True

        updated_row = get_training_session_by_id(conn, session_id=session_id, user_id=user_id)
        if updated_row is None:
            updated_session = {
                **session,
                "current_index": next_index,
                "correct_count": correct_count,
                "wrong_count": wrong_count,
                "is_finished": int(is_finished),
            }
        else:
            updated_session = dict(updated_row)

    return TrainingAnswerOutcome(
        status="show_result" if is_finished else "next_question",
        popup_text=_truncate_popup_text(popup_text),
        show_alert=show_alert,
        session=updated_session,
        result_kind=result_kind,
        mark_applied=mark_applied,
    )


async def show_training_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user: dict[str, object],
    session: dict[str, object],
    *,
    result_kind: str,
    mark_applied: bool,
) -> bool:
    """Render training result screen."""
    chat = update.effective_chat
    if chat is None:
        return False

    user_id = int(user["id"])
    telegram_id = int(user["telegram_id"])
    language = get_user_language_by_telegram_id(telegram_id)
    lang = normalize_language(language)

    topic_number = _to_positive_int(session.get("topic_number"), fallback=0)
    if topic_number <= 0:
        return False

    question_numbers = _load_question_numbers_from_session(session)
    total_questions = _to_positive_int(
        session.get("total_questions"),
        fallback=len(question_numbers) if question_numbers else 0,
    )
    if total_questions <= 0:
        return False

    correct_count = _to_positive_int(session.get("correct_count"), fallback=0)
    wrong_count = _to_positive_int(session.get("wrong_count"), fallback=0)
    source_page = _to_positive_int(session.get("source_page"), fallback=1)
    is_extra = _is_extra_topic_type(session.get("topic_type"))
    with get_connection() as conn:
        topics_for_navigation = list_extra_topics(conn) if is_extra else list_main_topics(conn)
    navigation = _build_topic_navigation_context(
        topics_for_navigation,
        topic_number=topic_number,
    )

    if result_kind == "excellent":
        text = training_result_excellent_text(
            lang,
            correct=correct_count,
            wrong=wrong_count,
            total=total_questions,
            mark_applied=mark_applied,
        )
    elif result_kind == "good":
        text = training_result_good_text(
            lang,
            correct=correct_count,
            wrong=wrong_count,
            total=total_questions,
            mark_applied=mark_applied,
        )
    else:
        text = training_result_weak_text(
            lang,
            correct=correct_count,
            wrong=wrong_count,
            total=total_questions,
        )

    await render_main_ui(
        bot=context.bot,
        chat_id=chat.id,
        user_id=user_id,
        text=text,
        reply_markup=grammar_training_result_keyboard(
            lang,
            topic_number=topic_number,
            source_page=source_page,
            is_extra=is_extra,
            is_weak_result=(result_kind == "weak"),
            next_topic_number=(
                navigation.next_topic_number if result_kind in {"excellent", "good"} else None
            ),
            next_topic_page=(
                navigation.next_topic_page if result_kind in {"excellent", "good"} else None
            ),
        ),
        parse_mode="HTML",
    )
    return True
