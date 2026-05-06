"""Pending notifications delivery job skeleton."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def register(job_queue) -> None:
    """Register pending delivery worker job (TODO)."""
    _ = job_queue
    logger.info("Pending delivery job placeholder registered.")
