"""Daily tips job skeleton."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def register(job_queue) -> None:
    """Register daily tips job (TODO)."""
    _ = job_queue
    logger.info("Daily tips job placeholder registered.")
