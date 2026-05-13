"""Service layer for routes feature."""

from __future__ import annotations

import random

from telegram import Bot

from db.connection import get_connection
from db.repositories.routes_repo import (
    get_route_user_state,
    list_active_news_for_route,
    upsert_route_news_state,
)
from features.routes.texts import (
    route_no_news_and_questions_alert,
    route_stale_session_alert,
)
from features.routes.service_list import (
    return_to_route_briefing,
    show_route_briefing,
    show_routes_list,
)
from features.routes.service_news import (
    _render_route_news,
    open_route_news_from_briefing as _open_route_news_from_briefing_impl,
    open_route_news_from_list as _open_route_news_from_list_impl,
    show_route_news_list as _show_route_news_list_impl,
    toggle_route_news_transcript as _toggle_route_news_transcript_impl,
)
from features.routes.service_questions import (
    _open_questions_flow,
    _render_route_question,
    finish_route_questions as _finish_route_questions_impl,
    move_route_question as _move_route_question_impl,
    open_route_questions_for_block as _open_route_questions_for_block_impl,
    open_route_questions_from_briefing as _open_route_questions_from_briefing_impl,
    open_route_questions_from_news as _open_route_questions_from_news_impl,
    return_to_question_blocks_list as _return_to_question_blocks_list_impl,
    show_route_question_blocks_list as _show_route_question_blocks_list_impl,
    toggle_route_question_translation as _toggle_route_question_translation_impl,
)
from features.routes.service_scenario import (
    _render_route_step,
    move_route_step as _move_route_step_impl,
    start_route_scenario as _start_route_scenario_impl,
    toggle_route_pilot_answer as _toggle_route_pilot_answer_impl,
    toggle_route_transcript as _toggle_route_transcript_impl,
)
from features.routes.service_session import (
    _ENTRY_MODE_FULL,
    _PHASE_SCENARIO,
    _PHASE_NEWS,
    _PHASE_QUESTIONS,
    _is_state_active_for_route,
    _state_entry_mode,
    _state_phase,
)
from features.routes.service_interrupt import (
    route_interrupt_confirm,
    routes_go_home,
    show_route_interrupt_confirmation,
)



async def show_route_news_list(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    page: int,
) -> tuple[bool, str | None]:
    return await _show_route_news_list_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        page=page,
    )


async def open_route_news_from_list(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    news_id: int,
    page: int,
) -> tuple[bool, str | None]:
    return await _open_route_news_from_list_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        news_id=news_id,
        page=page,
    )


async def show_route_question_blocks_list(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    page: int,
) -> tuple[bool, str | None]:
    return await _show_route_question_blocks_list_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        page=page,
    )


async def open_route_questions_for_block(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    block_id: int,
) -> tuple[bool, str | None]:
    return await _open_route_questions_for_block_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        block_id=block_id,
    )


def _pick_random_active_news(conn, *, route_id: int) -> dict[str, object] | None:
    news_items = list_active_news_for_route(conn, route_id=route_id)
    if not news_items:
        return None
    return random.choice(news_items)


async def start_route_scenario(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    return await _start_route_scenario_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
    )


async def _open_news_or_questions_after_scenario(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    with get_connection() as conn:
        news = _pick_random_active_news(conn, route_id=route_id)
        if news is not None:
            upsert_route_news_state(
                conn,
                user_id=user_id,
                route_id=route_id,
                selected_news_id=int(news["id"]),
                show_transcript=0,
                entry_mode=_ENTRY_MODE_FULL,
                is_active_session=1,
            )
            news_id = int(news["id"])
        else:
            news_id = None

    if news_id is not None:
        rendered = await _render_route_news(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            news_id=news_id,
            show_transcript=False,
            entry_mode=_ENTRY_MODE_FULL,
            news_list_page=None,
            resend_media=True,
        )
        if not rendered:
            return False, route_stale_session_alert(language)
        return True, None

    opened_questions, alert_text = await _open_questions_flow(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        entry_mode=_ENTRY_MODE_FULL,
    )
    if opened_questions:
        return True, None
    return False, route_no_news_and_questions_alert(language)


async def open_route_news_from_briefing(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    return await _open_route_news_from_briefing_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
    )


async def open_route_questions_from_briefing(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    return await _open_route_questions_from_briefing_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
    )


async def open_route_questions_from_news(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    return await _open_route_questions_from_news_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
    )


async def return_to_question_blocks_list(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    return await _return_to_question_blocks_list_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
    )


async def toggle_route_news_transcript(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    news_list_page: int | None,
) -> tuple[bool, str | None]:
    return await _toggle_route_news_transcript_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        news_list_page=news_list_page,
    )


