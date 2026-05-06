"""Guard chain skeleton for update access control."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import get_settings
from core.constants import ADMIN_ONLY_TEXT, BLOCKED_USER_TEXT, MAINTENANCE_TEXT
from core.safe_telegram import safe_send_message
from db.connection import get_connection
from db.repositories.settings_repo import is_maintenance_mode
from db.repositories.users_repo import get_user_by_telegram_id, upsert_user


logger = logging.getLogger(__name__)


def _get_chat_id(update: Update) -> int | None:
    if update.effective_chat:
        return update.effective_chat.id
    return None


def _is_admin(telegram_user_id: int) -> bool:
    settings = get_settings()
    return telegram_user_id in settings.admin_ids


async def _safe_notify(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    chat_id = _get_chat_id(update)
    if chat_id is None:
        return
    await safe_send_message(bot=context.bot, chat_id=chat_id, text=text)


async def update_last_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Update user last activity timestamp if user already exists."""
    _ = context  # reserved for future context-driven guard extensions

    telegram_user = update.effective_user
    if telegram_user is None:
        return False

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE users
            SET last_activity_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (telegram_user.id,),
        )
    return True


async def ensure_user_exists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Create or update user row for every incoming update."""
    _ = context

    telegram_user = update.effective_user
    if telegram_user is None:
        return False

    with get_connection() as conn:
        upsert_user(conn, telegram_user)
    return True


async def check_admin_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    First guard priority: blocked users are denied immediately.

    Blocked users should not see maintenance messages.
    """
    telegram_user = update.effective_user
    if telegram_user is None:
        return False

    with get_connection() as conn:
        user_row = get_user_by_telegram_id(conn, telegram_user.id)

    is_blocked = bool(user_row["is_blocked"]) if user_row is not None else False
    if not is_blocked:
        return True

    await _safe_notify(update, context, BLOCKED_USER_TEXT)
    logger.info("Blocked user %s attempted to interact.", telegram_user.id)
    return False


async def check_maintenance_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Second guard priority: maintenance gate.

    Admins are still allowed during maintenance.
    """
    telegram_user = update.effective_user
    if telegram_user is None:
        return False

    with get_connection() as conn:
        maintenance_enabled = is_maintenance_mode(conn)

    if not maintenance_enabled:
        return True
    if _is_admin(telegram_user.id):
        return True

    await _safe_notify(update, context, MAINTENANCE_TEXT)
    return False


async def check_admin_rights(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Ensure user has admin rights for admin-only actions."""
    telegram_user = update.effective_user
    if telegram_user is None:
        return False

    if _is_admin(telegram_user.id):
        return True

    await _safe_notify(update, context, ADMIN_ONLY_TEXT)
    return False


async def run_guard_chain(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    require_admin: bool = False,
) -> bool:
    """Run base guard chain in required priority order."""
    await ensure_user_exists(update, context)
    await update_last_activity(update, context)

    if not await check_admin_block(update, context):
        return False
    if not await check_maintenance_mode(update, context):
        return False
    if require_admin and not await check_admin_rights(update, context):
        return False
    return True
