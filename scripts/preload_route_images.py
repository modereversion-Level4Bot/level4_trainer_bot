"""Preload route images into Telegram and cache file_id in media_assets."""

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

from config import get_settings
from core.file_utils import (
    calculate_file_checksum,
    get_file_size,
    is_supported_image_extension,
)
from core.route_media_paths import build_route_media_candidates
from db.connection import get_connection, resolve_db_path
from db.repositories.media_assets_repo import (
    clear_orphaned_route_briefing_image_assets,
    clear_orphaned_route_news_image_assets,
    clear_orphaned_route_question_image_assets,
    clear_orphaned_route_step_image_assets,
    get_media_asset,
    mark_media_asset_failed,
    mark_media_asset_missing,
    upsert_media_asset,
)
from db.repositories.routes_repo import (
    list_active_route_briefing_image_assets,
    list_active_route_news_image_assets,
    list_active_route_question_image_assets,
    list_active_route_step_image_assets,
)


_ROUTES_FEATURE = "routes"
_ROUTE_BRIEFING_IMAGE_CONTENT_TYPE = "route_briefing_image"
_ROUTE_STEP_IMAGE_CONTENT_TYPE = "route_step_image"
_ROUTE_NEWS_IMAGE_CONTENT_TYPE = "route_news_image"
_ROUTE_QUESTION_IMAGE_CONTENT_TYPE = "route_question_image"
_DEFAULT_PRELOAD_DELAY_SECONDS = 1.5
_MAX_UPLOAD_ATTEMPTS = 5
_NETWORK_RETRY_BACKOFF_SECONDS = (3.0, 8.0, 15.0)


@dataclass(frozen=True, slots=True)
class RouteBriefingImageRow:
    route_code: str
    image_file: str


@dataclass(frozen=True, slots=True)
class RouteStepImageRow:
    route_code: str
    step_number: int
    image_file: str


@dataclass(frozen=True, slots=True)
class RouteNewsImageRow:
    route_code: str
    news_code: str
    image_file: str


@dataclass(frozen=True, slots=True)
class RouteQuestionImageRow:
    route_code: str
    block_code: str
    question_number: int
    image_file: str


@dataclass(slots=True)
class PreloadSummary:
    active_route_briefing_image_files: int = 0
    active_route_step_image_files: int = 0
    active_route_news_image_files: int = 0
    active_route_question_image_files: int = 0
    ready_existing: int = 0
    uploaded: int = 0
    missing: int = 0
    failed: int = 0
    skipped: int = 0
    outdated_assets: int = 0


def _safe_print(message: str, fallback: str | None = None) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(fallback if fallback is not None else message.encode("ascii", "replace").decode("ascii"))


def _print_error(message: str) -> None:
    _safe_print(f"ERROR: {message}")


def _format_seconds(seconds: float) -> str:
    normalized = max(0.0, float(seconds))
    if normalized.is_integer():
        return str(int(normalized))
    return f"{normalized:.1f}"


def _build_route_briefing_content_key(route_code: str) -> str | None:
    normalized_route_code = (route_code or "").strip()
    if not normalized_route_code:
        return None
    return f"route:{normalized_route_code}:briefing:image"


def _build_route_step_content_key(route_code: str, step_number: int) -> str | None:
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


def _build_route_news_content_key(route_code: str, news_code: str) -> str | None:
    normalized_route_code = (route_code or "").strip()
    normalized_news_code = (news_code or "").strip()
    if not normalized_route_code or not normalized_news_code:
        return None
    return f"route:{normalized_route_code}:news:{normalized_news_code}:image"


