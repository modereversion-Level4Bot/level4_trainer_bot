"""Temporary audio message handling for Questions feature."""

from __future__ import annotations

import logging

from telegram import Bot
from telegram.error import BadRequest

from db.connection import get_connection
from db.repositories.media_assets_repo import (
    get_media_asset,
    get_ready_media_asset,
)
from db.repositories.temporary_messages_repo import (
    add_temp_message,
    delete_temp_message_record,
    list_temp_messages,
)


logger = logging.getLogger(__name__)

_QUESTIONS_FEATURE = "questions"
_AUDIO_MESSAGE_TYPE = "audio"
_CURRENT_QUESTION_SCOPE = "current_question"
_MEDIA_CONTENT_TYPE = "question_audio"


def _looks_like_bot(candidate: object | None) -> bool:
    if candidate is None:
        return False
    return callable(getattr(candidate, "delete_message", None)) and callable(
        getattr(candidate, "send_audio", None)
    )


def _extract_bot(context: object) -> Bot | object | None:
    if isinstance(context, Bot):
        return context
    if _looks_like_bot(context):
        return context
    candidate = getattr(context, "bot", None)
    if isinstance(candidate, Bot) or _looks_like_bot(candidate):
        return candidate
    return None


def _extract_record_id(record: dict[str, object]) -> int | None:
    raw = record.get("id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _extract_message_id(record: dict[str, object]) -> int | None:
    raw = record.get("message_id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _extract_record_chat_id(record: dict[str, object], fallback_chat_id: int) -> int:
    raw = record.get("chat_id")
    try:
        return int(raw) if raw is not None else int(fallback_chat_id)
    except (TypeError, ValueError):
        return int(fallback_chat_id)


def _extract_positive_int(value: object) -> int | None:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return None
    if normalized <= 0:
        return None
    return normalized


def _build_question_audio_content_key(question: dict[str, object]) -> str | None:
    level = _extract_positive_int(question.get("level"))
    question_number = _extract_positive_int(question.get("question_number"))
    if level is None or question_number is None:
        return None
    return f"questions:{level}:{question_number}"


def _remove_record_best_effort(*, record_id: int | None) -> bool:
    if record_id is None:
        logger.warning("Questions temp audio DB record kept: invalid record_id")
        return False

    try:
        with get_connection() as conn:
            delete_temp_message_record(conn, record_id=record_id)
        logger.debug("Questions temp audio DB record removed: record_id=%s", record_id)
        return True
    except Exception:
        logger.warning(
            "Questions temp audio DB record kept: record_id=%s",
            record_id,
            exc_info=True,
        )
        return False


def _is_message_already_gone_error(exc: Exception) -> bool:
    if not isinstance(exc, BadRequest):
        return False
    message = str(exc).lower()
    if "message to delete not found" in message:
        return True
    if "message to be deleted not found" in message:
        return True
    if "message not found" in message:
        return True
    if "can't be deleted" in message and ("already" in message or "gone" in message):
        return True
    return False


def _list_questions_audio_temp_records(user_id: int) -> list[dict[str, object]]:
    with get_connection() as conn:
        return list_temp_messages(
            conn,
            user_id=user_id,
            feature=_QUESTIONS_FEATURE,
            message_type=_AUDIO_MESSAGE_TYPE,
        )


def count_questions_temp_audio_records(user_id: int) -> int:
    """Technical helper for diagnostics in checks/debug scripts."""
    return len(_list_questions_audio_temp_records(user_id))


async def cleanup_questions_audio(
    context: object,
    user_id: int,
    chat_id: int,
) -> None:
    """
    Delete temporary Questions audio messages and clear DB records.

    All operations are best-effort; failures are logged and never raised to user flow.
    """
    try:
        temp_messages = _list_questions_audio_temp_records(user_id)
    except Exception:
        logger.warning(
            "Questions audio cleanup failed to load temporary messages: user_id=%s",
            user_id,
            exc_info=True,
        )
        return

    logger.debug(
        "Questions temp audio cleanup: user_id=%s records=%s",
        user_id,
        len(temp_messages),
    )
    if not temp_messages:
        logger.debug("Questions temp audio cleanup: no temp records user_id=%s", user_id)
        return

    bot = _extract_bot(context)
    if bot is None:
        logger.warning(
            "Questions temp audio cleanup skipped: bot unavailable, "
            "records kept for retry: user_id=%s records=%s fallback_chat_id=%s",
            user_id,
            len(temp_messages),
            chat_id,
        )
        return

    for record in temp_messages:
        record_id = _extract_record_id(record)
        message_id = _extract_message_id(record)
        record_chat_id = _extract_record_chat_id(record, chat_id)

        logger.debug(
            "Trying to delete questions temp audio: user_id=%s chat_id=%s message_id=%s record_id=%s",
            user_id,
            record_chat_id,
            message_id,
            record_id,
        )

        if message_id is None:
            logger.warning(
                "Questions temp audio cleanup record has invalid message_id, "
                "keeping DB record for retry: user_id=%s record_id=%s",
                user_id,
                record_id,
            )
            logger.debug("Questions temp audio DB record kept: record_id=%s", record_id)
            continue

        should_remove_record = False
        try:
            await bot.delete_message(chat_id=record_chat_id, message_id=message_id)
            logger.debug(
                "Questions temp audio deleted: record_id=%s chat_id=%s message_id=%s",
                record_id,
                record_chat_id,
                message_id,
            )
            should_remove_record = True
        except Exception as exc:
            if _is_message_already_gone_error(exc):
                logger.debug(
                    "Questions temp audio already gone, removing DB record: "
                    "record_id=%s chat_id=%s message_id=%s",
                    record_id,
                    record_chat_id,
                    message_id,
                )
                should_remove_record = True
            else:
                logger.warning(
                    "Questions temp audio delete failed, keeping DB record for retry: "
                    "record_id=%s user_id=%s chat_id=%s message_id=%s error_type=%s error=%s",
                    record_id,
                    user_id,
                    record_chat_id,
                    message_id,
                    type(exc).__name__,
                    exc,
                )
                logger.debug("Questions temp audio DB record kept for retry: record_id=%s", record_id)

        if should_remove_record:
            _ = _remove_record_best_effort(record_id=record_id)


async def delete_user_audio(
    bot: Bot,
    chat_id: int,
    *,
    user_id: int,
) -> None:
    """Backward-compatible alias for Questions audio cleanup."""
    await cleanup_questions_audio(bot, user_id=user_id, chat_id=chat_id)


async def send_question_audio_if_exists(
    context: object,
    user_id: int,
    chat_id: int,
    *,
    question: dict[str, object],
) -> None:
    """
    Cleanup old Questions audio and send current question audio if available.

    Old audio is always cleaned first, even if current question has no valid audio file.
    """
    await cleanup_questions_audio(context, user_id=user_id, chat_id=chat_id)
    try:
        remaining_after_cleanup = _list_questions_audio_temp_records(user_id)
    except Exception:
        remaining_after_cleanup = []
        logger.warning(
            "Questions temp audio post-cleanup diagnostics failed: user_id=%s",
            user_id,
            exc_info=True,
        )
    if remaining_after_cleanup:
        logger.warning(
            "Questions temp audio cleanup left records for retry before send: "
            "user_id=%s records=%s",
            user_id,
            len(remaining_after_cleanup),
        )

    bot = _extract_bot(context)
    if bot is None:
        logger.warning(
            "Questions audio send skipped: bot unavailable user_id=%s chat_id=%s",
            user_id,
            chat_id,
        )
        return

    audio_file = str(question.get("audio_file") or "").strip() or None
    if audio_file is None:
        return

    content_key = _build_question_audio_content_key(question)
    if content_key is None:
        logger.warning(
            "Questions audio skipped: could not build content_key from question metadata; "
            "user_id=%s chat_id=%s level=%s question_number=%s audio_file=%s",
            user_id,
            chat_id,
            question.get("level"),
            question.get("question_number"),
            audio_file,
        )
        return

    ready_asset: dict[str, object] | None
    fallback_asset: dict[str, object] | None
    try:
        with get_connection() as conn:
            ready_asset = get_ready_media_asset(
                conn,
                feature=_QUESTIONS_FEATURE,
                content_type=_MEDIA_CONTENT_TYPE,
                content_key=content_key,
            )
            fallback_asset = (
                ready_asset
                if ready_asset is not None
                else get_media_asset(
                    conn,
                    feature=_QUESTIONS_FEATURE,
                    content_type=_MEDIA_CONTENT_TYPE,
                    content_key=content_key,
                )
            )
    except Exception:
        logger.warning(
            "Questions audio file_id lookup failed; showing text-only question: "
            "user_id=%s chat_id=%s content_key=%s audio_file=%s",
            user_id,
            chat_id,
            content_key,
            audio_file,
            exc_info=True,
        )
        return

    if ready_asset is None:
        asset_status = str((fallback_asset or {}).get("status") or "not_found").strip() or "not_found"
        logger.warning(
            "Questions audio file_id not ready; showing text-only question: "
            "user_id=%s chat_id=%s content_key=%s status=%s audio_file=%s",
            user_id,
            chat_id,
            content_key,
            asset_status,
            audio_file,
        )
        return

    file_id = str(ready_asset.get("file_id") or "").strip()
    if not file_id:
        logger.warning(
            "Questions audio file_id empty in ready asset; showing text-only question: "
            "user_id=%s chat_id=%s content_key=%s status=%s audio_file=%s",
            user_id,
            chat_id,
            content_key,
            ready_asset.get("status"),
            audio_file,
        )
        return

    file_id_present = bool(file_id)
    sent_message_id: int | None = None
    try:
        sent_message = await bot.send_audio(
            chat_id=chat_id,
            audio=file_id,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=15,
            pool_timeout=15,
        )
        if sent_message is not None:
            sent_message_id = sent_message.message_id
    except Exception as exc:
        logger.warning(
            "Questions audio send by file_id failed; showing text-only question: "
            "user_id=%s chat_id=%s content_key=%s file_id_present=%s status=%s audio_file=%s "
            "error_type=%s error=%s",
            user_id,
            chat_id,
            content_key,
            file_id_present,
            ready_asset.get("status"),
            audio_file,
            type(exc).__name__,
            exc,
        )
        return

    if sent_message_id is None:
        logger.warning(
            "Questions audio send by file_id returned no message_id: "
            "user_id=%s chat_id=%s content_key=%s file_id_present=%s",
            user_id,
            chat_id,
            content_key,
            file_id_present,
        )
        return

    try:
        with get_connection() as conn:
            add_temp_message(
                conn,
                user_id=user_id,
                chat_id=chat_id,
                message_id=sent_message_id,
                feature=_QUESTIONS_FEATURE,
                message_type=_AUDIO_MESSAGE_TYPE,
                scope=_CURRENT_QUESTION_SCOPE,
            )
        logger.debug(
            "Questions temp audio send registered: "
            "user_id=%s chat_id=%s message_id=%s content_key=%s file_id_present=%s",
            user_id,
            chat_id,
            sent_message_id,
            content_key,
            file_id_present,
        )
    except Exception:
        logger.warning(
            "Questions audio sent but temp record insert failed: user_id=%s message_id=%s",
            user_id,
            sent_message_id,
            exc_info=True,
        )
