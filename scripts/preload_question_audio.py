"""Preload Questions audio into Telegram and cache file_id in media_assets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import asyncio
import os
import sys

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import NetworkError, RetryAfter, TimedOut

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import BASE_DIR, get_settings
from core.file_utils import (
    calculate_file_checksum,
    get_file_size,
    is_supported_audio_extension,
)
from db.connection import get_connection
from db.repositories.media_assets_repo import (
    clear_orphaned_question_audio_assets,
    get_media_asset,
    mark_media_asset_failed,
    mark_media_asset_missing,
    upsert_media_asset,
)


_QUESTIONS_FEATURE = "questions"
_QUESTION_AUDIO_CONTENT_TYPE = "question_audio"
_DEFAULT_PRELOAD_DELAY_SECONDS = 1.5
_MAX_UPLOAD_ATTEMPTS = 5
_NETWORK_RETRY_BACKOFF_SECONDS = (3.0, 8.0, 15.0)


@dataclass(frozen=True, slots=True)
class QuestionAudioRow:
    level: int
    question_number: int
    audio_file: str


@dataclass(slots=True)
class PreloadSummary:
    active_questions_with_audio: int = 0
    ready_existing: int = 0
    uploaded: int = 0
    missing: int = 0
    failed: int = 0
    skipped: int = 0
    outdated: int = 0


def _safe_print(message: str, fallback: str | None = None) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(fallback if fallback is not None else message.encode("ascii", "replace").decode("ascii"))


def _print_error(message: str) -> None:
    _safe_print(f"❌ {message}", f"ERROR: {message}")


def _build_content_key(level: int, question_number: int) -> str:
    return f"questions:{int(level)}:{int(question_number)}"


def _format_seconds(seconds: float) -> str:
    normalized = max(0.0, float(seconds))
    if normalized.is_integer():
        return str(int(normalized))
    return f"{normalized:.1f}"


def _resolve_local_path(audio_file: str) -> Path:
    candidate = Path((audio_file or "").strip())
    if candidate.is_absolute():
        return candidate
    return BASE_DIR / candidate


def _load_preload_chat_id() -> int:
    raw_chat_id = os.getenv("MEDIA_PRELOAD_CHAT_ID", "").strip()
    if not raw_chat_id:
        raise RuntimeError(
            "MEDIA_PRELOAD_CHAT_ID is missing. Set it in .env to admin/service chat id for preload."
        )
    try:
        return int(raw_chat_id)
    except ValueError as exc:
        raise RuntimeError("MEDIA_PRELOAD_CHAT_ID must be an integer Telegram chat/user id.") from exc


def _load_preload_delay_seconds() -> float:
    raw = os.getenv("MEDIA_PRELOAD_DELAY_SECONDS", "").strip()
    if not raw:
        return _DEFAULT_PRELOAD_DELAY_SECONDS
    try:
        parsed = float(raw)
    except ValueError:
        return _DEFAULT_PRELOAD_DELAY_SECONDS
    if parsed < 0:
        return _DEFAULT_PRELOAD_DELAY_SECONDS
    return parsed


def _fetch_active_questions_with_audio() -> list[QuestionAudioRow]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                level,
                question_number,
                audio_file
            FROM exam_questions
            WHERE is_active = 1
              AND NULLIF(TRIM(COALESCE(audio_file, '')), '') IS NOT NULL
            ORDER BY level ASC, question_number ASC
            """
        ).fetchall()
    return [
        QuestionAudioRow(
            level=int(row["level"]),
            question_number=int(row["question_number"]),
            audio_file=str(row["audio_file"]),
        )
        for row in rows
    ]


def _is_already_ready(
    existing_asset: dict[str, object] | None,
    *,
    checksum: str,
    local_path: str,
) -> bool:
    if existing_asset is None:
        return False
    status = str(existing_asset.get("status") or "").strip().lower()
    file_id = str(existing_asset.get("file_id") or "").strip()
    existing_checksum = str(existing_asset.get("checksum") or "").strip()
    existing_path = str(existing_asset.get("local_path") or "").strip()
    if status != "ready":
        return False
    if not file_id:
        return False
    if existing_checksum != checksum:
        return False
    if existing_path != local_path:
        return False
    return True


def _mark_skipped_asset(
    *,
    content_key: str,
    local_path: str,
    reason: str,
) -> None:
    with get_connection() as conn:
        upsert_media_asset(
            conn,
            feature=_QUESTIONS_FEATURE,
            content_type=_QUESTION_AUDIO_CONTENT_TYPE,
            content_key=content_key,
            local_path=local_path,
            status="skipped",
            last_error=reason,
        )