def _build_route_question_content_key(
    route_code: str,
    block_code: str,
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


def _resolve_local_path(image_file: str) -> Path:
    candidates = build_route_media_candidates(image_file, media_kind="image")
    if not candidates:
        return Path((image_file or "").strip())
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


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


def _fetch_active_route_briefing_image_rows() -> list[RouteBriefingImageRow]:
    with get_connection() as conn:
        rows = list_active_route_briefing_image_assets(conn)
    return [
        RouteBriefingImageRow(
            route_code=str(row.get("route_code") or "").strip(),
            image_file=str(row.get("image_file") or "").strip(),
        )
        for row in rows
    ]


def _fetch_active_route_step_image_rows() -> list[RouteStepImageRow]:
    with get_connection() as conn:
        rows = list_active_route_step_image_assets(conn)
    parsed: list[RouteStepImageRow] = []
    for row in rows:
        try:
            step_number = int(row.get("step_number") or 0)
        except (TypeError, ValueError):
            step_number = 0
        parsed.append(
            RouteStepImageRow(
                route_code=str(row.get("route_code") or "").strip(),
                step_number=step_number,
                image_file=str(row.get("image_file") or "").strip(),
            )
        )
    return parsed


def _fetch_active_route_news_image_rows() -> list[RouteNewsImageRow]:
    with get_connection() as conn:
        rows = list_active_route_news_image_assets(conn)
    return [
        RouteNewsImageRow(
            route_code=str(row.get("route_code") or "").strip(),
            news_code=str(row.get("news_code") or "").strip(),
            image_file=str(row.get("image_file") or "").strip(),
        )
        for row in rows
    ]


def _fetch_active_route_question_image_rows() -> list[RouteQuestionImageRow]:
    with get_connection() as conn:
        rows = list_active_route_question_image_assets(conn)
    parsed: list[RouteQuestionImageRow] = []
    for row in rows:
        try:
            question_number = int(row.get("question_number") or 0)
        except (TypeError, ValueError):
            question_number = 0
        parsed.append(
            RouteQuestionImageRow(
                route_code=str(row.get("route_code") or "").strip(),
                block_code=str(row.get("block_code") or "").strip(),
                question_number=question_number,
                image_file=str(row.get("image_file") or "").strip(),
            )
        )
    return parsed


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
    content_type: str,
    content_key: str,
    local_path: str,
    reason: str,
) -> None:
    with get_connection() as conn:
        upsert_media_asset(
            conn,
            feature=_ROUTES_FEATURE,
            content_type=content_type,
            content_key=content_key,
            local_path=local_path,
            status="skipped",
            last_error=reason,
        )


def _mark_missing_asset(
    *,
    content_type: str,
    content_key: str,
    local_path: str,
    checksum: str | None,
    reason: str,
) -> None:
    with get_connection() as conn:
        mark_media_asset_missing(
            conn,
            feature=_ROUTES_FEATURE,
            content_type=content_type,
            content_key=content_key,
            local_path=local_path,
            checksum=checksum,
            error=reason,
        )


