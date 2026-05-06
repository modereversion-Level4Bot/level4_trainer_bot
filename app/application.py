"""Build Telegram Application instance."""

from __future__ import annotations

from telegram.ext import Application

from app.handlers import register_handlers
from app.lifecycle import post_init
from config import Settings, get_settings


def create_application(settings: Settings | None = None) -> Application:
    """Create and configure python-telegram-bot Application."""
    resolved_settings = settings or get_settings()

    application = (
        Application.builder()
        .token(resolved_settings.bot_token)
        .post_init(post_init)
        .build()
    )
    register_handlers(application)
    return application
