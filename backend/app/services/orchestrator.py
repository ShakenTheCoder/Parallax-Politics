"""Commander / orchestrator — runs the DAG and persists artifacts.

Two modes (selected by Run.meta.kind):
  pidaa_build  →  PIDAA only  (principal identity creation)
  brief_build  →  Brief agent (loads PIDAA, runs SGA + DCAA + DEMCAA internally, synthesizes)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select

from app.agents.base import AgentContext
from app.agents.brief import BriefAgent
from app.agents.pidaa import PIDAA
from app.config import get_settings
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
      - "brief_build" → Brief agent
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
            async with asyncio.timeout(get_settings().brief_run_timeout_seconds):
                await _run_brief_pipeline(run_id, ctx)
        elif run_kind == "audience_build":
            await _run_audience_pipeline(run_id, ctx)
        elif run_kind == "political_glossary_seed":
            from app.services.political_glossary import seed_glossary
            from app.services.wikidata_glossary import enrich_glossary_from_wikidata

            await seed_glossary()
            await enrich_glossary_from_wikidata()
        elif run_kind == "political_glossary_refresh":
            from app.services.political_glossary import refresh_figure

            await refresh_figure(UUID(run_meta["figure_id"]), run_id)
        else:
            log.warning("orchestrator.unknown_kind", kind=run_kind)
            await _run_brief_pipeline(run_id, ctx)

        await _finalize_run(run_id, status=RunStatus.completed)
        await publish_event(channel, {"type": "run.completed", "run_id": str(run_id)})

    except BudgetExhaustedError as exc:
        log.warning("orchestrator.budget_exhausted", error=str(exc))
        await _finalize_run(run_id, status=RunStatus.budget_exhausted, error=str(exc))
        await publish_event(channel, {"type": "run.budget_exhausted", "error": str(exc)})

    except TimeoutError:
        message = "Brief generation exceeded its two-minute live-analysis limit. Please retry."
        log.warning("orchestrator.timed_out", run_id=str(run_id), kind=run_kind)
        await _finalize_run(run_id, status=RunStatus.failed, error=message)
        await publish_event(channel, {"type": "run.failed", "error": message})

    except Exception as exc:
        log.exception("orchestrator.failed", error=str(exc))
        await _finalize_run(run_id, status=RunStatus.failed, error=str(exc))
        await publish_event(channel, {"type": "run.failed", "error": str(exc)})


# --- pipelines ---------------------------------------------------------------


async def _run_pidaa_pipeline(run_id: UUID, ctx: AgentContext) -> None:
    """Build the identity dossier, then derive the current competitor landscape."""
    from app.agents.competitor_analysis import CompetitorAnalysisAgent

    pidaa_result = await PIDAA().run(ctx)
    await _persist_artifact(run_id, "principal_identity", pidaa_result)
    ctx.upstream["PIDAA"] = pidaa_result

    competitor_result = await CompetitorAnalysisAgent().run(ctx)
    await _persist_artifact(run_id, "competitor_analysis", competitor_result)


async def _run_audience_pipeline(run_id: UUID, ctx: AgentContext) -> None:
    """Audience Center build — runs Personal, Competitors, and Contextual agents in parallel.
    Hydrates the principal's identity and previous briefings to make them context-aware.
    """
    import asyncio

    from app.agents.competitors_audience import CompetitorsAudienceAgent
    from app.agents.contextual_audience import ContextualAudienceAgent
    from app.agents.personal_audience import PersonalAudienceAgent

    # Hydrate context
    await _inject_pidaa_into_ctx(ctx)
    await _inject_latest_analysis_into_ctx(ctx)

    # Let UI know step started
    channel = f"run.{run_id}"
    await publish_event(
        channel,
        {"type": "step.started", "step": "audience_analysis", "label": "Running Audience Agents"},
    )

    # Run in parallel
    async def run_personal():
        try:
            return await PersonalAudienceAgent().run(ctx)
        except Exception as exc:
            log.warning("orchestrator.personal_audience_failed", error=str(exc))
            return None

    async def run_competitors():
        try:
            return await CompetitorsAudienceAgent().run(ctx)
        except Exception as exc:
            log.warning("orchestrator.competitors_audience_failed", error=str(exc))
            return None

    async def run_contextual():
        try:
            return await ContextualAudienceAgent().run(ctx)
        except Exception as exc:
            log.warning("orchestrator.contextual_audience_failed", error=str(exc))
            return None

    p_task = asyncio.create_task(run_personal())
    comp_task = asyncio.create_task(run_competitors())
    ctx_task = asyncio.create_task(run_contextual())

    p_res, comp_res, ctx_res = await asyncio.gather(p_task, comp_task, ctx_task)

    # Persist outputs as individual artifacts
    if p_res:
        ctx.upstream["PersonalAudience"] = p_res
        await _persist_artifact(run_id, "personal_audience_instructions", p_res)
    if comp_res:
        ctx.upstream["CompetitorsAudience"] = comp_res
        await _persist_artifact(run_id, "competitors_audience_instructions", comp_res)
    if ctx_res:
        ctx.upstream["ContextualAudience"] = ctx_res
        await _persist_artifact(run_id, "contextual_audience_instructions", ctx_res)

    # Now run Facebook Analysis leveraging the generated instructions
    await publish_event(
        channel,
        {
            "type": "step.started",
            "step": "facebook_analysis",
            "label": "Running Facebook Landscape Analysis",
        },
    )
    from app.agents.facebook_analysis import FacebookAnalysisAgent

    try:
        fb_res = await FacebookAnalysisAgent().run(ctx)
        if fb_res:
            await _persist_artifact(run_id, "facebook_analysis", fb_res)
    except Exception as exc:
        log.warning("orchestrator.facebook_analysis_failed", error=str(exc))

    await publish_event(channel, {"type": "step.completed", "step": "facebook_analysis"})
    await publish_event(channel, {"type": "step.completed", "step": "audience_analysis"})


async def _inject_pidaa_into_ctx(ctx: AgentContext) -> None:
    """Load PrincipalIdentity and inject it as pseudo-upstream PIDAA."""
    profile_id_raw = ctx.extra.get("profile_id") if isinstance(ctx.extra, dict) else None
    if not profile_id_raw:
        return
    try:
        profile_uuid = UUID(str(profile_id_raw))
    except (TypeError, ValueError):
        return

    from app.models.principal_identity import PrincipalIdentity

    async with session_scope() as db:
        res = await db.execute(
            select(PrincipalIdentity).where(PrincipalIdentity.profile_id == profile_uuid)
        )
        pi = res.scalar_one_or_none()
        if not pi:
            return
        payload = {
            "full_name": (pi.basics or {}).get("full_name", "")
            or (ctx.extra.get("full_name") if isinstance(ctx.extra, dict) else "")
            or "",
            "basics": pi.basics or {},
            "family": pi.family or {},
            "education": pi.education or {},
            "career_timeline": pi.career_timeline or {},
            "current_position": pi.current_position or {},
            "party_history": pi.party_history or {},
            "electoral_record": pi.electoral_record or {},
            "policy_stances": pi.policy_stances or {},
            "voice_signature": pi.voice_signature or {},
            "controversies": pi.controversies or {},
            "network": pi.network or {},
            "source_index": pi.source_index or {},
            "coverage_gaps": list(pi.coverage_gaps or []),
        }
        ctx.upstream["PIDAA"] = AgentResult(
            agent="PIDAA",
            summary=f"Identity dossier for {payload['full_name'] or 'principal'}",
            payload=payload,
        )


async def _inject_latest_analysis_into_ctx(ctx: AgentContext) -> None:
    """Load historical domain and demographic briefing artifacts and inject them."""
    profile_id_raw = ctx.extra.get("profile_id") if isinstance(ctx.extra, dict) else None
    if not profile_id_raw:
        return
    try:
        profile_uuid = UUID(str(profile_id_raw))
    except (TypeError, ValueError):
        return

    from app.models.artifact import Artifact

    async with session_scope() as db:
        # Latest domain briefing (DCAA)
        dcaa_res = await db.execute(
            select(Artifact)
            .join(Run)
            .where(Run.subject_id == profile_uuid)
            .where(Artifact.kind == "domain_briefing")
            .order_by(Artifact.created_at.desc())
            .limit(1)
        )
        dcaa_art = dcaa_res.scalar_one_or_none()
        if dcaa_art:
            ctx.upstream["DCAA"] = AgentResult(
                agent="DCAA",
                summary="Loaded from historical domain briefing",
                payload=dcaa_art.payload or {},
            )

        # Latest demographic briefing (DEMCAA)
        dem_res = await db.execute(
            select(Artifact)
            .join(Run)
            .where(Run.subject_id == profile_uuid)
            .where(Artifact.kind == "demographic_briefing")
            .order_by(Artifact.created_at.desc())
            .limit(1)
        )
        dem_art = dem_res.scalar_one_or_none()
        if dem_art:
            ctx.upstream["DEMCAA"] = AgentResult(
                agent="DEMCAA",
                summary="Loaded from historical demographic briefing",
                payload=dem_art.payload or {},
            )


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
                select(func.coalesce(func.sum(LLMCall.cost_usd), 0.0)).where(
                    LLMCall.run_id == run_id
                )
            )
        ).scalar_one()
        run.total_cost_usd = float(total or 0.0)
