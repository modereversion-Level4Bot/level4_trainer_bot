"""News helpers for routes service."""

from __future__ import annotations

from telegram import Bot

from core.message_stack import render_main_ui
from db.connection import get_connection
from db.repositories.routes_repo import (
    count_active_news_for_route,
    deactivate_active_route_sessions,
    get_route_by_id,
    get_route_news_by_id,
    get_route_user_state,
    list_active_news_for_route_paginated,
    update_route_news_transcript_state,
    upsert_route_news_state,
)
from features.routes.keyboards import (
    build_route_news_keyboard,
    build_route_news_list_keyboard,
)
from features.routes.service_list import (
    _normalize_page,
    _render_route_main_ui,
    _safe_total_pages,
)
from features.routes.service_media import (
    _MEDIA_CONTENT_TYPE_ROUTE_NEWS_AUDIO,
    _MEDIA_CONTENT_TYPE_ROUTE_NEWS_IMAGE,
    _build_route_news_audio_content_key,
    _build_route_news_image_content_key,
    _send_route_media_before_ui_best_effort,
    cleanup_routes_temp_images,
)
from features.routes.service_session import (
    _ENTRY_MODE_FREE_NEWS,
    _ENTRY_MODE_FULL,
    _PHASE_NEWS,
    _is_state_active_for_route,
    _state_entry_mode,
)
from features.routes.texts import (
    normalize_language,
    route_news_list_text,
    route_news_text,
    route_no_news_alert,
    route_stale_session_alert,
)


_ROUTES_PER_PAGE = 4


def _resolve_news_transcript_text(news: dict[str, object], *, language: str) -> str | None:
    if normalize_language(language) == "ru":
        transcript_ru = str(news.get("transcript_ru") or "").strip()
        if transcript_ru:
            return transcript_ru
    transcript_en = str(news.get("transcript_en") or "").strip()
    if transcript_en:
        return transcript_en
    transcript_ru = str(news.get("transcript_ru") or "").strip()
    if transcript_ru:
        return transcript_ru
    return None


async def show_route_news_list(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    page: int,
) -> tuple[bool, str | None]:
    """Render selectable news list for free mode."""
    lang = normalize_language(language)
    await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
    with get_connection() as conn:
        route = get_route_by_id(conn, route_id=route_id)
        if route is None or int(route.get("is_active") or 0) != 1:
            return False, route_stale_session_alert(language)
        total_news = count_active_news_for_route(conn, route_id=route_id)
        if total_news <= 0:
            return False, route_no_news_alert(language)
        total_pages = _safe_total_pages(total_news)
        safe_page = _normalize_page(page, total_pages=total_pages)
        offset = (safe_page - 1) * _ROUTES_PER_PAGE
        news_rows = list_active_news_for_route_paginated(
            conn,
            route_id=route_id,
            limit=_ROUTES_PER_PAGE,
            offset=offset,
        )

    news_buttons = [
        (int(item["id"]), int(item.get("news_order") or 0))
        for item in news_rows
    ]
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=route_news_list_text(lang),
        reply_markup=build_route_news_list_keyboard(
            lang,
            route_id=route_id,
            news_buttons=news_buttons,
            page=safe_page,
            total_pages=total_pages,
        ),
        parse_mode="HTML",
    )
    return True, None


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
    """Open selected news item from free news list."""
    with get_connection() as conn:
        route = get_route_by_id(conn, route_id=route_id)
        if route is None or int(route.get("is_active") or 0) != 1:
            return False, route_stale_session_alert(language)
        news = get_route_news_by_id(conn, route_id=route_id, news_id=news_id)
        if news is None:
            return False, route_stale_session_alert(language)
        deactivate_active_route_sessions(conn, user_id=user_id)
        upsert_route_news_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            selected_news_id=news_id,
            show_transcript=0,
            entry_mode=_ENTRY_MODE_FREE_NEWS,
            is_active_session=1,
        )

    rendered = await _render_route_news(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        news_id=news_id,
        show_transcript=False,
        entry_mode=_ENTRY_MODE_FREE_NEWS,
        news_list_page=page,
        resend_media=True,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None


async def _render_route_news(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    news_id: int,
    show_transcript: bool,
    entry_mode: str,
    news_list_page: int | None,
    resend_media: bool,
) -> bool:
    lang = normalize_language(language)
    with get_connection() as conn:
        news = get_route_news_by_id(conn, route_id=route_id, news_id=news_id)
        route = get_route_by_id(conn, route_id=route_id)
    if news is None:
        return False
    route_code = str((route or {}).get("code") or "").strip() or None
    news_code = str(news.get("news_code") or "").strip() or None
    news_image_content_key = _build_route_news_image_content_key(route_code, news_code)
    news_audio_content_key = _build_route_news_audio_content_key(route_code, news_code)

    media_sent = False
    if resend_media:
        await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
        media_sent = await _send_route_media_before_ui_best_effort(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            image_file=str(news.get("image_file") or "").strip() or None,
            image_content_type=_MEDIA_CONTENT_TYPE_ROUTE_NEWS_IMAGE,
            image_content_key=news_image_content_key,
            audio_file=str(news.get("audio_file") or "").strip() or None,
            audio_content_type=_MEDIA_CONTENT_TYPE_ROUTE_NEWS_AUDIO,
            audio_content_key=news_audio_content_key,
        )

    transcript_text = _resolve_news_transcript_text(news, language=lang)
    await _render_route_main_ui(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        text=route_news_text(
            lang,
            transcript_text=transcript_text,
            show_transcript=show_transcript,
        ),
        reply_markup=build_route_news_keyboard(
            lang,
            route_id=route_id,
            has_transcript=bool(transcript_text),
            transcript_open=show_transcript,
            is_full_mode=(entry_mode == _ENTRY_MODE_FULL),
            news_list_page=news_list_page,
        ),
        media_sent=media_sent,
    )
    return True


async def open_route_news_from_briefing(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    """Open free news list from briefing."""
    return await show_route_news_list(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        page=1,
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
    """Toggle news transcript block visibility."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_NEWS},
        ):
            return False, route_stale_session_alert(language)
        news_id = int(state.get("selected_news_id") or 0)
        if news_id <= 0:
            return False, route_stale_session_alert(language)
        next_show_transcript = 0 if int(state.get("show_transcript") or 0) == 1 else 1
        update_route_news_transcript_state(
            conn,
            user_id=user_id,
            route_id=route_id,
            show_transcript=next_show_transcript,
        )

    rendered = await _render_route_news(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        news_id=news_id,
        show_transcript=bool(next_show_transcript),
        entry_mode=_state_entry_mode(state),
        news_list_page=news_list_page,
        resend_media=False,
    )
    if not rendered:
        return False, route_stale_session_alert(language)
    return True, None
