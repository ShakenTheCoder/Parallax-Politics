"""Superadmin-only political figures glossary endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import AdminToken, DbSession
from app.models.political_figure import PoliticalFigure, PoliticalFigureSnapshot
from app.models.run import Run, RunStatus
from app.schemas.political_figure import (
    PoliticalFigureDetail,
    PoliticalFigureSeedOut,
    PoliticalFigureSummary,
)
from app.services.orchestrator import execute_run

router = APIRouter(prefix="/admin/glossary", tags=["political-glossary"])


def _summary(item: PoliticalFigure) -> PoliticalFigureSummary:
    summary = PoliticalFigureSummary.model_validate(item, from_attributes=True)
    summary.social_platforms = list(
        dict.fromkeys(
            str(account.get("platform"))
            for account in (item.social_accounts or [])
            if account.get("platform")
        )
    )
    return summary


@router.get("/figures", response_model=list[PoliticalFigureSummary])
async def list_figures(
    db: DbSession, _sa: AdminToken, q: str | None = Query(default=None), category: str | None = None
) -> list[PoliticalFigureSummary]:
    query = (
        select(PoliticalFigure)
        .where(PoliticalFigure.archived_at.is_(None))
        .order_by(PoliticalFigure.category, PoliticalFigure.canonical_name)
    )
    if q:
        query = query.where(PoliticalFigure.canonical_name.ilike(f"%{q}%"))
    if category:
        query = query.where(PoliticalFigure.category == category)
    return [_summary(item) for item in (await db.execute(query)).scalars().all()]


@router.get("/figures/{slug}", response_model=PoliticalFigureDetail)
async def get_figure(slug: str, db: DbSession, _sa: AdminToken) -> PoliticalFigureDetail:
    item = (
        await db.execute(
            select(PoliticalFigure).where(
                PoliticalFigure.slug == slug, PoliticalFigure.archived_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Political figure not found")
    count = (
        await db.execute(
            select(func.count(PoliticalFigureSnapshot.id)).where(
                PoliticalFigureSnapshot.figure_id == item.id
            )
        )
    ).scalar_one()
    out = PoliticalFigureDetail.model_validate(item, from_attributes=True)
    out.snapshot_count = int(count)
    return out


@router.post("/seed", response_model=PoliticalFigureSeedOut, status_code=status.HTTP_202_ACCEPTED)
async def seed_figures(
    db: DbSession, _sa: AdminToken, background: BackgroundTasks
) -> PoliticalFigureSeedOut:
    run = Run(
        requested_by=_sa.id,
        situation_prompt="Seed the Superadmin political figures glossary",
        status=RunStatus.queued,
        meta={"kind": "political_glossary_seed"},
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    background.add_task(execute_run, run.id)
    return PoliticalFigureSeedOut(run_id=run.id)


@router.post(
    "/figures/{slug}/refresh",
    response_model=PoliticalFigureSeedOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def refresh_figure(
    slug: str, db: DbSession, _sa: AdminToken, background: BackgroundTasks
) -> PoliticalFigureSeedOut:
    item = (
        await db.execute(
            select(PoliticalFigure).where(
                PoliticalFigure.slug == slug, PoliticalFigure.archived_at.is_(None)
            )
        )
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Political figure not found")
    active = (
        await db.execute(
            select(Run).where(
                Run.requested_by == _sa.id,
                Run.status.in_([RunStatus.queued, RunStatus.running]),
                Run.meta["kind"].as_string() == "political_glossary_refresh",
                Run.meta["figure_id"].as_string() == str(item.id),
            )
        )
    ).scalar_one_or_none()
    if active:
        return PoliticalFigureSeedOut(run_id=active.id, status=active.status.value)
    run = Run(
        requested_by=_sa.id,
        situation_prompt=f"Refresh evidence-backed glossary dossier for {item.canonical_name}",
        status=RunStatus.queued,
        meta={"kind": "political_glossary_refresh", "figure_id": str(item.id)},
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    background.add_task(execute_run, run.id)
    return PoliticalFigureSeedOut(run_id=run.id)