async def move_route_question(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_question_number: int,
    direction: str,
) -> tuple[bool, str | None]:
    return await _move_route_question_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        callback_question_number=callback_question_number,
        direction=direction,
    )


async def toggle_route_question_translation(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_question_number: int,
) -> tuple[bool, str | None]:
    return await _toggle_route_question_translation_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        callback_question_number=callback_question_number,
    )


async def finish_route_questions(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_question_number: int,
) -> tuple[bool, str | None]:
    return await _finish_route_questions_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        callback_question_number=callback_question_number,
    )


async def toggle_route_transcript(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_step_number: int,
) -> tuple[bool, str | None]:
    return await _toggle_route_transcript_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        callback_step_number=callback_step_number,
    )


async def toggle_route_pilot_answer(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_step_number: int,
) -> tuple[bool, str | None]:
    return await _toggle_route_pilot_answer_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        callback_step_number=callback_step_number,
    )


async def move_route_step(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_step_number: int,
    direction: str,
) -> tuple[bool, str | None]:
    async def _open_after_scenario() -> tuple[bool, str | None]:
        return await _open_news_or_questions_after_scenario(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            route_id=route_id,
        )

    return await _move_route_step_impl(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        callback_step_number=callback_step_number,
        direction=direction,
        open_after_scenario=_open_after_scenario,
    )


async def route_interrupt_stay(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    """Return from interrupt confirmation to current active phase."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_SCENARIO, _PHASE_NEWS, _PHASE_QUESTIONS},
        ):
            return False, route_stale_session_alert(language)
        phase = _state_phase(state)
        show_transcript = int(state.get("show_transcript") or 0) == 1
        show_pilot_answer = int(state.get("show_pilot_answer") or 0) == 1
        show_ru_translation = int(state.get("show_ru_translation") or 0) == 1
        step_number = int(state.get("current_step_number") or 0)
        news_id = int(state.get("selected_news_id") or 0)
        block_id = int(state.get("selected_block_id") or 0)
        question_number = int(state.get("current_question_number") or 0)

    if phase == _PHASE_SCENARIO:
        if step_number <= 0:
            return False, route_stale_session_alert(language)
        rendered = await _render_route_step(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            step_number=step_number,
            show_transcript=show_transcript,
            show_pilot_answer=show_pilot_answer,
            resend_media=False,
        )
        if not rendered:
            return False, route_stale_session_alert(language)
        return True, None

    if phase == _PHASE_NEWS:
        if news_id <= 0:
            return False, route_stale_session_alert(language)
        rendered = await _render_route_news(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            news_id=news_id,
            show_transcript=show_transcript,
            entry_mode=_state_entry_mode(state),
            news_list_page=1,
            resend_media=False,
        )
        if not rendered:
            return False, route_stale_session_alert(language)
        return True, None

    if phase == _PHASE_QUESTIONS:
        if block_id <= 0 or question_number <= 0:
            return False, route_stale_session_alert(language)
        rendered = await _render_route_question(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            block_id=block_id,
            question_number=question_number,
            show_ru_translation=show_ru_translation,
            entry_mode=_state_entry_mode(state),
            resend_media=False,
        )
        if not rendered:
            return False, route_stale_session_alert(language)
        return True, None

    return False, route_stale_session_alert(language)
