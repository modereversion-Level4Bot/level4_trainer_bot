"""Ads job skeleton."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)


def register(job_queue) -> None:
    """Register ads delivery job (TODO)."""
    _ = job_queue
    logger.info("Ads job placeholder registered.")
