"""Scenario-step helpers for routes service."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from telegram import Bot

from db.connection import get_connection
from db.repositories.routes_repo import (
    deactivate_active_route_sessions,
    get_active_steps_for_route,
    get_next_active_step_number,
    get_previous_active_step_number,
    get_route_by_id,
    get_route_step,
    get_route_user_state,
    update_route_step_state,
    upsert_route_user_state,
)
from features.routes.keyboards import build_route_step_keyboard
from features.routes.service_list import _render_route_main_ui
from features.routes.service_media import (
    _MEDIA_CONTENT_TYPE_ROUTE_STEP_AUDIO,
    _MEDIA_CONTENT_TYPE_ROUTE_STEP_IMAGE,
    _build_route_step_audio_content_key,
    _build_route_step_image_content_key,
    _send_route_media_before_ui_best_effort,
    cleanup_routes_temp_images,
)
from features.routes.service_session import _PHASE_SCENARIO, _is_state_active_for_route
from features.routes.texts import (
    normalize_language,
    route_no_steps_alert,
    route_stale_session_alert,
    route_step_text,
)


def _resolve_step_text(step: dict[str, object], *, language: str) -> str:
    if normalize_language(language) == "ru":
        text_ru = str(step.get("text_ru") or "").strip()
        if text_ru:
            return text_ru
    text_en = str(step.get("text_en") or "").strip()
    if text_en:
        return text_en
    text_ru = str(step.get("text_ru") or "").strip()
    if text_ru:
        return text_ru
    return ""


def _resolve_transcript_text(step: dict[str, object], *, language: str) -> str | None:
    if normalize_language(language) == "ru":
        transcript_ru = str(step.get("transcript_ru") or "").strip()
        if transcript_ru:
            return transcript_ru
    transcript_en = str(step.get("transcript_en") or "").strip()
    if transcript_en:
        return transcript_en
    transcript_ru = str(step.get("transcript_ru") or "").strip()
    if transcript_ru:
        return transcript_ru
    return None


def _resolve_pilot_answer_text(step: dict[str, object], *, language: str) -> str | None:
    if normalize_language(language) == "ru":
        answer_ru = str(step.get("pilot_answer_ru") or "").strip()
        if answer_ru:
            return answer_ru
    answer_en = str(step.get("pilot_answer_en") or "").strip()
    if answer_en:
        return answer_en
    answer_ru = str(step.get("pilot_answer_ru") or "").strip()
    if answer_ru:
        return answer_ru
    return None


async def _render_route_step(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    step_number: int,
    show_transcript: bool,
    show_pilot_answer: bool,
    resend_media: bool,
) -> bool:
    lang = normalize_language(language)
    with get_connection() as conn:
        route = get_route_by_id(conn, route_id=route_id)
        step = get_route_step(conn, route_id=route_id, step_number=step_number)
        has_previous = get_previous_active_step_number(
            conn,
            route_id=route_id,
            current_step_number=step_number,
        ) is not None
        has_next = get_next_active_step_number(
            conn,
            route_id=route_id,
            current_step_number=step_number,
        ) is not None
    if step is None:
        return False

    step_text = _resolve_step_text(step, language=lang)
    if not step_text:
        return False
    transcript_text = _resolve_transcript_text(step, language=lang)
    pilot_answer_text = _resolve_pilot_answer_text(step, language=lang)
    step_type = str(step.get("step_type") or "").strip().lower()
    route_code = str((route or {}).get("code") or "").strip() or None
    step_image_content_key = _build_route_step_image_content_key(
        route_code,
        step_number,
    )
    step_audio_content_key = _build_route_step_audio_content_key(
        route_code,
        step_number,
    )

    media_sent = False
    if resend_media:
        await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
        media_sent = await _send_route_media_before_ui_best_effort(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            image_file=str(step.get("image_file") or "").strip() or None,
            image_content_type=_MEDIA_CONTENT_TYPE_ROUTE_STEP_IMAGE,
            image_content_key=step_image_content_key,
            audio_file=str(step.get("audio_file") or "").strip() or None,
            audio_content_type=_MEDIA_CONTENT_TYPE_ROUTE_STEP_AUDIO,
            audio_content_key=step_audio_content_key,
        )

    await _render_route_main_ui(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        text=route_step_text(
            lang,
            step_text=step_text,
            transcript_text=transcript_text,
            show_transcript=show_transcript,
            step_type=step_type,
            pilot_answer_text=pilot_answer_text,
            show_pilot_answer=show_pilot_answer,
        ),
        reply_markup=build_route_step_keyboard(
            lang,
            route_id=route_id,
            step_number=int(step["step_number"]),
            has_previous=has_previous,
            has_next=has_next,
            has_transcript=bool(transcript_text),
            transcript_open=show_transcript,
            step_type=step_type,
            has_pilot_answer=bool(pilot_answer_text),
            pilot_answer_open=show_pilot_answer,
        ),
        media_sent=media_sent,
    )
    return True


async def start_route_scenario(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    """
    Start route scenario from briefing.

    Returns (success, alert_text_if_any).
    """
    await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
    with get_connection() as conn:
        route = get_route_by_id(conn, route_id=route_id)
        if route is None or int(route.get("is_active") or 0) != 1:
            return False, route_stale_session_alert(language)
        active_steps = get_active_steps_for_route(conn, route_id=route_id)
        if not active_steps:
            return False, route_no_steps_alert(language)
        first_step_number = int(active_steps[0]["step_number"])
        deactivate_active_route_sessions(conn, user_id=user_id)
        upsert_route_user_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            phase=_PHASE_SCENARIO,
            current_step_number=first_step_number,
            show_transcript=0,
            show_pilot_answer=0,
            show_ru_translation=0,
            entry_mode="full",
            is_active_session=1,
        )
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if state is None:
            return False, route_stale_session_alert(language)

    rendered = await _render_route_step(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        step_number=first_step_number,
        show_transcript=False,
        show_pilot_answer=False,
        resend_media=True,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None


async def toggle_route_transcript(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_step_number: int,
) -> tuple[bool, str | None]:
    """Toggle transcript visibility on current scenario step."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_SCENARIO},
        ):
            return False, route_stale_session_alert(language)
        current_step_number = int(state.get("current_step_number") or 0)
        if current_step_number <= 0 or current_step_number != callback_step_number:
            return False, route_stale_session_alert(language)
        next_transcript_value = 0 if int(state.get("show_transcript") or 0) == 1 else 1
        update_route_step_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            current_step_number=current_step_number,
            show_transcript=next_transcript_value,
            show_pilot_answer=int(state.get("show_pilot_answer") or 0),
        )
        next_pilot_answer = int(state.get("show_pilot_answer") or 0)

    rendered = await _render_route_step(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        step_number=current_step_number,
        show_transcript=bool(next_transcript_value),
        show_pilot_answer=bool(next_pilot_answer),
        resend_media=False,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None


async def toggle_route_pilot_answer(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_step_number: int,
) -> tuple[bool, str | None]:
    """Toggle pilot answer visibility on current scenario step."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_SCENARIO},
        ):
            return False, route_stale_session_alert(language)
        current_step_number = int(state.get("current_step_number") or 0)
        if current_step_number <= 0 or current_step_number != callback_step_number:
            return False, route_stale_session_alert(language)
        next_answer_value = 0 if int(state.get("show_pilot_answer") or 0) == 1 else 1
        update_route_step_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            current_step_number=current_step_number,
            show_transcript=int(state.get("show_transcript") or 0),
            show_pilot_answer=next_answer_value,
        )
        next_transcript_value = int(state.get("show_transcript") or 0)

    rendered = await _render_route_step(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        step_number=current_step_number,
        show_transcript=bool(next_transcript_value),
        show_pilot_answer=bool(next_answer_value),
        resend_media=False,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None


async def move_route_step(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_step_number: int,
    direction: str,
    open_after_scenario: Callable[[], Awaitable[tuple[bool, str | None]]],
) -> tuple[bool, str | None]:
    """Move to next/previous scenario step with media cleanup and toggle reset."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_SCENARIO},
        ):
            return False, route_stale_session_alert(language)
        current_step_number = int(state.get("current_step_number") or 0)
        if current_step_number <= 0 or current_step_number != callback_step_number:
            return False, route_stale_session_alert(language)
        if direction == "next":
            target_step_number = get_next_active_step_number(
                conn,
                route_id=route_id,
                current_step_number=current_step_number,
            )
            if target_step_number is None:
                target_step_number = None
        elif direction == "back":
            target_step_number = get_previous_active_step_number(
                conn,
                route_id=route_id,
                current_step_number=current_step_number,
            )
            if target_step_number is None:
                return False, route_stale_session_alert(language)
        else:
            return False, route_stale_session_alert(language)

        if target_step_number is not None:
            update_route_step_state(
                conn,
                user_id=user_id,
                route_id=route_id,
                current_step_number=target_step_number,
                show_transcript=0,
                show_pilot_answer=0,
            )

    if target_step_number is None:
        await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
        return await open_after_scenario()

    rendered = await _render_route_step(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        step_number=target_step_number,
        show_transcript=False,
        show_pilot_answer=False,
        resend_media=True,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None
