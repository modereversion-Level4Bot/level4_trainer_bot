"""Media helpers for routes service."""

from __future__ import annotations

import logging
from pathlib import Path

from telegram import Bot

from config import BASE_DIR
from core.route_media_paths import build_route_media_candidates
from core.safe_telegram import safe_delete_message, safe_send_photo
from db.connection import get_connection
from db.repositories.media_assets_repo import get_media_asset, get_ready_media_asset
from db.repositories.temporary_messages_repo import (
    add_temp_message,
    delete_temp_message_record,
    list_temp_messages,
)


_TEMP_MESSAGE_TYPE_IMAGE = "image"
_TEMP_MESSAGE_TYPE_AUDIO = "audio"
_TEMP_MEDIA_MESSAGE_TYPES = frozenset({_TEMP_MESSAGE_TYPE_IMAGE, _TEMP_MESSAGE_TYPE_AUDIO})
_TEMP_SCOPE_ROUTE_IMAGE = "route_image"
_TEMP_SCOPE_ROUTE_AUDIO = "route_audio"
_ROUTES_FEATURE = "routes"
_MEDIA_CONTENT_TYPE_ROUTE_BRIEFING_IMAGE = "route_briefing_image"
_MEDIA_CONTENT_TYPE_ROUTE_STEP_IMAGE = "route_step_image"
_MEDIA_CONTENT_TYPE_ROUTE_NEWS_IMAGE = "route_news_image"
_MEDIA_CONTENT_TYPE_ROUTE_QUESTION_IMAGE = "route_question_image"
_MEDIA_CONTENT_TYPE_ROUTE_STEP_AUDIO = "route_step_audio"
_MEDIA_CONTENT_TYPE_ROUTE_NEWS_AUDIO = "route_news_audio"


logger = logging.getLogger(__name__)


def _resolve_image_file_path(image_file: str | None) -> Path | None:
    candidates = build_route_media_candidates(image_file, media_kind="image")
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=False)
        except OSError:
            continue
        try:
            base_resolved = BASE_DIR.resolve(strict=False)
            resolved.relative_to(base_resolved)
        except (ValueError, OSError):
            continue
        if resolved.is_file():
            return resolved
    return None


def _build_route_briefing_image_content_key(route_code: str | None) -> str | None:
    normalized_route_code = (route_code or "").strip()
    if not normalized_route_code:
        return None
    return f"route:{normalized_route_code}:briefing:image"


def _build_route_step_image_content_key(route_code: str | None, step_number: int) -> str | None:
    normalized_route_code = (route_code or "").strip()
    if not normalized_route_code:
        return None
    try:
        normalized_step_number = int(step_number)
    except (TypeError, ValueError):
        return None
    if normalized_step_number <= 0:
        return None
    return f"route:{normalized_route_code}:step:{normalized_step_number}:image"


def _build_route_news_image_content_key(route_code: str | None, news_code: str | None) -> str | None:
    normalized_route_code = (route_code or "").strip()
    normalized_news_code = (news_code or "").strip()
    if not normalized_route_code or not normalized_news_code:
        return None
    return f"route:{normalized_route_code}:news:{normalized_news_code}:image"


def _build_route_question_image_content_key(
    route_code: str | None,
    block_code: str | None,
    question_number: int,
) -> str | None:
    normalized_route_code = (route_code or "").strip()
    normalized_block_code = (block_code or "").strip()
    if not normalized_route_code or not normalized_block_code:
        return None
    try:
        normalized_question_number = int(question_number)
    except (TypeError, ValueError):
        return None
    if normalized_question_number <= 0:
        return None
    return (
        f"route:{normalized_route_code}:question:{normalized_block_code}:{normalized_question_number}:image"
    )


def _build_route_step_audio_content_key(route_code: str | None, step_number: int) -> str | None:
    normalized_route_code = (route_code or "").strip()
    if not normalized_route_code:
        return None
    try:
        normalized_step_number = int(step_number)
    except (TypeError, ValueError):
        return None
    if normalized_step_number <= 0:
        return None
    return f"route:{normalized_route_code}:step:{normalized_step_number}"


def _build_route_news_audio_content_key(route_code: str | None, news_code: str | None) -> str | None:
    normalized_route_code = (route_code or "").strip()
    normalized_news_code = (news_code or "").strip()
    if not normalized_route_code or not normalized_news_code:
        return None
    return f"route:{normalized_route_code}:news:{normalized_news_code}"


