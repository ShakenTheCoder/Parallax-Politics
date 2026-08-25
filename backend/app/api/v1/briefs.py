"""Brief endpoints — on-demand strategic briefs for the current user's principal."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import desc, select

from app.api.deps import CurrentUser, DbSession
from app.models.principal_brief import PrincipalBrief
from app.models.principal_identity import PrincipalIdentity
from app.models.profile import Profile
from app.schemas.brief import (
    BriefActionCard,
    BriefActiveOut,
    BriefGenerateOut,
    BriefOut,
    BriefSource,
    BriefSummary,
    BriefTopic,
    TopOpportunity,
    TopRisk,
)
from app.services.brief_runs import enqueue_brief_run, get_active_brief_run
from app.services.orchestrator import execute_run

router = APIRouter(prefix="/briefs", tags=["briefs"])


def _row_to_out(row: PrincipalBrief) -> BriefOut:
    return BriefOut(
        id=row.id,
        profile_id=row.profile_id,
        run_id=row.run_id,
        created_at=row.created_at,
        top_risk=TopRisk.model_validate(row.top_risk or {}),
        top_opportunity=TopOpportunity.model_validate(row.top_opportunity or {}),
        topics=[BriefTopic.model_validate(t) for t in (row.topics or [])],
        action_card=BriefActionCard.model_validate(row.action_card or {}),
        reasoning=row.reasoning or "",
        sources=[BriefSource.model_validate(s) for s in (row.sources or [])],
        model=row.model,
        cost_usd=float(row.cost_usd or 0.0),
        confidence=float(row.confidence or 0.0),
        command_view=None,
        review_status=row.review_status,
        reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at,
        review_note=row.review_note,
    )


def _row_to_summary(row: PrincipalBrief) -> BriefSummary:
    tr = row.top_risk or {}
    to = row.top_opportunity or {}
    ac = row.action_card or {}
    return BriefSummary(
        id=row.id,
        created_at=row.created_at,
        top_risk_label=str(tr.get("label") or ""),
        top_opportunity_label=str(to.get("label") or ""),
        action_what=str(ac.get("what") or ""),
        confidence=float(row.confidence or 0.0),
        cost_usd=float(row.cost_usd or 0.0),
        review_status=row.review_status,
    )


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


# --- Generate ---------------------------------------------------------------


@router.post("", response_model=BriefGenerateOut, status_code=status.HTTP_202_ACCEPTED)
async def generate_brief(
    db: DbSession,
    user: CurrentUser,
    background: BackgroundTasks,
) -> BriefGenerateOut:
    """Kick off a Brief build for the current user's principal."""
    profile = await _resolve_principal(db, user)

    run, created = await enqueue_brief_run(
        db,
        profile=profile,
        requested_by=user.id,
        trigger="manual",
    )
    await db.commit()
    if created:
        background.add_task(execute_run, run.id)
    return BriefGenerateOut(run_id=run.id, status="queued" if created else "running")


# --- Read -------------------------------------------------------------------


@router.get("/active", response_model=BriefActiveOut)
async def get_active_brief(db: DbSession, user: CurrentUser) -> BriefActiveOut:
    """Return the current in-flight Brief so a reloaded client can resume it."""
    profile = await _resolve_principal(db, user)
    run = await get_active_brief_run(db, profile.id)
    if not run:
        return BriefActiveOut()
    return BriefActiveOut(run_id=run.id, status=run.status.value)


@router.get("", response_model=list[BriefSummary])
async def list_my_briefs(db: DbSession, user: CurrentUser) -> list[BriefSummary]:
    profile = await _resolve_principal(db, user)
    res = await db.execute(
        select(PrincipalBrief)
        .where(
            PrincipalBrief.profile_id == profile.id,
            PrincipalBrief.archived_at.is_(None),
        )
        .order_by(desc(PrincipalBrief.created_at))
        .limit(50)
    )
    return [_row_to_summary(r) for r in res.scalars().all()]


@router.get("/latest", response_model=BriefOut)
async def get_my_latest_brief(db: DbSession, user: CurrentUser) -> BriefOut:
    profile = await _resolve_principal(db, user)
    res = await db.execute(
        select(PrincipalBrief)
        .where(
            PrincipalBrief.profile_id == profile.id,
            PrincipalBrief.archived_at.is_(None),
        )
        .order_by(desc(PrincipalBrief.created_at))
        .limit(1)
    )
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No briefs yet")
    return _row_to_out(row)


@router.get("/me/identity")
async def get_my_identity(db: DbSession, user: CurrentUser) -> dict:
    """Return the current user's principal identity dossier (PIDAA output)."""
    profile = await _resolve_principal(db, user)
    pi_res = await db.execute(
        select(PrincipalIdentity).where(PrincipalIdentity.profile_id == profile.id)
    )
    pi = pi_res.scalar_one_or_none()
    return {
        "profile_id": str(profile.id),
        "full_name": profile.full_name,
        "role_title": profile.role_title,
        "party": profile.party,
        "pack_id": profile.pack_id,
        "pidaa_status": pi.status if pi else "no_identity",
        "built_at": pi.built_at.isoformat() if (pi and pi.built_at) else None,
        "identity": {
            "basics": (pi.basics if pi else {}) or {},
            "family": (pi.family if pi else {}) or {},
            "education": (pi.education if pi else {}) or {},
            "career_timeline": (pi.career_timeline if pi else {}) or {},
            "current_position": (pi.current_position if pi else {}) or {},
            "party_history": (pi.party_history if pi else {}) or {},
            "electoral_record": (pi.electoral_record if pi else {}) or {},
            "policy_stances": (pi.policy_stances if pi else {}) or {},
            "voice_signature": (pi.voice_signature if pi else {}) or {},
            "controversies": (pi.controversies if pi else {}) or {},
            "network": (pi.network if pi else {}) or {},
            "source_index": (pi.source_index if pi else {}) or {},
            "coverage_gaps": list((pi.coverage_gaps if pi else []) or []),
        }
        if pi
        else None,
    }


@router.post("/{brief_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_brief(brief_id: UUID, db: DbSession, user: CurrentUser) -> None:
    """Soft-archive one of the current principal's briefs, preserving the audit record."""
    profile = await _resolve_principal(db, user)
    res = await db.execute(
        select(PrincipalBrief).where(
            PrincipalBrief.id == brief_id,
            PrincipalBrief.profile_id == profile.id,
        )
    )
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    if row.archived_at is None:
        row.archived_at = datetime.now(UTC)
        await db.commit()


@router.get("/{brief_id}", response_model=BriefOut)
async def get_brief(brief_id: UUID, db: DbSession, user: CurrentUser) -> BriefOut:
    profile = await _resolve_principal(db, user)
    res = await db.execute(
        select(PrincipalBrief).where(
            PrincipalBrief.id == brief_id,
            PrincipalBrief.profile_id == profile.id,
        )
    )
    row = res.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brief not found")
    return _row_to_out(row)
