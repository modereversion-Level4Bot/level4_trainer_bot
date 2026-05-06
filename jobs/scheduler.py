"""Job scheduler wiring."""

from __future__ import annotations

import logging

from jobs.ads_job import register as register_ads_job
from jobs.announcements_job import register as register_announcements_job
from jobs.daily_tips_job import register as register_daily_tips_job
from jobs.pending_delivery_job import register as register_pending_delivery_job
from jobs.reminders_job import register as register_reminders_job


logger = logging.getLogger(__name__)


def register_jobs(job_queue) -> None:
    """Register all current background jobs."""
    if job_queue is None:
        logger.warning("Job queue is not available, jobs are skipped.")
        return

    register_daily_tips_job(job_queue)
    register_reminders_job(job_queue)
    register_ads_job(job_queue)
    register_announcements_job(job_queue)
    register_pending_delivery_job(job_queue)
