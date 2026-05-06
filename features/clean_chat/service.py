"""Helpers that define the clean-chat runtime contract.

Source of truth for incoming private messages:
- feature handlers process message first;
- clean-chat guard deletes user message best-effort afterwards;
- deletion errors are ignored and must not break UX flow.
"""

from __future__ import annotations

from telegram import Chat, Message, User


def should_cleanup_private_user_message(
    *,
    message: Message | None,
    chat: Chat | None,
    user: User | None,
) -> bool:
    """Return True when clean-chat guard should attempt post-processing delete."""
    if message is None or chat is None or user is None:
        return False
    if user.is_bot:
        return False
    return chat.type == "private"

