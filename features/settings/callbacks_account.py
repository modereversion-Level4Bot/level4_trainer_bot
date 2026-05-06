"""Account-related callbacks for Settings."""

from __future__ import annotations

from telegram import CallbackQuery, Chat, User
from telegram.ext import ContextTypes

from core.safe_telegram import safe_answer_callback
from features.settings.account_service import (
    _apply_progress_reset,
    _complete_delete_account,
    _complete_restart_onboarding,
    _show_delete_account_confirm_screen,
    _show_delete_account_screen,
    _show_reset_confirm_screen,
    _show_reset_progress_screen,
    _show_restart_onboarding_screen,
)
from features.settings.keyboards import (
    CB_SETTINGS_DELETE_ACCOUNT,
    CB_SETTINGS_DELETE_CANCEL,
    CB_SETTINGS_DELETE_CONFIRM,
    CB_SETTINGS_DELETE_CONTINUE,
    CB_SETTINGS_RESET_BACK,
    CB_SETTINGS_RESET_CANCEL,
    CB_SETTINGS_RESET_CONFIRM_PREFIX,
    CB_SETTINGS_RESET_PROGRESS,
    CB_SETTINGS_RESTART_CANCEL,
    CB_SETTINGS_RESTART_CONFIRM,
    CB_SETTINGS_RESTART_ONBOARDING,
    RESET_TARGET_BY_CALLBACK,
)
from features.settings.sections_service import (
    SettingsState,
    _is_admin,
    _load_state_by_user_id,
    _show_settings_account_section,
)
from features.settings.texts import alert_admin_delete_forbidden, toast_progress_reset


async def handle_account_callbacks(
    *,
    callback_data: str,
    query: CallbackQuery,
    user: User,
    chat: Chat,
    state: SettingsState,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Handle account/reset/restart/delete callback branches."""
    if callback_data == CB_SETTINGS_RESET_PROGRESS:
        await safe_answer_callback(query)
        await _show_reset_progress_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_RESET_BACK:
        await safe_answer_callback(query)
        await _show_settings_account_section(
            bot=context.bot,
            chat_id=chat.id,
            state=state,
            telegram_id=user.id,
        )
        return True

    if callback_data in RESET_TARGET_BY_CALLBACK:
        target = RESET_TARGET_BY_CALLBACK[callback_data]
        await safe_answer_callback(query)
        await _show_reset_confirm_screen(bot=context.bot, chat_id=chat.id, state=state, target=target)
        return True

    if callback_data.startswith(CB_SETTINGS_RESET_CONFIRM_PREFIX):
        target = callback_data.removeprefix(CB_SETTINGS_RESET_CONFIRM_PREFIX)
        if target not in {"grammar", "questions", "routes", "all"}:
            await safe_answer_callback(query)
            return True
        await _apply_progress_reset(
            bot=context.bot,
            chat_id=chat.id,
            user_id=state.user_id,
            target=target,
        )
        await safe_answer_callback(
            query,
            text=toast_progress_reset(state.ui_language),
            show_alert=False,
        )
        refreshed = _load_state_by_user_id(state.user_id)
        if refreshed is not None:
            await _show_settings_account_section(
                bot=context.bot,
                chat_id=chat.id,
                state=refreshed,
                telegram_id=user.id,
            )
        return True

    if callback_data == CB_SETTINGS_RESET_CANCEL:
        await safe_answer_callback(query)
        await _show_reset_progress_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_RESTART_ONBOARDING:
        await safe_answer_callback(query)
        await _show_restart_onboarding_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_RESTART_CANCEL:
        await safe_answer_callback(query)
        await _show_settings_account_section(
            bot=context.bot,
            chat_id=chat.id,
            state=state,
            telegram_id=user.id,
        )
        return True

    if callback_data == CB_SETTINGS_RESTART_CONFIRM:
        await safe_answer_callback(query)
        await _complete_restart_onboarding(
            bot=context.bot,
            chat_id=chat.id,
            state=state,
            telegram_id=user.id,
        )
        return True

    if callback_data == CB_SETTINGS_DELETE_ACCOUNT:
        if _is_admin(state.telegram_id):
            await safe_answer_callback(
                query,
                text=alert_admin_delete_forbidden(state.ui_language),
                show_alert=True,
            )
            return True
        await safe_answer_callback(query)
        await _show_delete_account_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_DELETE_CONTINUE:
        if _is_admin(state.telegram_id):
            await safe_answer_callback(
                query,
                text=alert_admin_delete_forbidden(state.ui_language),
                show_alert=True,
            )
            return True
        await safe_answer_callback(query)
        await _show_delete_account_confirm_screen(bot=context.bot, chat_id=chat.id, state=state)
        return True

    if callback_data == CB_SETTINGS_DELETE_CANCEL:
        await safe_answer_callback(query)
        await _show_settings_account_section(
            bot=context.bot,
            chat_id=chat.id,
            state=state,
            telegram_id=user.id,
        )
        return True

    if callback_data == CB_SETTINGS_DELETE_CONFIRM:
        if _is_admin(state.telegram_id):
            await safe_answer_callback(
                query,
                text=alert_admin_delete_forbidden(state.ui_language),
                show_alert=True,
            )
            return True
        await safe_answer_callback(query)
        await _complete_delete_account(bot=context.bot, chat_id=chat.id, state=state)
        return True

    return False