async def _send_route_audio_by_content_key_best_effort(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    content_type: str,
    content_key: str | None,
    audio_file: str | None,
) -> bool:
    normalized_content_key = (content_key or "").strip()
    normalized_audio_file = (audio_file or "").strip()
    if not normalized_content_key or not normalized_audio_file:
        return False

    ready_asset: dict[str, object] | None
    fallback_asset: dict[str, object] | None
    try:
        with get_connection() as conn:
            ready_asset = get_ready_media_asset(
                conn,
                feature=_ROUTES_FEATURE,
                content_type=content_type,
                content_key=normalized_content_key,
            )
            fallback_asset = (
                ready_asset
                if ready_asset is not None
                else get_media_asset(
                    conn,
                    feature=_ROUTES_FEATURE,
                    content_type=content_type,
                    content_key=normalized_content_key,
                )
            )
    except Exception:
        logger.warning(
            "Routes audio file_id lookup failed; showing text-only: "
            "user_id=%s chat_id=%s content_type=%s content_key=%s audio_file=%s",
            user_id,
            chat_id,
            content_type,
            normalized_content_key,
            normalized_audio_file,
            exc_info=True,
        )
        return False

    if ready_asset is None:
        asset_status = str((fallback_asset or {}).get("status") or "not_found").strip() or "not_found"
        logger.warning(
            "Routes audio file_id not ready; showing text-only: "
            "user_id=%s chat_id=%s content_type=%s content_key=%s status=%s audio_file=%s",
            user_id,
            chat_id,
            content_type,
            normalized_content_key,
            asset_status,
            normalized_audio_file,
        )
        return False

    file_id = str(ready_asset.get("file_id") or "").strip()
    if not file_id:
        logger.warning(
            "Routes audio ready asset has empty file_id; showing text-only: "
            "user_id=%s chat_id=%s content_type=%s content_key=%s status=%s audio_file=%s",
            user_id,
            chat_id,
            content_type,
            normalized_content_key,
            ready_asset.get("status"),
            normalized_audio_file,
        )
        return False

    try:
        sent_message = await bot.send_audio(
            chat_id=chat_id,
            audio=file_id,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=15,
            pool_timeout=15,
        )
    except Exception as exc:
        logger.warning(
            "Routes audio send by file_id failed; showing text-only: "
            "user_id=%s chat_id=%s content_type=%s content_key=%s status=%s audio_file=%s "
            "error_type=%s",
            user_id,
            chat_id,
            content_type,
            normalized_content_key,
            ready_asset.get("status"),
            normalized_audio_file,
            type(exc).__name__,
        )
        return False

    try:
        with get_connection() as conn:
            add_temp_message(
                conn,
                user_id=user_id,
                chat_id=chat_id,
                message_id=sent_message.message_id,
                feature=_ROUTES_FEATURE,
                message_type=_TEMP_MESSAGE_TYPE_AUDIO,
                scope=_TEMP_SCOPE_ROUTE_AUDIO,
            )
    except Exception:
        logger.warning(
            "Routes audio sent but temp record insert failed: user_id=%s chat_id=%s message_id=%s",
            user_id,
            chat_id,
            sent_message.message_id,
            exc_info=True,
        )
    return True


