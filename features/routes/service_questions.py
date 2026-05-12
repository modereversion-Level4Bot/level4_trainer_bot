"""Question blocks and questions flow for routes service."""

from __future__ import annotations

import random

from telegram import Bot

from core.message_stack import render_main_ui
from db.connection import get_connection
from db.repositories.routes_repo import (
    count_active_question_blocks_with_questions,
    deactivate_active_route_sessions,
    get_next_question_number,
    get_previous_question_number,
    get_route_by_id,
    get_route_question,
    get_route_user_state,
    get_question_block_by_id,
    list_active_question_blocks,
    list_active_question_blocks_with_question_counts,
    list_active_questions_for_block,
    mark_route_completed,
    update_route_question_state,
    upsert_route_questions_state,
    clear_route_user_state,
)
from features.routes.keyboards import (
    build_route_completion_keyboard,
    build_route_question_blocks_list_keyboard,
    build_route_questions_keyboard,
)
from features.routes.service_list import (
    _normalize_page,
    _render_route_main_ui,
    _resolve_route_title,
    _safe_total_pages,
)
from features.routes.service_media import (
    _MEDIA_CONTENT_TYPE_ROUTE_QUESTION_IMAGE,
    _build_route_question_image_content_key,
    _send_route_media_before_ui_best_effort,
    cleanup_routes_temp_images,
)
from features.routes.service_session import (
    _ENTRY_MODE_FREE_QUESTIONS,
    _ENTRY_MODE_FULL,
    _PHASE_NEWS,
    _PHASE_QUESTIONS,
    _is_full_entry_mode,
    _is_state_active_for_route,
    _state_entry_mode,
)
from features.routes.texts import (
    normalize_language,
    route_free_completion_text,
    route_full_completion_text,
    route_no_questions_alert,
    route_question_blocks_list_text,
    route_questions_screen_text,
    route_stale_session_alert,
)


_ROUTES_PER_PAGE = 4


def _resolve_question_translation_text(question: dict[str, object]) -> str | None:
    translation = str(question.get("question_translation_ru") or "").strip()
    return translation or None


def _pick_random_active_question_block(
    conn,
    *,
    route_id: int,
) -> tuple[dict[str, object], list[dict[str, object]]] | None:
    blocks = list_active_question_blocks(conn, route_id=route_id)
    eligible: list[tuple[dict[str, object], list[dict[str, object]]]] = []
    for block in blocks:
        block_id = int(block["id"])
        questions = list_active_questions_for_block(
            conn,
            route_id=route_id,
            block_id=block_id,
        )
        if questions:
            eligible.append((block, questions))
    if not eligible:
        return None
    return random.choice(eligible)


async def show_route_question_blocks_list(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    page: int,
) -> tuple[bool, str | None]:
    """Render selectable question blocks list for free mode."""
    lang = normalize_language(language)
    await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
    with get_connection() as conn:
        route = get_route_by_id(conn, route_id=route_id)
        if route is None or int(route.get("is_active") or 0) != 1:
            return False, route_stale_session_alert(language)
        total_blocks = count_active_question_blocks_with_questions(
            conn,
            route_id=route_id,
        )
        if total_blocks <= 0:
            return False, route_no_questions_alert(language)
        total_pages = _safe_total_pages(total_blocks)
        safe_page = _normalize_page(page, total_pages=total_pages)
        offset = (safe_page - 1) * _ROUTES_PER_PAGE
        block_rows = list_active_question_blocks_with_question_counts(
            conn,
            route_id=route_id,
            limit=_ROUTES_PER_PAGE,
            offset=offset,
        )

    block_buttons = [
        (int(item["id"]), int(item.get("block_order") or 0))
        for item in block_rows
    ]
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=route_question_blocks_list_text(lang),
        reply_markup=build_route_question_blocks_list_keyboard(
            lang,
            route_id=route_id,
            block_buttons=block_buttons,
            page=safe_page,
            total_pages=total_pages,
        ),
        parse_mode="HTML",
    )
    return True, None


