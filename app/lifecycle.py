"""Lifecycle hooks for Telegram Application."""

from __future__ import annotations

import logging

from telegram.ext import Application

from config import get_settings
from core.logging import log_startup_banner
from jobs.scheduler import register_jobs


logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Run startup hooks after bot initialization."""
    register_jobs(application.job_queue)
    settings = get_settings()
    log_startup_banner(
        bot_version=settings.bot_version,
        app_env=settings.app_env,
        db_path=settings.db_path,
        handlers_registered=True,
        job_queue_started=application.job_queue is not None,
    )
    logger.info("Application post-init finished.")
