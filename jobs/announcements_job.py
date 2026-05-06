"""Announcements job skeleton."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def register(job_queue) -> None:
    """Register announcements delivery job (TODO)."""
    _ = job_queue
    logger.info("Announcements job placeholder registered.")