def _mark_missing_asset(
    *,
    content_key: str,
    local_path: str,
    checksum: str | None,
    reason: str,
) -> None:
    with get_connection() as conn:
        mark_media_asset_missing(
            conn,
            feature=_QUESTIONS_FEATURE,
            content_type=_QUESTION_AUDIO_CONTENT_TYPE,
            content_key=content_key,
            local_path=local_path,
            checksum=checksum,
            error=reason,
        )


def _mark_failed_asset(
    *,
    content_key: str,
    local_path: str,
    checksum: str | None,
    reason: str,
) -> None:
    with get_connection() as conn:
        mark_media_asset_failed(
            conn,
            feature=_QUESTIONS_FEATURE,
            content_type=_QUESTION_AUDIO_CONTENT_TYPE,
            content_key=content_key,
            local_path=local_path,
            checksum=checksum,
            error=reason,
        )


def _build_upload_error_text(
    *,
    error_type: str,
    attempts: int,
    last_retry_after: float | None,
    message: str,
) -> str:
    retry_after_text = (
        "none" if last_retry_after is None else _format_seconds(float(last_retry_after))
    )
    return (
        f"error_type={error_type}; "
        f"attempts={attempts}; "
        f"retry_after={retry_after_text}; "
        f"message={message}"
    )


async def _upload_audio_with_retries(
    *,
    bot: Bot,
    preload_chat_id: int,
    local_path: Path,
) -> tuple[str | None, str | None, str | None]:
    attempts = 0
    network_retries = 0
    last_retry_after: float | None = None
    last_exception: Exception | None = None

    while attempts < _MAX_UPLOAD_ATTEMPTS:
        attempts += 1
        try:
            with local_path.open("rb") as audio_stream:
                sent_message = await bot.send_audio(
                    chat_id=preload_chat_id,
                    audio=audio_stream,
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=30,
                    pool_timeout=30,
                )
            message_audio = getattr(sent_message, "audio", None)
            file_id = str(getattr(message_audio, "file_id", "") or "").strip()
            file_unique_id = str(getattr(message_audio, "file_unique_id", "") or "").strip()
            if not file_id:
                error_text = _build_upload_error_text(
                    error_type="UploadMissingFileId",
                    attempts=attempts,
                    last_retry_after=last_retry_after,
                    message="Telegram upload returned no audio.file_id",
                )
                return None, None, error_text
            return file_id, file_unique_id or None, None
        except RetryAfter as exc:
            last_exception = exc
            retry_after_raw = getattr(exc, "retry_after", 0)
            try:
                retry_after_value = float(retry_after_raw)
            except (TypeError, ValueError):
                retry_after_value = 0.0
            retry_after_value = max(0.0, retry_after_value)
            last_retry_after = retry_after_value

            if attempts >= _MAX_UPLOAD_ATTEMPTS:
                break

            wait_seconds = retry_after_value + 1.0
            _safe_print(
                f"Flood control: waiting {_format_seconds(wait_seconds)} seconds before retry..."
            )
            await asyncio.sleep(wait_seconds)
            continue
        except (TimedOut, NetworkError) as exc:
            last_exception = exc
            if network_retries >= len(_NETWORK_RETRY_BACKOFF_SECONDS):
                break
            if attempts >= _MAX_UPLOAD_ATTEMPTS:
                break
            wait_seconds = float(_NETWORK_RETRY_BACKOFF_SECONDS[network_retries])
            network_retries += 1
            _safe_print(
                f"Network issue ({type(exc).__name__}): waiting {_format_seconds(wait_seconds)} seconds before retry..."
            )
            await asyncio.sleep(wait_seconds)
            continue
        except Exception as exc:
            last_exception = exc
            break

    error = last_exception
    if error is None:
        return None, None, "error_type=UnknownUploadError; attempts=0; retry_after=none; message=Unknown upload error"

    error_text = _build_upload_error_text(
        error_type=type(error).__name__,
        attempts=attempts,
        last_retry_after=last_retry_after,
        message=str(error),
    )
    return None, None, error_text


