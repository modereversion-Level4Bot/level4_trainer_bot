"""Logging configuration for the bot."""

from __future__ import annotations

import logging
import os
import re
from typing import Any


EXTERNAL_LOGGERS = (
    "telegram",
    "telegram.ext",
    "httpx",
    "httpcore",
    "apscheduler",
)

PROJECT_LOGGERS = (
    "app",
    "core",
    "db",
    "features",
    "integrations",
    "jobs",
    "scripts",
)

TELEGRAM_BOT_URL_PATTERN = re.compile(r"(https://api\.telegram\.org/bot)([^/\s]+)")


def _redact_sensitive(value: str, bot_token: str | None) -> str:
    redacted = TELEGRAM_BOT_URL_PATTERN.sub(r"\1<redacted>", value)
    if bot_token:
        redacted = redacted.replace(bot_token, "<redacted>")
    return redacted


def _sanitize_log_args(value: Any, bot_token: str | None) -> Any:
    if isinstance(value, str):
        return _redact_sensitive(value, bot_token)
    if isinstance(value, tuple):
        return tuple(_sanitize_log_args(item, bot_token) for item in value)
    if isinstance(value, list):
        return [_sanitize_log_args(item, bot_token) for item in value]
    if isinstance(value, dict):
        return {
            key: _sanitize_log_args(item, bot_token)
            for key, item in value.items()
        }
    return value


class TokenRedactionFilter(logging.Filter):
    """Remove BOT_TOKEN from log records if it appears in message text."""

    def __init__(self, bot_token: str | None) -> None:
        super().__init__()
        self.bot_token = bot_token.strip() if bot_token else None

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact_sensitive(str(record.msg), self.bot_token)
        if record.args:
            record.args = _sanitize_log_args(record.args, self.bot_token)
        return True


class RedactingFormatter(logging.Formatter):
    """Formatter that redacts BOT_TOKEN from final log output."""

    def __init__(self, fmt: str, bot_token: str | None) -> None:
        super().__init__(fmt=fmt)
        self.bot_token = bot_token.strip() if bot_token else None

    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        return _redact_sensitive(rendered, self.bot_token)


def _setup_external_logger_levels() -> None:
    for logger_name in EXTERNAL_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def _setup_project_logger_levels() -> None:
    for logger_name in PROJECT_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.INFO)


def setup_logging(app_env: str) -> None:
    """Configure application-safe logging strategy."""
    _ = app_env
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        force=True,
    )

    token_filter = TokenRedactionFilter(bot_token=bot_token)
    redacting_formatter = RedactingFormatter(fmt=log_format, bot_token=bot_token)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(token_filter)
        handler.setFormatter(redacting_formatter)

    _setup_external_logger_levels()
    _setup_project_logger_levels()


def _format_version(bot_version: str) -> str:
    normalized = (bot_version or "").strip()
    if not normalized:
        return "v0.0"
    if normalized.lower().startswith("v"):
        return normalized
    return f"v{normalized}"


def log_startup_banner(
    *,
    bot_version: str,
    app_env: str,
    db_path: str,
    handlers_registered: bool = True,
    job_queue_started: bool = True,
) -> None:
    """Log a safe startup banner without exposing secrets."""
    logger = logging.getLogger("core.logging")

    logger.info("🤖 [SYSTEM] Level 4 Trainer bot is running...")
    logger.info("🎮 [SYSTEM] Version: %s", _format_version(bot_version))
    logger.info("🌍 [SYSTEM] Environment: %s", (app_env or "local").strip() or "local")
    logger.info("🗄️ [SYSTEM] SQLite DB: %s", (db_path or "data/local/dev_main.db").strip())
    logger.info("📡 [SYSTEM] Mode: polling")
    if handlers_registered:
        logger.info("🧩 [SYSTEM] Handlers registered")
    else:
        logger.info("🧩 [SYSTEM] Handlers registration skipped")
    if job_queue_started:
        logger.info("⏰ [SYSTEM] JobQueue started")
    else:
        logger.info("⏰ [SYSTEM] JobQueue unavailable")
    logger.info("✅ [SYSTEM] Startup completed")
