"""Safe Telegram API wrappers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram import Bot, CallbackQuery, Message
from telegram.error import BadRequest, Forbidden, NetworkError, RetryAfter, TimedOut


logger = logging.getLogger(__name__)


async def _run_with_safety(
    action_name: str,
    call,
    *,
    retry_enabled: bool = True,
) -> Any:
    try:
        return await call()
    except RetryAfter as exc:
        logger.warning("%s failed with RetryAfter: %s", action_name, exc)
        if not retry_enabled:
            return None
        await asyncio.sleep(min(exc.retry_after, 5))
        try:
            return await call()
        except (BadRequest, Forbidden, TimedOut, NetworkError, RetryAfter) as retry_exc:
            logger.warning("%s retry failed: %s", action_name, retry_exc)
            return None
    except (BadRequest, Forbidden, TimedOut, NetworkError) as exc:
        logger.warning("%s failed: %s", action_name, exc)
        return None
    except Exception:
        logger.exception("%s failed with unexpected error.", action_name)
        return None


async def safe_answer_callback(
    query: CallbackQuery,
    text: str | None = None,
    show_alert: bool = False,
    **kwargs: Any,
) -> bool:
    """Safely answer callback query."""

    async def _call() -> bool:
        return await query.answer(text=text, show_alert=show_alert, **kwargs)

    result = await _run_with_safety("safe_answer_callback", _call, retry_enabled=False)
    return bool(result)


async def safe_send_message(
    bot: Bot,
    chat_id: int,
    text: str,
    **kwargs: Any,
) -> Message | None:
    """Safely send text message."""

    async def _call() -> Message:
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)

    result = await _run_with_safety("safe_send_message", _call)
    return result if isinstance(result, Message) else None


async def safe_edit_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str,
    **kwargs: Any,
) -> Message | bool | None:
    """Safely edit text message."""

    async def _call() -> Message | bool:
        return await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            **kwargs,
        )

    return await _run_with_safety("safe_edit_message", _call, retry_enabled=False)


async def safe_delete_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    **kwargs: Any,
) -> bool:
    """Safely delete message."""

    async def _call() -> bool:
        return await bot.delete_message(
            chat_id=chat_id,
            message_id=message_id,
            **kwargs,
        )

    result = await _run_with_safety("safe_delete_message", _call, retry_enabled=False)
    return bool(result)


async def safe_send_photo(
    bot: Bot,
    chat_id: int,
    photo: Any,
    **kwargs: Any,
) -> Message | None:
    """Safely send photo."""

    async def _call() -> Message:
        return await bot.send_photo(chat_id=chat_id, photo=photo, **kwargs)

    result = await _run_with_safety("safe_send_photo", _call)
    return result if isinstance(result, Message) else None


async def safe_send_audio(
    bot: Bot,
    chat_id: int,
    audio: Any,
    **kwargs: Any,
) -> Message | None:
    """Safely send audio."""

    async def _call() -> Message:
        return await bot.send_audio(chat_id=chat_id, audio=audio, **kwargs)

    result = await _run_with_safety("safe_send_audio", _call)
    return result if isinstance(result, Message) else None


async def safe_send_voice(
    bot: Bot,
    chat_id: int,
    voice: Any,
    **kwargs: Any,
) -> Message | None:
    """Safely send voice."""

    async def _call() -> Message:
        return await bot.send_voice(chat_id=chat_id, voice=voice, **kwargs)

    result = await _run_with_safety("safe_send_voice", _call)
    return result if isinstance(result, Message) else None