async def _send_route_image_best_effort(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    image_file: str | None,
    content_type: str | None,
    content_key: str | None,
) -> bool:
    normalized_image_file = (image_file or "").strip()
    normalized_content_key = (content_key or "").strip()
    if not normalized_image_file:
        return False

    if content_type and normalized_content_key:
        ready_asset: dict[str, object] | None
        fallback_asset: dict[str, object] | None
        try:
            with get_connection() as conn:
                ready_asset = get_ready_media_asset(
                    conn,
                    feature=_ROUTES_FEATURE,
                    content_type=content_type,
                    content_key=normalized_content_key,
                )
                fallback_asset = (
                    ready_asset
                    if ready_asset is not None
                    else get_media_asset(
                        conn,
                        feature=_ROUTES_FEATURE,
                        content_type=content_type,
                        content_key=normalized_content_key,
                    )
                )
        except Exception:
            logger.warning(
                "Routes image file_id lookup failed; trying local file fallback: "
                "user_id=%s chat_id=%s content_type=%s content_key=%s image_file=%s",
                user_id,
                chat_id,
                content_type,
                normalized_content_key,
                normalized_image_file,
                exc_info=True,
            )
            ready_asset = None
            fallback_asset = None

        if ready_asset is not None:
            file_id = str(ready_asset.get("file_id") or "").strip()
            if file_id:
                sent_message = await safe_send_photo(bot, chat_id=chat_id, photo=file_id)
                if sent_message is not None:
                    try:
                        with get_connection() as conn:
                            add_temp_message(
                                conn,
                                user_id=user_id,
                                chat_id=chat_id,
                                message_id=sent_message.message_id,
                                feature=_ROUTES_FEATURE,
                                message_type=_TEMP_MESSAGE_TYPE_IMAGE,
                                scope=_TEMP_SCOPE_ROUTE_IMAGE,
                            )
                    except Exception:
                        # best-effort only: media send must not break routes flow
                        return True
                    return True
                logger.warning(
                    "Routes image send by file_id failed; trying local file fallback: "
                    "user_id=%s chat_id=%s content_type=%s content_key=%s image_file=%s",
                    user_id,
                    chat_id,
                    content_type,
                    normalized_content_key,
                    normalized_image_file,
                )
            else:
                logger.warning(
                    "Routes image ready asset has empty file_id; trying local file fallback: "
                    "user_id=%s chat_id=%s content_type=%s content_key=%s status=%s image_file=%s",
                    user_id,
                    chat_id,
                    content_type,
                    normalized_content_key,
                    ready_asset.get("status"),
                    normalized_image_file,
                )
        elif fallback_asset is not None:
            logger.warning(
                "Routes image file_id not ready; trying local file fallback: "
                "user_id=%s chat_id=%s content_type=%s content_key=%s status=%s image_file=%s",
                user_id,
                chat_id,
                content_type,
                normalized_content_key,
                str(fallback_asset.get("status") or "unknown"),
                normalized_image_file,
            )

    image_path = _resolve_image_file_path(normalized_image_file)
    if image_path is None:
        return False
    try:
        with image_path.open("rb") as stream:
            sent_message = await safe_send_photo(bot, chat_id=chat_id, photo=stream)
    except OSError:
        return False
    if sent_message is None:
        return False
    try:
        with get_connection() as conn:
            add_temp_message(
                conn,
                user_id=user_id,
                chat_id=chat_id,
                message_id=sent_message.message_id,
                feature=_ROUTES_FEATURE,
                message_type=_TEMP_MESSAGE_TYPE_IMAGE,
                scope=_TEMP_SCOPE_ROUTE_IMAGE,
            )
    except Exception:
        # best-effort only: media send must not break routes flow
        return True
    return True


async def _send_route_media_before_ui_best_effort(
    bot: Bot,
    *,
    chat_id: int,
    user_id: int,
    image_file: str | None,
    image_content_type: str | None,
    image_content_key: str | None,
    audio_file: str | None,
    audio_content_type: str | None,
    audio_content_key: str | None,
) -> bool:
    """Send route media before UI render: image, then audio."""
    image_sent = await _send_route_image_best_effort(
        bot,
        chat_id=chat_id,
        user_id=user_id,
        image_file=image_file,
        content_type=image_content_type,
        content_key=image_content_key,
    )
    audio_sent = False
    if audio_content_type is not None:
        audio_sent = await _send_route_audio_by_content_key_best_effort(
            bot,
            chat_id=chat_id,
            user_id=user_id,
            content_type=audio_content_type,
            content_key=audio_content_key,
            audio_file=audio_file,
        )
    return image_sent or audio_sent


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


def _extract_chat_id(record: dict[str, object], fallback_chat_id: int) -> int:
    raw = record.get("chat_id")
    try:
        return int(raw) if raw is not None else int(fallback_chat_id)
    except (TypeError, ValueError):
        return int(fallback_chat_id)


async def cleanup_routes_temp_images(bot: Bot, *, user_id: int, chat_id: int) -> None:
    """Best-effort cleanup for temporary route media (images/audio)."""
    try:
        with get_connection() as conn:
            records = list_temp_messages(
                conn,
                user_id=user_id,
                feature=_ROUTES_FEATURE,
            )
    except Exception:
        return

    for record in records:
        message_type = str(record.get("message_type") or "").strip().lower()
        if message_type not in _TEMP_MEDIA_MESSAGE_TYPES:
            continue
        record_id = _extract_record_id(record)
        message_id = _extract_message_id(record)
        record_chat_id = _extract_chat_id(record, chat_id)
        if message_id is not None:
            await safe_delete_message(
                bot=bot,
                chat_id=record_chat_id,
                message_id=message_id,
            )
        if record_id is not None:
            try:
                with get_connection() as conn:
                    delete_temp_message_record(conn, record_id=record_id)
            except Exception:
                continue
