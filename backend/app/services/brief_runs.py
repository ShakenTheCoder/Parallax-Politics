"""Brief-run creation and daily scheduling."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models.profile import Profile
from app.models.run import Run, RunStatus
from app.models.user import User
from app.telemetry.logging import get_logger

log = get_logger(__name__)
_ACTIVE_STATUSES = (RunStatus.queued, RunStatus.running)


async def get_active_brief_run(db: AsyncSession, profile_id: UUID) -> Run | None:
    """Return the one in-flight Brief run for a principal, if present."""
    candidates = (
        await db.execute(
            select(Run)
            .where(Run.subject_id == profile_id, Run.status.in_(_ACTIVE_STATUSES))
            .order_by(Run.created_at.desc())
        )
    ).scalars()
    return next((run for run in candidates if (run.meta or {}).get("kind") == "brief_build"), None)


async def enqueue_brief_run(
    db: AsyncSession,
    *,
    profile: Profile,
    requested_by: UUID,
    trigger: str,
) -> tuple[Run, bool]:
    """Return an active brief run or enqueue exactly one new run for a principal."""
    active_run = await get_active_brief_run(db, profile.id)
    if active_run:
        return active_run, False

    run = Run(
        subject_id=profile.id,
        requested_by=requested_by,
        situation_prompt="",
        status=RunStatus.queued,
        meta={
            "kind": "brief_build",
            "trigger": trigger,
            "pack_id": profile.pack_id,
            "profile_id": str(profile.id),
            "full_name": profile.full_name,
        },
    )
    db.add(run)
    await db.flush()
    return run, True


async def run_daily_briefs(ctx: dict[Any, Any]) -> int:
    """Generate one daily brief per principal account, without duplicate active runs."""
    del ctx
    async with SessionLocal() as db:
        users = (
            (await db.execute(select(User).where(User.principal_id.is_not(None)))).scalars().all()
        )
        queued: list[UUID] = []
        for user in users:
            profile = await db.get(Profile, user.principal_id)
            if not profile:
                continue
            run, created = await enqueue_brief_run(
                db,
                profile=profile,
                requested_by=user.id,
                trigger="daily",
            )
            if created:
                queued.append(run.id)
        await db.commit()

    if not queued:
        return 0

    from app.services.orchestrator import execute_run

    await asyncio.gather(*(execute_run(run_id) for run_id in queued))
    log.info("brief.daily.complete", queued=len(queued))
    return len(queued)