async def _preload_question_audio() -> int:
    summary = PreloadSummary()
    preload_delay_seconds = _load_preload_delay_seconds()

    _safe_print("🎧 Preloading question audio...", "Preloading question audio...")
    try:
        preload_chat_id = _load_preload_chat_id()
        settings = get_settings()
    except RuntimeError as exc:
        _print_error(str(exc))
        return 1

    questions_with_audio = _fetch_active_questions_with_audio()
    summary.active_questions_with_audio = len(questions_with_audio)
    active_content_keys: set[str] = set()

    async with Bot(token=settings.bot_token) as bot:
        for item in questions_with_audio:
            content_key = _build_content_key(item.level, item.question_number)
            active_content_keys.add(content_key)

            local_path = _resolve_local_path(item.audio_file)
            local_path_str = str(local_path)
            extension = local_path.suffix.lower()

            if not is_supported_audio_extension(local_path):
                _mark_skipped_asset(
                    content_key=content_key,
                    local_path=local_path_str,
                    reason=f"Unsupported audio extension: {extension or '<none>'}",
                )
                summary.skipped += 1
                continue

            if not local_path.exists():
                _mark_missing_asset(
                    content_key=content_key,
                    local_path=local_path_str,
                    checksum=None,
                    reason=f"Local audio file not found: {local_path_str}",
                )
                summary.missing += 1
                continue

            try:
                size_bytes = get_file_size(local_path)
            except Exception as exc:
                _mark_failed_asset(
                    content_key=content_key,
                    local_path=local_path_str,
                    checksum=None,
                    reason=f"Could not read file size: {type(exc).__name__}: {exc}",
                )
                summary.failed += 1
                continue

            if size_bytes <= 0:
                _mark_failed_asset(
                    content_key=content_key,
                    local_path=local_path_str,
                    checksum=None,
                    reason="Audio file is empty",
                )
                summary.failed += 1
                continue

            try:
                checksum = calculate_file_checksum(local_path)
            except Exception as exc:
                _mark_failed_asset(
                    content_key=content_key,
                    local_path=local_path_str,
                    checksum=None,
                    reason=f"Could not calculate checksum: {type(exc).__name__}: {exc}",
                )
                summary.failed += 1
                continue

            with get_connection() as conn:
                existing_asset = get_media_asset(
                    conn,
                    feature=_QUESTIONS_FEATURE,
                    content_type=_QUESTION_AUDIO_CONTENT_TYPE,
                    content_key=content_key,
                )
            if _is_already_ready(existing_asset, checksum=checksum, local_path=local_path_str):
                summary.ready_existing += 1
                continue

            file_id, file_unique_id, upload_error = await _upload_audio_with_retries(
                bot=bot,
                preload_chat_id=preload_chat_id,
                local_path=local_path,
            )
            if upload_error is not None:
                _mark_failed_asset(
                    content_key=content_key,
                    local_path=local_path_str,
                    checksum=checksum,
                    reason=f"Telegram upload failed: {upload_error}",
                )
                summary.failed += 1
                continue

            with get_connection() as conn:
                upsert_media_asset(
                    conn,
                    feature=_QUESTIONS_FEATURE,
                    content_type=_QUESTION_AUDIO_CONTENT_TYPE,
                    content_key=content_key,
                    local_path=local_path_str,
                    file_id=file_id,
                    file_unique_id=file_unique_id or None,
                    checksum=checksum,
                    status="ready",
                    last_error=None,
                )
            summary.uploaded += 1
            if preload_delay_seconds > 0:
                await asyncio.sleep(preload_delay_seconds)

    with get_connection() as conn:
        summary.outdated = clear_orphaned_question_audio_assets(conn, active_content_keys)

    _safe_print(
        f"✅ active questions with audio_file: {summary.active_questions_with_audio}",
        f"active questions with audio_file: {summary.active_questions_with_audio}",
    )
    _safe_print(f"✅ ready existing: {summary.ready_existing}", f"ready existing: {summary.ready_existing}")
    _safe_print(f"⬆️ uploaded: {summary.uploaded}", f"uploaded: {summary.uploaded}")
    _safe_print(f"⚠️ missing: {summary.missing}", f"missing: {summary.missing}")
    _safe_print(f"❌ failed: {summary.failed}", f"failed: {summary.failed}")
    _safe_print(f"⏭ skipped: {summary.skipped}", f"skipped: {summary.skipped}")
    _safe_print(f"🗂 outdated assets: {summary.outdated}", f"outdated assets: {summary.outdated}")
    if summary.failed > 0:
        _safe_print("❌ preload completed with failures", "preload completed with failures")
        return 1
    _safe_print("✅ preload completed", "preload completed")
    return 0


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    return asyncio.run(_preload_question_audio())


if __name__ == "__main__":
    raise SystemExit(main())
