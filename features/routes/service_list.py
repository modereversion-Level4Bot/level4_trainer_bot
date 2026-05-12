"""Routes list/briefing helpers for routes service."""

from __future__ import annotations

from telegram import Bot

from core.message_stack import render_main_ui, replace_main_ui
from db.connection import get_connection
from db.repositories.routes_repo import (
    clear_route_user_state,
    count_active_routes,
    count_completed_routes,
    get_route_by_id,
    get_route_user_state,
    list_active_routes,
)
from features.routes.keyboards import (
    build_route_briefing_keyboard,
    build_routes_empty_keyboard,
    build_routes_list_keyboard,
)
from features.routes.service_media import (
    _MEDIA_CONTENT_TYPE_ROUTE_BRIEFING_IMAGE,
    _build_route_briefing_image_content_key,
    _send_route_media_before_ui_best_effort,
    cleanup_routes_temp_images,
)
from features.routes.service_session import _is_full_entry_mode
from features.routes.texts import (
    normalize_language,
    route_briefing_text,
    route_stale_session_alert,
    routes_empty_text,
    routes_list_text,
)


_ROUTES_PER_PAGE = 4


def _safe_total_pages(total_routes: int) -> int:
    if total_routes <= 0:
        return 1
    return ((total_routes - 1) // _ROUTES_PER_PAGE) + 1


def _normalize_page(page: int, *, total_pages: int) -> int:
    normalized_page = int(page)
    if normalized_page < 1:
        return 1
    if normalized_page > total_pages:
        return total_pages
    return normalized_page


def _resolve_route_title(route: dict[str, object], *, language: str) -> str:
    if normalize_language(language) == "ru":
        title_ru = str(route.get("title_ru") or "").strip()
        if title_ru:
            return title_ru
    title_en = str(route.get("title_en") or "").strip()
    if title_en:
        return title_en
    title_ru = str(route.get("title_ru") or "").strip()
    if title_ru:
        return title_ru
    return str(route.get("title") or "").strip() or f"Route #{route.get('id')}"


def _resolve_route_briefing(route: dict[str, object], *, language: str) -> str:
    if normalize_language(language) == "ru":
        briefing_ru = str(route.get("briefing_ru") or "").strip()
        if briefing_ru:
            return briefing_ru
    briefing_en = str(route.get("briefing_en") or "").strip()
    if briefing_en:
        return briefing_en
    briefing_ru = str(route.get("briefing_ru") or "").strip()
    if briefing_ru:
        return briefing_ru
    return ""


async def _render_route_main_ui(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    text: str,
    reply_markup,
    media_sent: bool,
) -> None:
    # When route media is sent first (image now, audio in future), we replace
    # main UI so the final visual order stays: media -> text/buttons.
    if media_sent:
        await replace_main_ui(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


async def show_routes_list(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    page: int,
) -> None:
    """Render routes list screen with pagination."""
    lang = normalize_language(language)
    await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
    with get_connection() as conn:
        total_routes = count_active_routes(conn)
        completed_routes = count_completed_routes(conn, user_id=user_id)
        total_pages = _safe_total_pages(total_routes)
        safe_page = _normalize_page(page, total_pages=total_pages)
        if total_routes <= 0:
            await render_main_ui(
                bot=bot,
                chat_id=chat_id,
                user_id=user_id,
                text=routes_empty_text(lang),
                reply_markup=build_routes_empty_keyboard(lang),
                parse_mode="HTML",
            )
            return

        offset = (safe_page - 1) * _ROUTES_PER_PAGE
        routes = list_active_routes(conn, limit=_ROUTES_PER_PAGE, offset=offset)

    route_buttons = [
        (int(route["id"]), _resolve_route_title(route, language=lang))
        for route in routes
    ]
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=routes_list_text(
            lang,
            completed=completed_routes,
            total=total_routes,
            page=safe_page,
            total_pages=total_pages,
        ),
        reply_markup=build_routes_list_keyboard(
            lang,
            route_buttons=route_buttons,
            page=safe_page,
            total_pages=total_pages,
        ),
        parse_mode="HTML",
    )


async def show_route_briefing(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
    page: int,
) -> bool:
    """Render one route briefing. Returns False if route is unavailable."""
    lang = normalize_language(language)
    await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
    with get_connection() as conn:
        route = get_route_by_id(conn, route_id=route_id)
    if route is None or int(route.get("is_active") or 0) != 1:
        return False

    briefing = _resolve_route_briefing(route, language=lang)
    if not briefing:
        return False
    route_code = str(route.get("code") or "").strip() or None
    briefing_image_content_key = _build_route_briefing_image_content_key(route_code)

    media_sent = await _send_route_media_before_ui_best_effort(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        image_file=str(route.get("image_file") or "").strip() or None,
        image_content_type=_MEDIA_CONTENT_TYPE_ROUTE_BRIEFING_IMAGE,
        image_content_key=briefing_image_content_key,
        audio_file=None,
        audio_content_type=None,
        audio_content_key=None,
    )
    await _render_route_main_ui(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        text=route_briefing_text(lang, briefing_text=briefing),
        reply_markup=build_route_briefing_keyboard(
            lang,
            route_id=int(route["id"]),
            page=max(1, int(page)),
        ),
        media_sent=media_sent,
    )
    return True


async def return_to_route_briefing(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    """Return from free news/questions flow back to route briefing."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if (
            state is not None
            and int(state.get("is_active_session") or 0) == 1
            and _is_full_entry_mode(state)
        ):
            return False, route_stale_session_alert(language)
        if state is not None:
            clear_route_user_state(conn, user_id=user_id, route_id=route_id)

    shown = await show_route_briefing(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        language=language,
        route_id=route_id,
        page=1,
    )
    if not shown:
        return False, route_stale_session_alert(language)
    return True, None
