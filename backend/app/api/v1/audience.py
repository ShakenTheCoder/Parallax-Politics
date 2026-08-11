"""Audience Center endpoints — on-demand audience and extraction instructions mapping."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import desc, select

from app.api.deps import CurrentUser, DbSession
from app.models.artifact import Artifact
from app.models.principal_identity import PrincipalIdentity
from app.models.profile import Profile
from app.models.run import Run, RunStatus
from app.schemas.brief import BriefGenerateOut
from app.schemas.audience import (
    AudienceInstructionsSummary,
    PersonalAudienceInstructions,
    CompetitorsAudienceInstructions,
    ContextualAudienceInstructions,
)
from app.services.orchestrator import execute_run

router = APIRouter(prefix="/audience", tags=["audience"])


async def _resolve_principal(db, user) -> Profile:
    if not user.principal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No principal linked to this account",
        )
    res = await db.execute(select(Profile).where(Profile.id == user.principal_id))
    profile = res.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principal not found")
    return profile


# --- Trigger Analysis --------------------------------------------------------

@router.post("/analyze", response_model=BriefGenerateOut, status_code=status.HTTP_202_ACCEPTED)
async def analyze_audience(
    db: DbSession,
    user: CurrentUser,
    background: BackgroundTasks,
) -> BriefGenerateOut:
    """Kick off an Audience monitoring and instruction fanning build."""
    profile = await _resolve_principal(db, user)

    # Require a built PIDAA identity before allowing audience analysis
    pi_res = await db.execute(
        select(PrincipalIdentity).where(PrincipalIdentity.profile_id == profile.id)
    )
    pi = pi_res.scalar_one_or_none()
    if not pi or pi.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Principal identity not ready (status: {pi.status if pi else 'missing'}). "
                   "Wait for the PIDAA build to complete before triggering audience analysis.",
        )

    run = Run(
        subject_id=profile.id,
        requested_by=user.id,
        situation_prompt="",
        status=RunStatus.queued,
        meta={
            "kind": "audience_build",
            "pack_id": profile.pack_id,
            "profile_id": str(profile.id),
        },
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    background.add_task(execute_run, run.id)
    return BriefGenerateOut(run_id=run.id, status="queued")


# --- Fetch Instructions ------------------------------------------------------

@router.get("/instructions", response_model=AudienceInstructionsSummary)
async def get_audience_instructions(db: DbSession, user: CurrentUser) -> AudienceInstructionsSummary:
    """Retrieve the latest Personal, Competitors, and Contextual extraction instructions."""
    profile = await _resolve_principal(db, user)

    # Get latest artifacts for each of our kinds
    kinds = [
        "personal_audience_instructions",
        "competitors_audience_instructions",
        "contextual_audience_instructions",
        "facebook_analysis",
    ]

    artifacts_dict = {}
    last_updated = None

    for kind in kinds:
        res = await db.execute(
            select(Artifact)
            .join(Run)
            .where(Run.subject_id == profile.id)
            .where(Artifact.kind == kind)
            .order_by(desc(Artifact.created_at))
            .limit(1)
        )
        art = res.scalar_one_or_none()
        if art:
            artifacts_dict[kind] = art.payload
            if last_updated is None or art.created_at > last_updated:
                last_updated = art.created_at

    personal = None
    if "personal_audience_instructions" in artifacts_dict:
        try:
            personal = PersonalAudienceInstructions.model_validate(artifacts_dict["personal_audience_instructions"])
        except Exception:
            pass

    competitors = None
    if "competitors_audience_instructions" in artifacts_dict:
        try:
            competitors = CompetitorsAudienceInstructions.model_validate(artifacts_dict["competitors_audience_instructions"])
        except Exception:
            pass

    contextual = None
    if "contextual_audience_instructions" in artifacts_dict:
        try:
            contextual = ContextualAudienceInstructions.model_validate(artifacts_dict["contextual_audience_instructions"])
        except Exception:
            pass

    from app.schemas.audience import FacebookAnalysisResult
    facebook_analysis = None
    if "facebook_analysis" in artifacts_dict:
        try:
            facebook_analysis = FacebookAnalysisResult.model_validate(artifacts_dict["facebook_analysis"])
        except Exception:
            pass

    return AudienceInstructionsSummary(
        personal=personal,
        competitors=competitors,
        contextual=contextual,
        facebook_analysis=facebook_analysis,
        last_updated_at=last_updated.isoformat() if last_updated else None,
    )
