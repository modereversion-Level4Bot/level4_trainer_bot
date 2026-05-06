"""Account-related Settings flows."""

from __future__ import annotations

from telegram import Bot

from core.message_stack import load_stack
from db.connection import get_connection
from db.repositories.deleted_account_cleanup_repo import upsert_deleted_account_cleanup
from db.repositories.progress_repo import (
    reset_all_progress,
    reset_grammar_progress,
    reset_questions_progress,
    reset_routes_progress,
)
from db.repositories.settings_repo import restart_onboarding
from db.repositories.users_repo import delete_user_account
from features.onboarding.service import show_current_onboarding_screen
from features.questions.audio_service import cleanup_questions_audio
from features.settings.keyboards import (
    build_settings_delete_account_confirm_keyboard,
    build_settings_delete_account_keyboard,
    build_settings_reset_confirm_keyboard,
    build_settings_reset_progress_keyboard,
    build_settings_restart_keyboard,
)
from features.settings.sections_service import SettingsState, _render_settings_screen
from features.settings.texts import (
    ResetTarget,
    settings_account_deleted_screen,
    settings_delete_account_confirm_screen,
    settings_delete_account_screen,
    settings_reset_confirm_screen,
    settings_reset_progress_screen,
    settings_restart_onboarding_screen,
)


async def _show_reset_progress_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_reset_progress_screen(state.ui_language),
        reply_markup=build_settings_reset_progress_keyboard(state.ui_language),
    )


async def _show_reset_confirm_screen(
    bot: Bot,
    chat_id: int,
    state: SettingsState,
    target: ResetTarget,
) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_reset_confirm_screen(state.ui_language, target),
        reply_markup=build_settings_reset_confirm_keyboard(state.ui_language, target),
    )


async def _show_restart_onboarding_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_restart_onboarding_screen(state.ui_language),
        reply_markup=build_settings_restart_keyboard(state.ui_language),
    )


async def _show_delete_account_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_delete_account_screen(state.ui_language),
        reply_markup=build_settings_delete_account_keyboard(state.ui_language),
    )


async def _show_delete_account_confirm_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_delete_account_confirm_screen(state.ui_language),
        reply_markup=build_settings_delete_account_confirm_keyboard(state.ui_language),
    )


async def _show_account_deleted_screen(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _render_settings_screen(
        bot=bot,
        chat_id=chat_id,
        state=state,
        text=settings_account_deleted_screen(state.ui_language),
        reply_markup=None,
    )


async def _apply_progress_reset(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    target: str,
) -> None:
    if target in {"questions", "all"}:
        await cleanup_questions_audio(
            bot,
            user_id=user_id,
            chat_id=chat_id,
        )

    with get_connection() as conn:
        if target == "grammar":
            reset_grammar_progress(conn, user_id)
        elif target == "questions":
            reset_questions_progress(conn, user_id)
        elif target == "routes":
            reset_routes_progress(conn, user_id)
        else:
            reset_all_progress(conn, user_id)


async def _complete_restart_onboarding(
    bot: Bot,
    chat_id: int,
    state: SettingsState,
    *,
    telegram_id: int,
) -> None:
    with get_connection() as conn:
        restart_onboarding(conn, state.user_id)
    await show_current_onboarding_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=state.user_id,
        telegram_id=telegram_id,
    )


async def _complete_delete_account(bot: Bot, chat_id: int, state: SettingsState) -> None:
    await _show_account_deleted_screen(bot=bot, chat_id=chat_id, state=state)
    stack = load_stack(state.user_id)
    cleanup_message_id = stack.main_ui_message_id
    with get_connection() as conn:
        if cleanup_message_id is not None:
            upsert_deleted_account_cleanup(
                conn,
                telegram_id=state.telegram_id,
                chat_id=chat_id,
                message_id=cleanup_message_id,
            )
        _ = delete_user_account(conn, state.user_id)
