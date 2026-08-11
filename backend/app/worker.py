"""ARQ worker configuration for persistent background intelligence work."""

from typing import ClassVar

from arq import cron
from arq.connections import RedisSettings

from app.config import get_settings
from app.intelligence.jobs import run_due_collections


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    cron_jobs: ClassVar = [
        cron(
            run_due_collections,
            second=5,
            run_at_startup=True,
            timeout=300,
            max_tries=1,
        )
    ]
    max_jobs = 10
    job_timeout = 300
