"""Main message stack primitives for clean-chat architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
from typing import Any

from telegram import Bot, Message

from core.safe_telegram import safe_delete_message, safe_edit_message, safe_send_message
from db.connection import get_connection


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MessageStack:
    """Stored message IDs for one user."""

    main_ui_message_id: int | None = None
    ad_message_id: int | None = None
    announcement_message_ids: list[int] = field(default_factory=list)
    temporary_media_message_ids: list[int] = field(default_factory=list)
    service_layer_message_ids: list[int] = field(default_factory=list)


def _safe_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []
    return [int(item) for item in data if isinstance(item, int)]


def _dump_list(values: list[int]) -> str:
    return json.dumps(values)


def _ensure_stack_row_exists(conn, user_id: int) -> None:
    conn.execute(
        """
        INSERT INTO user_message_state (user_id)
        VALUES (?)
        ON CONFLICT(user_id) DO NOTHING
        """,
        (user_id,),
    )


def load_stack(user_id: int) -> MessageStack:
    """Load user message stack from DB."""
    with get_connection() as conn:
        _ensure_stack_row_exists(conn, user_id)
        row = conn.execute(
            """
            SELECT main_ui_message_id, ad_message_id, announcement_message_ids,
                   temporary_media_message_ids, service_layer_message_ids
            FROM user_message_state
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if row is None:
        return MessageStack()

    return MessageStack(
        main_ui_message_id=row["main_ui_message_id"],
        ad_message_id=row["ad_message_id"],
        announcement_message_ids=_safe_list(row["announcement_message_ids"]),
        temporary_media_message_ids=_safe_list(row["temporary_media_message_ids"]),
        service_layer_message_ids=_safe_list(row["service_layer_message_ids"]),
    )


def save_stack(user_id: int, stack: MessageStack) -> None:
    """Persist stack to DB."""
    with get_connection() as conn:
        _ensure_stack_row_exists(conn, user_id)
        conn.execute(
            """
            UPDATE user_message_state
            SET
                main_ui_message_id = ?,
                ad_message_id = ?,
                announcement_message_ids = ?,
                temporary_media_message_ids = ?,
                service_layer_message_ids = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (
                stack.main_ui_message_id,
                stack.ad_message_id,
                _dump_list(stack.announcement_message_ids),
                _dump_list(stack.temporary_media_message_ids),
                _dump_list(stack.service_layer_message_ids),
                user_id,
            ),
        )


async def render_main_ui(
    bot: Bot,
    chat_id: int,
    user_id: int,
    text: str,
    **kwargs: Any,
) -> Message | None:
    """Render one active main UI message with edit-first strategy."""
    stack = load_stack(user_id)
    old_message_id = stack.main_ui_message_id

    if old_message_id is not None:
        edited = await safe_edit_message(
            bot=bot,
            chat_id=chat_id,
            message_id=old_message_id,
            text=text,
            **kwargs,
        )
        if edited is not None:
            return edited if isinstance(edited, Message) else None

    sent = await safe_send_message(
        bot=bot,
        chat_id=chat_id,
        text=text,
        **kwargs,
    )
    if sent is None:
        logger.warning("Failed to render main UI for user_id=%s", user_id)
        return None

    stack.main_ui_message_id = sent.message_id
    save_stack(user_id=user_id, stack=stack)

    if old_message_id is not None and old_message_id != sent.message_id:
        await safe_delete_message(bot=bot, chat_id=chat_id, message_id=old_message_id)

    return sent


def rebuild_user_stack(user_id: int) -> MessageStack:
    """Load and normalize stack values for a user."""
    stack = load_stack(user_id=user_id)
    save_stack(user_id=user_id, stack=stack)
    return stack


async def clear_temporary_media(bot: Bot, chat_id: int, user_id: int) -> None:
    """Delete temporary media layer messages for user."""
    stack = load_stack(user_id)
    for message_id in stack.temporary_media_message_ids:
        await safe_delete_message(bot=bot, chat_id=chat_id, message_id=message_id)
    stack.temporary_media_message_ids = []
    save_stack(user_id=user_id, stack=stack)


async def replace_main_ui(
    bot: Bot,
    chat_id: int,
    user_id: int,
    text: str,
    **kwargs: Any,
) -> Message | None:
    """Replace the only active main UI message."""
    stack = load_stack(user_id)
    if stack.main_ui_message_id is not None:
        await safe_delete_message(
            bot=bot,
            chat_id=chat_id,
            message_id=stack.main_ui_message_id,
        )

    sent = await safe_send_message(
        bot=bot,
        chat_id=chat_id,
        text=text,
        **kwargs,
    )
    if sent is not None:
        stack.main_ui_message_id = sent.message_id
        save_stack(user_id=user_id, stack=stack)
    else:
        logger.warning("Failed to replace main UI for user_id=%s", user_id)
    return sent


def register_service_layer(user_id: int, message_id: int) -> None:
    """Register service message layer entry."""
    stack = load_stack(user_id)
    if message_id not in stack.service_layer_message_ids:
        stack.service_layer_message_ids.append(message_id)
        save_stack(user_id=user_id, stack=stack)


async def remove_service_layer(
    bot: Bot,
    chat_id: int,
    user_id: int,
    message_id: int,
    *,
    delete_message: bool = True,
) -> None:
    """Unregister service message layer entry."""
    stack = load_stack(user_id)
    if message_id in stack.service_layer_message_ids:
        stack.service_layer_message_ids.remove(message_id)
        save_stack(user_id=user_id, stack=stack)

    if delete_message:
        await safe_delete_message(bot=bot, chat_id=chat_id, message_id=message_id)


async def clear_service_layers(bot: Bot, chat_id: int, user_id: int) -> None:
    """Delete all registered service layer messages for user."""
    stack = load_stack(user_id)
    for message_id in list(stack.service_layer_message_ids):
        await safe_delete_message(bot=bot, chat_id=chat_id, message_id=message_id)
    stack.service_layer_message_ids = []
    save_stack(user_id=user_id, stack=stack)