async def open_route_questions_for_block(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    block_id: int,
) -> tuple[bool, str | None]:
    """Open first question of explicitly selected free block."""
    with get_connection() as conn:
        route = get_route_by_id(conn, route_id=route_id)
        if route is None or int(route.get("is_active") or 0) != 1:
            return False, route_stale_session_alert(language)
        block = get_question_block_by_id(conn, route_id=route_id, block_id=block_id)
        if block is None:
            return False, route_stale_session_alert(language)
        questions = list_active_questions_for_block(
            conn,
            route_id=route_id,
            block_id=block_id,
        )
        if not questions:
            return False, route_no_questions_alert(language)
        first_question_number = int(questions[0]["question_number"])
        deactivate_active_route_sessions(conn, user_id=user_id)
        upsert_route_questions_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            selected_block_id=block_id,
            current_question_number=first_question_number,
            show_ru_translation=0,
            entry_mode=_ENTRY_MODE_FREE_QUESTIONS,
            is_active_session=1,
        )

    rendered = await _render_route_question(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        block_id=block_id,
        question_number=first_question_number,
        show_ru_translation=False,
        entry_mode=_ENTRY_MODE_FREE_QUESTIONS,
        resend_media=True,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None


async def open_route_questions_from_briefing(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    """Open free question-block list from briefing."""
    return await show_route_question_blocks_list(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        page=1,
    )


async def open_route_questions_from_news(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    """Open questions after news: random for full, selectable blocks for free."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_NEWS},
        ):
            return False, route_stale_session_alert(language)
        entry_mode = _state_entry_mode(state)
    if entry_mode == _ENTRY_MODE_FULL:
        return await _open_questions_flow(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            language=language,
            route_id=route_id,
            entry_mode=_ENTRY_MODE_FULL,
        )
    return await show_route_question_blocks_list(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        page=1,
    )


async def return_to_question_blocks_list(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    """Return from free questions detail to selectable blocks list."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if (
            state is not None
            and int(state.get("is_active_session") or 0) == 1
            and _is_full_entry_mode(state)
        ):
            return False, route_stale_session_alert(language)
    return await show_route_question_blocks_list(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        page=1,
    )


async def _render_route_question(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    block_id: int,
    question_number: int,
    show_ru_translation: bool,
    entry_mode: str,
    resend_media: bool,
) -> bool:
    lang = normalize_language(language)
    with get_connection() as conn:
        route = get_route_by_id(conn, route_id=route_id)
        block = get_question_block_by_id(conn, route_id=route_id, block_id=block_id)
        question = get_route_question(
            conn,
            route_id=route_id,
            block_id=block_id,
            question_number=question_number,
        )
        questions = list_active_questions_for_block(
            conn,
            route_id=route_id,
            block_id=block_id,
        )
    if question is None or not questions:
        return False

    question_numbers = [int(item["question_number"]) for item in questions]
    if question_number not in question_numbers:
        return False
    current_index = question_numbers.index(question_number) + 1
    total_questions = len(question_numbers)
    has_previous = current_index > 1
    has_next = current_index < total_questions
    translation_text = _resolve_question_translation_text(question)
    allow_translation_toggle = normalize_language(lang) == "ru" and bool(translation_text)
    show_translation = show_ru_translation and allow_translation_toggle
    route_code = str((route or {}).get("code") or "").strip() or None
    block_code = str((block or {}).get("block_code") or "").strip() or None
    question_image_content_key = _build_route_question_image_content_key(
        route_code,
        block_code,
        question_number,
    )

    media_sent = False
    if resend_media:
        await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
        media_sent = await _send_route_media_before_ui_best_effort(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            image_file=str(question.get("image_file") or "").strip() or None,
            image_content_type=_MEDIA_CONTENT_TYPE_ROUTE_QUESTION_IMAGE,
            image_content_key=question_image_content_key,
            audio_file=None,
            audio_content_type=None,
            audio_content_key=None,
        )

    await _render_route_main_ui(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        text=route_questions_screen_text(
            lang,
            current_index=current_index,
            total_questions=total_questions,
            question_en=str(question.get("question_en") or "").strip(),
            show_ru_translation=show_translation,
            question_translation_ru=translation_text,
        ),
        reply_markup=build_route_questions_keyboard(
            lang,
            route_id=route_id,
            question_number=question_number,
            has_previous=has_previous,
            has_next=has_next,
            has_ru_translation=allow_translation_toggle,
            show_ru_translation=show_translation,
            is_full_mode=(entry_mode == _ENTRY_MODE_FULL),
            show_to_blocks=(entry_mode == _ENTRY_MODE_FREE_QUESTIONS),
        ),
        media_sent=media_sent,
    )
    return True


async def _open_questions_flow(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    entry_mode: str,
) -> tuple[bool, str | None]:
    with get_connection() as conn:
        picked = _pick_random_active_question_block(conn, route_id=route_id)
        if picked is None:
            return False, route_no_questions_alert(language)
        block, questions = picked
        first_question_number = int(questions[0]["question_number"])
        upsert_route_questions_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            selected_block_id=int(block["id"]),
            current_question_number=first_question_number,
            show_ru_translation=0,
            entry_mode=entry_mode,
            is_active_session=1,
        )

    rendered = await _render_route_question(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        block_id=int(block["id"]),
        question_number=first_question_number,
        show_ru_translation=False,
        entry_mode=entry_mode,
        resend_media=True,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None


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
    """Move route question pointer (back/next) and reset RU translation toggle."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_QUESTIONS},
        ):
            return False, route_stale_session_alert(language)
        block_id = int(state.get("selected_block_id") or 0)
        current_question_number = int(state.get("current_question_number") or 0)
        if block_id <= 0 or current_question_number <= 0:
            return False, route_stale_session_alert(language)
        if current_question_number != callback_question_number:
            return False, route_stale_session_alert(language)
        if direction == "next":
            target_question_number = get_next_question_number(
                conn,
                route_id=route_id,
                block_id=block_id,
                current_question_number=current_question_number,
            )
        elif direction == "back":
            target_question_number = get_previous_question_number(
                conn,
                route_id=route_id,
                block_id=block_id,
                current_question_number=current_question_number,
            )
        else:
            return False, route_stale_session_alert(language)
        if target_question_number is None:
            return False, route_stale_session_alert(language)
        update_route_question_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            current_question_number=target_question_number,
            show_ru_translation=0,
        )

    rendered = await _render_route_question(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        block_id=block_id,
        question_number=target_question_number,
        show_ru_translation=False,
        entry_mode=_state_entry_mode(state),
        resend_media=True,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None


async def toggle_route_question_translation(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_question_number: int,
) -> tuple[bool, str | None]:
    """Toggle RU question translation in questions phase."""
    if normalize_language(language) != "ru":
        return False, route_stale_session_alert(language)

    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_QUESTIONS},
        ):
            return False, route_stale_session_alert(language)
        block_id = int(state.get("selected_block_id") or 0)
        current_question_number = int(state.get("current_question_number") or 0)
        if block_id <= 0 or current_question_number <= 0:
            return False, route_stale_session_alert(language)
        if current_question_number != callback_question_number:
            return False, route_stale_session_alert(language)
        question = get_route_question(
            conn,
            route_id=route_id,
            block_id=block_id,
            question_number=current_question_number,
        )
        if question is None or not _resolve_question_translation_text(question):
            return False, route_stale_session_alert(language)
        next_show_translation = 0 if int(state.get("show_ru_translation") or 0) == 1 else 1
        update_route_question_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            current_question_number=current_question_number,
            show_ru_translation=next_show_translation,
        )

    rendered = await _render_route_question(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        block_id=block_id,
        question_number=current_question_number,
        show_ru_translation=bool(next_show_translation),
        entry_mode=_state_entry_mode(state),
        resend_media=False,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None


async def finish_route_questions(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    callback_question_number: int,
) -> tuple[bool, str | None]:
    """Finish route questions and render full/free completion result."""
    lang = normalize_language(language)
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_QUESTIONS},
        ):
            return False, route_stale_session_alert(language)
        block_id = int(state.get("selected_block_id") or 0)
        current_question_number = int(state.get("current_question_number") or 0)
        if block_id <= 0 or current_question_number <= 0:
            return False, route_stale_session_alert(language)
        if current_question_number != callback_question_number:
            return False, route_stale_session_alert(language)

        next_question = get_next_question_number(
            conn,
            route_id=route_id,
            block_id=block_id,
            current_question_number=current_question_number,
        )
        if next_question is not None:
            return False, route_stale_session_alert(language)

        route = get_route_by_id(conn, route_id=route_id)
        if route is None:
            return False, route_stale_session_alert(language)
        entry_mode = _state_entry_mode(state)
        clear_route_user_state(conn, user_id=user_id, route_id=route_id)
        if entry_mode == _ENTRY_MODE_FULL:
            mark_route_completed(conn, user_id=user_id, route_id=route_id)
            completion_text = route_full_completion_text(
                lang,
                route_title=_resolve_route_title(route, language=lang),
            )
        else:
            completion_text = route_free_completion_text(lang)

    await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=completion_text,
        reply_markup=build_route_completion_keyboard(lang),
        parse_mode="HTML",
    )
    return True, None
