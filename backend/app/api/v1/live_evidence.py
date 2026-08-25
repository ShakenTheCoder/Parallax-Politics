"""Poll, audience experiment, and brief review endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import desc, select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.intelligence.principal_scope import resolve_principal
from app.models.audience_experiment import AudienceExperimentRun
from app.models.poll import Poll
from app.models.principal_brief import PrincipalBrief
from app.schemas.audience_experiment import AudienceExperimentCreate, AudienceExperimentOut
from app.schemas.brief import BriefReview
from app.schemas.poll import PollCreate, PollOut, PollReview
from app.services.audience_experiments import enqueue_experiment, execute_audience_experiment

router = APIRouter(tags=["live-evidence"])


def _poll_out(row: Poll) -> PollOut:
    return PollOut.model_validate({key: getattr(row, key) for key in ("id", "pollster", "sponsor", "published_at", "field_start", "field_end", "sample_size", "population", "mode", "margin_of_error", "confidence_level", "exact_question", "geography", "results", "source_url", "verification_status", "verified_by", "verified_at", "verification_note", "methodology_notes", "created_at")})


@router.get("/intelligence/polls", response_model=list[PollOut])
async def list_polls(db: DbSession, _user: CurrentUser) -> list[PollOut]:
    rows = (await db.execute(select(Poll).order_by(desc(Poll.published_at)).limit(100))).scalars().all()
    return [_poll_out(row) for row in rows]


@router.post("/intelligence/polls", response_model=PollOut, status_code=status.HTTP_201_CREATED)
async def create_poll(payload: PollCreate, db: DbSession, admin: AdminUser) -> PollOut:
    if (await db.execute(select(Poll).where(Poll.source_url == str(payload.source_url)))).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Poll source already imported")
    row = Poll(**payload.model_dump(), source_url=str(payload.source_url))
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _poll_out(row)


@router.patch("/intelligence/polls/{poll_id}/review", response_model=PollOut)
async def review_poll(poll_id: UUID, payload: PollReview, db: DbSession, admin: AdminUser) -> PollOut:
    row = await db.get(Poll, poll_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poll not found")
    row.verification_status = payload.decision
    row.verification_note = payload.note
    row.verified_by = admin.id
    row.verified_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(row)
    return _poll_out(row)


@router.post("/intelligence/audience-experiments", response_model=AudienceExperimentOut, status_code=status.HTTP_202_ACCEPTED)
async def create_audience_experiment(payload: AudienceExperimentCreate, db: DbSession, user: CurrentUser, background: BackgroundTasks) -> AudienceExperimentOut:
    profile = await resolve_principal(db, user, payload.profile_id)
    experiment = await enqueue_experiment(db, profile=profile, requested_by=user.id, payload=payload)
    await db.commit()
    background.add_task(execute_audience_experiment, experiment.id)
    return AudienceExperimentOut.model_validate({key: getattr(experiment, key) for key in ("id", "run_id", "profile_id", "variants", "cohorts", "status", "provider_status", "samples", "aggregate", "error", "created_at", "started_at", "finished_at")})


async def _experiment_for_user(db, user, run_id: UUID) -> AudienceExperimentRun:
    row = (await db.execute(select(AudienceExperimentRun).where(AudienceExperimentRun.run_id == run_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audience experiment not found")
    await resolve_principal(db, user, row.profile_id)
    return row


def _experiment_out(row: AudienceExperimentRun) -> AudienceExperimentOut:
    return AudienceExperimentOut.model_validate({key: getattr(row, key) for key in ("id", "run_id", "profile_id", "variants", "cohorts", "status", "provider_status", "samples", "aggregate", "error", "created_at", "started_at", "finished_at")})


@router.get("/intelligence/audience-experiments", response_model=list[AudienceExperimentOut])
async def list_audience_experiments(db: DbSession, user: CurrentUser) -> list[AudienceExperimentOut]:
    profile = await resolve_principal(db, user)
    rows = (await db.execute(select(AudienceExperimentRun).where(AudienceExperimentRun.profile_id == profile.id).order_by(desc(AudienceExperimentRun.created_at)).limit(50))).scalars().all()
    return [_experiment_out(row) for row in rows]


@router.get("/intelligence/audience-experiments/{run_id}", response_model=AudienceExperimentOut)
async def get_audience_experiment(run_id: UUID, db: DbSession, user: CurrentUser) -> AudienceExperimentOut:
    return _experiment_out(await _experiment_for_user(db, user, run_id))


@router.patch("/briefs/{brief_id}/review", response_model=dict)
async def review_brief(brief_id: UUID, payload: BriefReview, db: DbSession, admin: AdminUser) -> dict:
    row = await db.get(PrincipalBrief, brief_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    row.review_status = payload.decision
    row.reviewed_by = admin.id
    row.reviewed_at = datetime.now(UTC)
    row.review_note = payload.note
    await db.commit()
    return {"id": str(row.id), "review_status": row.review_status, "reviewed_by": str(admin.id), "reviewed_at": row.reviewed_at.isoformat(), "review_note": row.review_note}
