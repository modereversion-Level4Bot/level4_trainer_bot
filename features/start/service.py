"""Service helpers for /start flow."""

from __future__ import annotations

from telegram import Bot

from core.message_stack import load_stack, save_stack
from core.safe_telegram import safe_delete_message
from db.connection import get_connection
from db.repositories.deleted_account_cleanup_repo import (
    delete_deleted_account_cleanup,
    get_deleted_account_cleanup_message_id,
)
from db.repositories.users_repo import get_user_with_onboarding_by_user_id
from features.main_menu.service import show_main_menu
from features.onboarding.service import ensure_initial_language, show_current_onboarding_screen


async def _cleanup_deleted_account_main_ui(
    *,
    bot: Bot,
    chat_id: int,
    user_id: int,
    telegram_id: int,
) -> None:
    """Remove or reuse stale 'account deleted' UI before normal /start flow."""
    with get_connection() as conn:
        cleanup_message_id = get_deleted_account_cleanup_message_id(
            conn,
            telegram_id=telegram_id,
            chat_id=chat_id,
        )
    if cleanup_message_id is None:
        return

    deleted = await safe_delete_message(
        bot=bot,
        chat_id=chat_id,
        message_id=cleanup_message_id,
    )
    if not deleted:
        # Reuse stale message as the next main UI target (edit-first strategy).
        stack = load_stack(user_id)
        stack.main_ui_message_id = cleanup_message_id
        save_stack(user_id=user_id, stack=stack)

    with get_connection() as conn:
        delete_deleted_account_cleanup(
            conn,
            telegram_id=telegram_id,
            chat_id=chat_id,
        )


async def handle_start_flow(
    bot: Bot,
    chat_id: int,
    user_id: int,
    telegram_id: int,
    telegram_language_code: str | None,
) -> None:
    """Route /start either to onboarding or main menu."""
    await _cleanup_deleted_account_main_ui(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        telegram_id=telegram_id,
    )

    with get_connection() as conn:
        row = get_user_with_onboarding_by_user_id(conn, user_id)

    if row is None:
        return

    onboarding_completed = bool(row["onboarding_completed"])
    if onboarding_completed:
        await show_main_menu(
            bot=bot,
            chat_id=chat_id,
            user_id=user_id,
            telegram_id=telegram_id,
        )
        return

    _ = ensure_initial_language(
        user_id=user_id,
        telegram_language_code=telegram_language_code,
    )

    await show_current_onboarding_screen(
        bot=bot,
        chat_id=chat_id,
        user_id=user_id,
        telegram_id=telegram_id,
    )
