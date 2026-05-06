"""Question-level rendering and navigation for Questions feature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from telegram import Bot

from core.message_stack import render_main_ui
from db.connection import get_connection
from db.repositories.questions_progress_repo import mark_question_completed, set_current_question
from features.questions.audio_service import send_question_audio_if_exists
from features.questions.keyboards import (
    VIEW_BASE,
    VIEW_REVIEW,
    build_base_question_keyboard,
    build_review_keyboard,
)
from features.questions.progress_service import (
    QuestionNavigationContext,
    load_level_questions_context,
    resolve_question_navigation,
)
from features.questions.texts import (
    level_unavailable_alert,
    question_base_text,
    question_review_text,
    question_unavailable_alert,
)


QuestionActionStatus = Literal["rendered", "completed", "level_unavailable", "question_unavailable"]


@dataclass(frozen=True, slots=True)
class QuestionActionResult:
    status: QuestionActionStatus
    popup_text: str | None = None
    show_alert: bool = False


def _trimmed(value: object) -> str:
    return str(value or "").strip()


def _normalize_view_mode(view_mode: str) -> str:
    normalized = (view_mode or "").strip().lower()
    if normalized == VIEW_REVIEW:
        return VIEW_REVIEW
    return VIEW_BASE


def _resolve_navigation(level: int, question_number: int) -> tuple[QuestionNavigationContext | None, str | None]:
    with get_connection() as conn:
        context = load_level_questions_context(conn, level)
        if context is None:
            return None, "level_unavailable"
        navigation = resolve_question_navigation(context, question_number)
    if navigation is None:
        return None, "question_unavailable"
    return navigation, None


def _build_base_text(language: str, *, navigation: QuestionNavigationContext) -> str:
    question = navigation.question
    question_en = _trimmed(question.get("question_en"))
    return question_base_text(
        language,
        level=navigation.level,
        current=navigation.index,
        total=navigation.total,
        question_en=question_en,
    )


def _build_review_text(language: str, *, navigation: QuestionNavigationContext) -> str:
    question = navigation.question
    return question_review_text(
        language,
        level=navigation.level,
        current=navigation.index,
        total=navigation.total,
        question_en=_trimmed(question.get("question_en")),
        question_translation_ru=_trimmed(question.get("question_translation_ru")),
        sample_answer_en=_trimmed(question.get("sample_answer_en")),
        sample_answer_translation_ru=_trimmed(question.get("sample_answer_translation_ru")),
    )


def _has_review_content(language: str, question: dict[str, object]) -> bool:
    sample_answer_en = _trimmed(question.get("sample_answer_en"))
    if language == "ru":
        return bool(
            _trimmed(question.get("question_translation_ru"))
            or sample_answer_en
            or _trimmed(question.get("sample_answer_translation_ru"))
        )
    # In EN interface, review is useful only when sample answer exists.
    return bool(sample_answer_en)


def _build_base_keyboard(language: str, *, navigation: QuestionNavigationContext):
    question = navigation.question
    return build_base_question_keyboard(
        language,
        level=navigation.level,
        question_number=navigation.question_number,
        has_review_content=_has_review_content(language, question),
        has_prev=navigation.has_prev,
        has_next=navigation.has_next,
    )


def _build_review_keyboard(language: str, *, navigation: QuestionNavigationContext):
    return build_review_keyboard(
        language,
        level=navigation.level,
        question_number=navigation.question_number,
        has_prev=navigation.has_prev,
        has_next=navigation.has_next,
    )


async def _render_question(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    navigation: QuestionNavigationContext,
    view_mode: str,
    resend_audio: bool,
) -> None:
    normalized_view_mode = _normalize_view_mode(view_mode)
    if normalized_view_mode == VIEW_REVIEW:
        text = _build_review_text(language, navigation=navigation)
        keyboard = _build_review_keyboard(language, navigation=navigation)
    else:
        text = _build_base_text(language, navigation=navigation)
        keyboard = _build_base_keyboard(language, navigation=navigation)

    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    if resend_audio:
        await send_question_audio_if_exists(
            bot,
            user_id=user_id,
            chat_id=chat_id,
            question=navigation.question,
        )


async def show_question_view(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    level: int,
    question_number: int,
    view_mode: str,
    resend_audio: bool,
) -> QuestionActionResult:
    navigation, error_code = _resolve_navigation(level, question_number)
    if error_code == "level_unavailable":
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )
    if error_code == "question_unavailable":
        return QuestionActionResult(
            status="question_unavailable",
            popup_text=question_unavailable_alert(language),
            show_alert=True,
        )
    if navigation is None:
        return QuestionActionResult(status="question_unavailable")

    normalized_view_mode = _normalize_view_mode(view_mode)

    with get_connection() as conn:
        set_current_question(conn, user_id, navigation.level, navigation.question_number)

    await _render_question(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        navigation=navigation,
        view_mode=normalized_view_mode,
        resend_audio=resend_audio,
    )
    return QuestionActionResult(status="rendered")


async def go_to_previous_question(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    level: int,
    question_number: int,
) -> QuestionActionResult:
    navigation, error_code = _resolve_navigation(level, question_number)
    if error_code == "level_unavailable":
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )
    if error_code == "question_unavailable":
        return QuestionActionResult(
            status="question_unavailable",
            popup_text=question_unavailable_alert(language),
            show_alert=True,
        )
    if navigation is None:
        return QuestionActionResult(status="question_unavailable")

    target_question_number = navigation.prev_question_number or navigation.question_number
    return await show_question_view(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        level=navigation.level,
        question_number=target_question_number,
        view_mode=VIEW_BASE,
        resend_audio=target_question_number != navigation.question_number,
    )


async def go_to_next_question(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    language: str,
    level: int,
    question_number: int,
) -> QuestionActionResult:
    navigation, error_code = _resolve_navigation(level, question_number)
    if error_code == "level_unavailable":
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )
    if error_code == "question_unavailable":
        return QuestionActionResult(
            status="question_unavailable",
            popup_text=question_unavailable_alert(language),
            show_alert=True,
        )
    if navigation is None:
        return QuestionActionResult(status="question_unavailable")

    with get_connection() as conn:
        mark_question_completed(conn, user_id, navigation.level, navigation.question_number)

    if navigation.next_question_number is None:
        return QuestionActionResult(status="completed")

    return await show_question_view(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        level=navigation.level,
        question_number=navigation.next_question_number,
        view_mode=VIEW_BASE,
        resend_audio=True,
    )


def finish_current_question(
    *,
    user_id: int,
    language: str,
    level: int,
    question_number: int,
) -> QuestionActionResult:
    navigation, error_code = _resolve_navigation(level, question_number)
    if error_code == "level_unavailable":
        return QuestionActionResult(
            status="level_unavailable",
            popup_text=level_unavailable_alert(language),
            show_alert=True,
        )
    if error_code == "question_unavailable":
        return QuestionActionResult(
            status="question_unavailable",
            popup_text=question_unavailable_alert(language),
            show_alert=True,
        )
    if navigation is None:
        return QuestionActionResult(status="question_unavailable")

    with get_connection() as conn:
        mark_question_completed(conn, user_id, navigation.level, navigation.question_number)
        set_current_question(conn, user_id, navigation.level, navigation.question_number)
    return QuestionActionResult(status="completed")
