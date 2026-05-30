"""Commander / orchestrator — runs the DAG and persists artifacts.

Two modes (selected by Run.meta.kind):
  pidaa_build  →  PIDAA only  (principal identity creation)
  brief_build  →  Brief agent (loads PIDAA, runs SGA + DCAA + DEMCAA internally, synthesizes)
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select

from app.agents.base import AgentContext
from app.agents.brief import BriefAgent
from app.agents.pidaa import PIDAA
from app.db import session_scope
from app.eventbus.bus import publish_event
from app.llm.budget import BudgetExhaustedError
from app.models.artifact import Artifact
from app.models.run import Run, RunStatus
from app.schemas.agents import AgentResult
from app.services.evidence_store import persist_evidence

log = structlog.get_logger(__name__)


async def execute_run(run_id: UUID) -> None:
    """Top-level entry — called from the API as a background task.

    Dispatches based on Run.meta.kind:
      - "pidaa_build" → PIDAA only
      - "brief_build" → Brief agent (default fallback)
    """
    channel = f"run.{run_id}"

    async with session_scope() as db:
        res = await db.execute(select(Run).where(Run.id == run_id))
        run = res.scalar_one_or_none()
        if not run:
            log.warning("orchestrator.no_run", run_id=str(run_id))
            return
        run.status = RunStatus.running
        run.started_at = datetime.now(UTC)
        subject_slug, run_meta = await _resolve_subject(db, run)

    await publish_event(channel, {"type": "run.started", "run_id": str(run_id)})

    pack_id: str | None = run_meta.get("pack_id") if run_meta else None
    run_kind: str = (run_meta.get("kind") or "brief_build") if run_meta else "brief_build"

    ctx = AgentContext(
        run_id=str(run_id),
        situation_prompt="",  # deprecated — retained as empty string for AgentContext shape
        subject_slug=subject_slug,
        pack_id=pack_id,
        extra=run_meta or {},
    )

    try:
        if run_kind == "pidaa_build":
            await _run_pidaa_pipeline(run_id, ctx)
        elif run_kind == "brief_build":
            await _run_brief_pipeline(run_id, ctx)
        else:
            log.warning("orchestrator.unknown_kind", kind=run_kind)
            await _run_brief_pipeline(run_id, ctx)

        await _finalize_run(run_id, status=RunStatus.completed)
        await publish_event(channel, {"type": "run.completed", "run_id": str(run_id)})

    except BudgetExhaustedError as exc:
        log.warning("orchestrator.budget_exhausted", error=str(exc))
        await _finalize_run(run_id, status=RunStatus.budget_exhausted, error=str(exc))
        await publish_event(channel, {"type": "run.budget_exhausted", "error": str(exc)})

    except Exception as exc:
        log.exception("orchestrator.failed", error=str(exc))
        await _finalize_run(run_id, status=RunStatus.failed, error=str(exc))
        await publish_event(channel, {"type": "run.failed", "error": str(exc)})


# --- pipelines ---------------------------------------------------------------

async def _run_pidaa_pipeline(run_id: UUID, ctx: AgentContext) -> None:
    """PIDAA build — identity creation for a new principal."""
    pidaa_result = await PIDAA().run(ctx)
    await _persist_artifact(run_id, "principal_identity", pidaa_result)


async def _run_brief_pipeline(run_id: UUID, ctx: AgentContext) -> None:
    """Brief build — Brief agent fans out to SGA/DCAA/DEMCAA internally and persists
    a PrincipalBrief row. We also persist the SGA/DCAA/DEMCAA artifacts to the run
    for traceability.
    """
    # BriefAgent emits per-step events internally (sga/dcaa/demcaa/brief).
    brief_result = await BriefAgent().run(ctx)

    # Persist sub-agent artifacts produced by the Brief pipeline (best-effort).
    if "SGA" in ctx.upstream:
        await _persist_artifact(run_id, "source_pack", ctx.upstream["SGA"])
    if "DCAA" in ctx.upstream:
        await _persist_artifact(run_id, "domain_briefing", ctx.upstream["DCAA"])
    if "DEMCAA" in ctx.upstream:
        await _persist_artifact(run_id, "demographic_briefing", ctx.upstream["DEMCAA"])

    # Persist a top-level brief artifact pointing at the PrincipalBrief row.
    await _persist_artifact(run_id, "brief", brief_result)


# --- helpers ----------------------------------------------------------------

async def _resolve_subject(db, run: Run) -> tuple[str | None, dict]:
    meta: dict = run.meta or {}
    if not run.subject_id:
        return None, meta
    from app.models.profile import Profile
    res = await db.execute(select(Profile).where(Profile.id == run.subject_id))
    p = res.scalar_one_or_none()
    if p:
        if not meta.get("pack_id") and getattr(p, "pack_id", None):
            meta = {**meta, "pack_id": p.pack_id}
        if not meta.get("profile_id"):
            meta = {**meta, "profile_id": str(p.id)}
    return (p.slug if p else None), meta


async def _persist_artifact(run_id: UUID, kind: str, result: AgentResult) -> None:
    async with session_scope() as db:
        art = Artifact(
            run_id=run_id,
            kind=kind,
            payload=result.payload,
            produced_by=result.agent,
            confidence=result.confidence,
        )
        db.add(art)
        await db.flush()
        await persist_evidence(db, run_id=run_id, artifact_id=art.id, result=result)


async def _finalize_run(run_id: UUID, *, status: RunStatus, error: str | None = None) -> None:
    async with session_scope() as db:
        res = await db.execute(select(Run).where(Run.id == run_id))
        run = res.scalar_one_or_none()
        if not run:
            return
        run.status = status
        run.finished_at = datetime.now(UTC)
        if error:
            run.error = error
        # Compute total cost from llm_calls
        from sqlalchemy import func

        from app.models.llm_call import LLMCall
        total = (
            await db.execute(
                select(func.coalesce(func.sum(LLMCall.cost_usd), 0.0))
                .where(LLMCall.run_id == run_id)
            )
        ).scalar_one()
        run.total_cost_usd = float(total or 0.0)