def _mark_failed_asset(
    *,
    content_type: str,
    content_key: str,
    local_path: str,
    checksum: str | None,
    reason: str,
) -> None:
    with get_connection() as conn:
        mark_media_asset_failed(
            conn,
            feature=_ROUTES_FEATURE,
            content_type=content_type,
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


async def _upload_image_with_retries(
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
            with local_path.open("rb") as image_stream:
                sent_message = await bot.send_photo(
                    chat_id=preload_chat_id,
                    photo=image_stream,
                    read_timeout=120,
                    write_timeout=120,
                    connect_timeout=30,
                    pool_timeout=30,
                )
            message_photo = getattr(sent_message, "photo", None)
            if not message_photo:
                error_text = _build_upload_error_text(
                    error_type="UploadMissingFileId",
                    attempts=attempts,
                    last_retry_after=last_retry_after,
                    message="Telegram upload returned no photo sizes.",
                )
                return None, None, error_text
            best_size = message_photo[-1]
            file_id = str(getattr(best_size, "file_id", "") or "").strip()
            file_unique_id = str(getattr(best_size, "file_unique_id", "") or "").strip()
            if not file_id:
                error_text = _build_upload_error_text(
                    error_type="UploadMissingFileId",
                    attempts=attempts,
                    last_retry_after=last_retry_after,
                    message="Telegram upload returned no photo.file_id",
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


async def _process_route_image_asset(
    *,
    bot: Bot,
    preload_chat_id: int,
    preload_delay_seconds: float,
    summary: PreloadSummary,
    content_type: str,
    content_key: str | None,
    image_file: str,
) -> None:
    if content_key is None:
        summary.skipped += 1
        return

    local_path = _resolve_local_path(image_file)
    local_path_str = str(local_path)
    extension = local_path.suffix.lower()

    if not is_supported_image_extension(local_path):
        _mark_skipped_asset(
            content_type=content_type,
            content_key=content_key,
            local_path=local_path_str,
            reason=f"Unsupported image extension: {extension or '<none>'}",
        )
        summary.skipped += 1
        return

    if not local_path.exists():
        _mark_missing_asset(
            content_type=content_type,
            content_key=content_key,
            local_path=local_path_str,
            checksum=None,
            reason=f"Local image file not found: {local_path_str}",
        )
        summary.missing += 1
        return

    try:
        size_bytes = get_file_size(local_path)
    except Exception as exc:
        _mark_failed_asset(
            content_type=content_type,
            content_key=content_key,
            local_path=local_path_str,
            checksum=None,
            reason=f"Could not read file size: {type(exc).__name__}: {exc}",
        )
        summary.failed += 1
        return

    if size_bytes <= 0:
        _mark_failed_asset(
            content_type=content_type,
            content_key=content_key,
            local_path=local_path_str,
            checksum=None,
            reason="Image file is empty",
        )
        summary.failed += 1
        return

    try:
        checksum = calculate_file_checksum(local_path)
    except Exception as exc:
        _mark_failed_asset(
            content_type=content_type,
            content_key=content_key,
            local_path=local_path_str,
            checksum=None,
            reason=f"Could not calculate checksum: {type(exc).__name__}: {exc}",
        )
        summary.failed += 1
        return

    with get_connection() as conn:
        existing_asset = get_media_asset(
            conn,
            feature=_ROUTES_FEATURE,
            content_type=content_type,
            content_key=content_key,
        )
    if _is_already_ready(existing_asset, checksum=checksum, local_path=local_path_str):
        summary.ready_existing += 1
        return

    file_id, file_unique_id, upload_error = await _upload_image_with_retries(
        bot=bot,
        preload_chat_id=preload_chat_id,
        local_path=local_path,
    )
    if upload_error is not None:
        _mark_failed_asset(
            content_type=content_type,
            content_key=content_key,
            local_path=local_path_str,
            checksum=checksum,
            reason=f"Telegram upload failed: {upload_error}",
        )
        summary.failed += 1
        return

    with get_connection() as conn:
        upsert_media_asset(
            conn,
            feature=_ROUTES_FEATURE,
            content_type=content_type,
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


async def _preload_route_images() -> int:
    summary = PreloadSummary()
    preload_delay_seconds = _load_preload_delay_seconds()
    configured_db_path = os.getenv("DB_PATH", "").strip() or "data/local/dev_main.db"
    resolved_db_path = resolve_db_path()

    _safe_print("Preloading route images...")
    _safe_print(f"DB_PATH = {configured_db_path}")
    _safe_print(f"Resolved DB path = {resolved_db_path}")
    _safe_print("Operation mode = write")
    try:
        preload_chat_id = _load_preload_chat_id()
        settings = get_settings()
    except RuntimeError as exc:
        _print_error(str(exc))
        return 1

    briefing_rows = _fetch_active_route_briefing_image_rows()
    step_rows = _fetch_active_route_step_image_rows()
    news_rows = _fetch_active_route_news_image_rows()
    question_rows = _fetch_active_route_question_image_rows()
    summary.active_route_briefing_image_files = len(briefing_rows)
    summary.active_route_step_image_files = len(step_rows)
    summary.active_route_news_image_files = len(news_rows)
    summary.active_route_question_image_files = len(question_rows)

    active_briefing_content_keys: set[str] = set()
    active_step_content_keys: set[str] = set()
    active_news_content_keys: set[str] = set()
    active_question_content_keys: set[str] = set()

    async with Bot(token=settings.bot_token) as bot:
        for item in briefing_rows:
            content_key = _build_route_briefing_content_key(item.route_code)
            if content_key is not None:
                active_briefing_content_keys.add(content_key)
            await _process_route_image_asset(
                bot=bot,
                preload_chat_id=preload_chat_id,
                preload_delay_seconds=preload_delay_seconds,
                summary=summary,
                content_type=_ROUTE_BRIEFING_IMAGE_CONTENT_TYPE,
                content_key=content_key,
                image_file=item.image_file,
            )

        for item in step_rows:
            content_key = _build_route_step_content_key(item.route_code, item.step_number)
            if content_key is not None:
                active_step_content_keys.add(content_key)
            await _process_route_image_asset(
                bot=bot,
                preload_chat_id=preload_chat_id,
                preload_delay_seconds=preload_delay_seconds,
                summary=summary,
                content_type=_ROUTE_STEP_IMAGE_CONTENT_TYPE,
                content_key=content_key,
                image_file=item.image_file,
            )

        for item in news_rows:
            content_key = _build_route_news_content_key(item.route_code, item.news_code)
            if content_key is not None:
                active_news_content_keys.add(content_key)
            await _process_route_image_asset(
                bot=bot,
                preload_chat_id=preload_chat_id,
                preload_delay_seconds=preload_delay_seconds,
                summary=summary,
                content_type=_ROUTE_NEWS_IMAGE_CONTENT_TYPE,
                content_key=content_key,
                image_file=item.image_file,
            )

        for item in question_rows:
            content_key = _build_route_question_content_key(
                item.route_code,
                item.block_code,
                item.question_number,
            )
            if content_key is not None:
                active_question_content_keys.add(content_key)
            await _process_route_image_asset(
                bot=bot,
                preload_chat_id=preload_chat_id,
                preload_delay_seconds=preload_delay_seconds,
                summary=summary,
                content_type=_ROUTE_QUESTION_IMAGE_CONTENT_TYPE,
                content_key=content_key,
                image_file=item.image_file,
            )

    with get_connection() as conn:
        outdated_briefing_assets = clear_orphaned_route_briefing_image_assets(
            conn,
            active_briefing_content_keys,
        )
        outdated_step_assets = clear_orphaned_route_step_image_assets(conn, active_step_content_keys)
        outdated_news_assets = clear_orphaned_route_news_image_assets(conn, active_news_content_keys)
        outdated_question_assets = clear_orphaned_route_question_image_assets(
            conn,
            active_question_content_keys,
        )
    summary.outdated_assets = (
        outdated_briefing_assets
        + outdated_step_assets
        + outdated_news_assets
        + outdated_question_assets
    )

    _safe_print(
        f"active route briefing image_file count: {summary.active_route_briefing_image_files}"
    )
    _safe_print(f"active route step image_file count: {summary.active_route_step_image_files}")
    _safe_print(f"active route news image_file count: {summary.active_route_news_image_files}")
    _safe_print(
        f"active route question image_file count: {summary.active_route_question_image_files}"
    )
    _safe_print(f"ready existing: {summary.ready_existing}")
    _safe_print(f"uploaded: {summary.uploaded}")
    _safe_print(f"missing: {summary.missing}")
    _safe_print(f"failed: {summary.failed}")
    _safe_print(f"skipped: {summary.skipped}")
    _safe_print(f"outdated assets: {summary.outdated_assets}")
    if summary.failed > 0:
        _safe_print("preload completed with failures")
        return 1
    _safe_print("preload completed")
    return 0


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")
    return asyncio.run(_preload_route_images())


if __name__ == "__main__":
    raise SystemExit(main())
