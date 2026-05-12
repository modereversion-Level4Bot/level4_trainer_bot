"""Interrupt/home-confirm helpers for routes service."""

from __future__ import annotations

from telegram import Bot

from core.message_stack import render_main_ui
from db.connection import get_connection
from db.repositories.routes_repo import (
    clear_route_user_state,
    deactivate_active_route_sessions,
    get_route_user_state,
)
from features.main_menu.service import show_main_menu
from features.routes.keyboards import build_route_interrupt_keyboard
from features.routes.service_media import cleanup_routes_temp_images
from features.routes.service_session import (
    _PHASE_NEWS,
    _PHASE_QUESTIONS,
    _PHASE_SCENARIO,
    _is_full_entry_mode,
    _is_state_active_for_route,
)
from features.routes.texts import (
    normalize_language,
    route_interrupt_text,
    route_stale_session_alert,
)


async def show_route_interrupt_confirmation(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    telegram_id: int,
    language: str,
    route_id: int,
) -> tuple[bool, str | None]:
    """Handle main menu request from active routes flow."""
    should_return_home = False
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_SCENARIO, _PHASE_NEWS, _PHASE_QUESTIONS},
        ):
            return False, route_stale_session_alert(language)

        if not _is_full_entry_mode(state):
            clear_route_user_state(conn, user_id=user_id, route_id=route_id)
            should_return_home = True

    if should_return_home:
        await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
        await show_main_menu(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            telegram_id=telegram_id,
        )
        return True, None

    lang = normalize_language(language)
    await render_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        text=route_interrupt_text(lang),
        reply_markup=build_route_interrupt_keyboard(lang, route_id=route_id),
        parse_mode="HTML",
    )
    return True, None


async def route_interrupt_confirm(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    telegram_id: int,
    route_id: int,
) -> tuple[bool, str | None]:
    """Confirm scenario interrupt and return to main menu."""
    with get_connection() as conn:
        state = get_route_user_state(conn, user_id=user_id, route_id=route_id)
        if not _is_state_active_for_route(
            state,
            route_id=route_id,
            allowed_phases={_PHASE_SCENARIO, _PHASE_NEWS, _PHASE_QUESTIONS},
        ):
            return False, None
        clear_route_user_state(conn, user_id=user_id, route_id=route_id)
    await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
    await show_main_menu(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        telegram_id=telegram_id,
    )
    return True, None


async def routes_go_home(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    telegram_id: int,
) -> None:
    """Navigate back to main menu from routes feature."""
    with get_connection() as conn:
        deactivate_active_route_sessions(conn, user_id=user_id)
    await cleanup_routes_temp_images(bot, user_id=user_id, chat_id=chat_id)
    await show_main_menu(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        telegram_id=telegram_id,
    )
