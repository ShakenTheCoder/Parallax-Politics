"""Run + artifact endpoints (orchestrator wired)."""

import asyncio
import contextlib
from uuid import UUID

import orjson
from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import desc, select
from sse_starlette.sse import EventSourceResponse

from app.api.deps import CurrentUser, DbSession
from app.eventbus.bus import stream_events
from app.models.artifact import Artifact
from app.models.profile import Profile
from app.models.run import Run
from app.models.user import User
from app.schemas.agents import (
    DemographicBriefing,
    DomainBriefing,
    PrincipalIdentityArtifact,
    RunArtifacts,
    SourcePack,
)
from app.schemas.runs import PrincipalOut, RunOut

router = APIRouter(prefix="/runs", tags=["runs"])


def _can_access_run(run: Run, user: User) -> bool:
    return user.role == "superadmin" or run.requested_by == user.id


def _profile_to_out(profile: Profile | None) -> PrincipalOut | None:
    if not profile:
        return None
    return PrincipalOut(
        id=profile.id,
        slug=profile.slug,
        full_name=profile.full_name,
        role_title=profile.role_title,
        party=profile.party,
        pack_id=profile.pack_id,
        identity=profile.identity or {},
        career=profile.career or {},
        stances=profile.stances or {},
        voice_patterns=profile.voice_patterns or {},
        vulnerabilities=profile.vulnerabilities or {},
        allies_rivals=profile.allies_rivals or {},
        media_footprint=profile.media_footprint or {},
    )


def _run_to_out(run: Run, artifacts: list[Artifact], profile: Profile | None = None) -> RunOut:
    out_artifacts = RunArtifacts()
    for art in artifacts:
        with contextlib.suppress(Exception):
            if art.kind == "source_pack":
                out_artifacts.source_pack = SourcePack.model_validate(art.payload)
            elif art.kind == "domain_briefing":
                out_artifacts.domain_briefing = DomainBriefing.model_validate(art.payload)
            elif art.kind == "demographic_briefing":
                out_artifacts.demographic_briefing = DemographicBriefing.model_validate(art.payload)
            elif art.kind == "principal_identity":
                out_artifacts.principal_identity = PrincipalIdentityArtifact.model_validate(
                    art.payload
                )
    run_kind = (run.meta or {}).get("kind") or "situation"
    return RunOut(
        id=run.id,
        status=run.status.value,
        run_kind=run_kind,
        situation_prompt=run.situation_prompt,
        total_cost_usd=run.total_cost_usd,
        created_at=run.created_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
        error=run.error,
        artifacts=out_artifacts,
        principal=_profile_to_out(profile),
    )


@router.get("/{run_id}/events")
async def run_events(
    run_id: UUID,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> EventSourceResponse:
    """Authenticated SSE stream for the run owner or an administrator."""
    run = (await db.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    if not _can_access_run(run, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Run access denied")

    async def event_gen():
        channel = f"run.{run_id}"
        try:
            async for evt in stream_events(channel):
                if await request.is_disconnected():
                    break
                yield {"event": evt.get("type", "message"), "data": orjson.dumps(evt).decode()}
                if evt.get("type") in {"run.completed", "run.failed", "run.budget_exhausted"}:
                    break
        except asyncio.CancelledError:
            return

    return EventSourceResponse(event_gen())


@router.get("/me/latest-full", response_model=RunOut)
async def get_my_latest_full_run(db: DbSession, user: CurrentUser) -> RunOut:
    """Return the most recent run for the current user with all artifacts and principal snapshot."""
    run_res = await db.execute(
        select(Run).where(Run.requested_by == user.id).order_by(desc(Run.created_at)).limit(1)
    )
    run = run_res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No runs found")

    art_res = await db.execute(select(Artifact).where(Artifact.run_id == run.id))
    artifacts = list(art_res.scalars().all())

    profile: Profile | None = None
    if run.subject_id:
        prof_res = await db.execute(select(Profile).where(Profile.id == run.subject_id))
        profile = prof_res.scalar_one_or_none()

    return _run_to_out(run, artifacts, profile)


@router.get("/{run_id}", response_model=RunOut)
async def get_run(run_id: UUID, db: DbSession, user: CurrentUser) -> RunOut:
    res = await db.execute(select(Run).where(Run.id == run_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    if not _can_access_run(run, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Run access denied")
    art_res = await db.execute(select(Artifact).where(Artifact.run_id == run_id))
    artifacts = list(art_res.scalars().all())
    profile: Profile | None = None
    if run.subject_id:
        prof_res = await db.execute(select(Profile).where(Profile.id == run.subject_id))
        profile = prof_res.scalar_one_or_none()
    return _run_to_out(run, artifacts, profile)
