"""PIDAA — Person Identity Deep Analyzer Agent.

Runs once at principal creation (after superadmin confirmation).
Builds the full 11-section identity knowledge base from multi-query EXA fan-out.

Pipeline:
1. 8-facet EXA fan-out (parallel, capped at 8 results each).
2. Cheap-tier rank + deduplicate → unified source pack (≤40 sources).
3. One structured LLM synthesis (default tier) covering every dossier section.
4. Aggregator pass: stitch + add source_index + coverage_gaps.
5. Persist PrincipalIdentity row, emit AgentResult.
"""
from __future__ import annotations

import asyncio  # still used for EXA fan-out gather
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.agents.base import AgentContext, BaseAgent
from app.db import session_scope
from app.identity import calculate_data_completeness, detect_gaps_from_pidaa_output
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.models.principal_identity import PrincipalIdentity
from app.schemas.agents import AgentResult, PrincipalIdentityArtifact
from app.search.exa import ExaSearchResult, get_exa_client
from app.utils.portraits import resolve_wikimedia_portrait

_SECTION_GROUPS = ("A", "B", "C", "D")
_GROUP_SECTIONS: dict[str, tuple[str, ...]] = {
    "A": ("basics", "family", "education"),
    "B": ("career_timeline", "current_position", "party_history", "electoral_record"),
    "C": ("policy_stances", "voice_signature"),
    "D": ("controversies", "network"),
}
_IDENTITY_KEYS = (
    "basics", "family", "education", "career_timeline", "current_position",
    "party_history", "electoral_record", "policy_stances", "voice_signature",
    "controversies", "network",
)
_EXA_FACETS = (
    "{name} Philippines politician biography",
    "{name} Philippines birthplace education career",
    "{name} Philippines party affiliation",
    "{name} Philippines Comelec election results votes",
    "{name} Philippines Senate hearing controversy",
    "{name} Philippines West Philippine Sea ICC stance",
    "{name} Philippines allies rivals political network",
    "{name} Philippines social media speech interview",
)


class PIDAA(BaseAgent):
    name = "PIDAA"
    default_tier = ModelTier.default
    max_cost_usd = 0.50

    async def _run(self, ctx: AgentContext) -> AgentResult:
        """Build a source-backed baseline dossier within a bounded few-second SLA."""
        candidate: dict[str, Any] = ctx.extra.get("confirmed_candidate") or {}
        full_name: str = candidate.get("full_name") or ctx.situation_prompt[:100]
        exa = get_exa_client()
        queries = [
            f"{full_name} Philippines politician biography current role",
            f"{full_name} Philippines party election record",
            f"{full_name} Philippines policy controversy",
        ]

        async def _bounded_search(query: str) -> list[ExaSearchResult]:
            try:
                return await asyncio.wait_for(
                    exa.search(query, num_results=5, text_chars=300),
                    timeout=3.0,
                )
            except Exception as exc:
                self.log.warning("pidaa.fast_search_skipped", query=query, error=str(exc))
                return []

        search_tasks = [_bounded_search(query) for query in queries]
        portrait_task = resolve_wikimedia_portrait(full_name)
        gathered = await asyncio.gather(*search_tasks, portrait_task)
        search_results = gathered[:-1]
        profile_image_url = gathered[-1] if isinstance(gathered[-1], str) else None

        pool: dict[str, ExaSearchResult] = {}
        for results in search_results:
            for item in results:
                pool.setdefault(item.url, item)
        ranked = sorted(
            pool.values(),
            key=lambda item: item.credibility_score * (item.score if item.score is not None else 0.5),
            reverse=True,
        )[:12]
        source_index = {"sources": [{
            "url": item.url, "title": item.title, "domain": item.domain,
            "published_at": item.published_at,
            "credibility_score": round(item.credibility_score, 2),
        } for item in ranked]}
        provenance_url = ranked[0].url if ranked else "domain_knowledge"
        basics = {
            "full_name": full_name,
            "aliases": list(candidate.get("aliases") or []),
            "born": candidate.get("born"),
            "birthplace": candidate.get("birthplace"),
            "region": candidate.get("region"),
            "profile_image_url": profile_image_url,
            "summary": candidate.get("one_line_bio"),
            "_provenance": {"source_url": provenance_url, "verified": bool(ranked)},
        }
        current_position = {
            "role": candidate.get("current_role"),
            "jurisdiction": candidate.get("region"),
            "_provenance": {"source_url": provenance_url, "verified": bool(ranked)},
        }
        party = candidate.get("party")
        merged: dict[str, Any] = {
            "basics": basics,
            "family": {},
            "education": {},
            "career_timeline": {},
            "current_position": current_position,
            "party_history": {"affiliations": [{"party": party}] if party else []},
            "electoral_record": {},
            "policy_stances": {},
            "voice_signature": {},
            "controversies": {},
            "network": {},
            "source_index": source_index,
        }
        coverage_gaps = [
            "Family and education require deep retrieval",
            "Career and electoral history require deep retrieval",
            "Policy, controversy, and network analysis require deep retrieval",
        ]
        structured_gaps = detect_gaps_from_pidaa_output(merged)
        data_completeness = calculate_data_completeness(merged)
        subject_id = UUID(str(ctx.extra["profile_id"])) if ctx.extra.get("profile_id") else None
        if subject_id:
            await self._persist(subject_id, full_name, merged, coverage_gaps, structured_gaps, data_completeness, profile_image_url)

        artifact = PrincipalIdentityArtifact(
            full_name=full_name,
            profile_image_url=profile_image_url,
            basics=basics,
            current_position=current_position,
            party_history=merged["party_history"],
            source_index=source_index,
            coverage_gaps=coverage_gaps,
            coverage_gaps_structured=structured_gaps,
            data_completeness_score=data_completeness,
        )
        return AgentResult(
            agent=self.name,
            summary=f"PIDAA fast identity built for {full_name} from {len(ranked)} ranked sources.",
            payload=artifact.model_dump(),
            model="deterministic-fast-path",
            confidence=float(candidate.get("confidence") or 0.5),
        )

    async def _run_deep(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        system = load_prompt("pidaa", pack_id=ctx.pack_id)
        exa = get_exa_client()

        candidate: dict[str, Any] = ctx.extra.get("confirmed_candidate") or {}
        full_name: str = candidate.get("full_name") or ctx.situation_prompt[:100]
        portrait_task = asyncio.create_task(resolve_wikimedia_portrait(full_name))

        # --- 1. EXA fan-out (parallel) ----------------------------------------
        queries = [f.format(name=full_name) for f in _EXA_FACETS]
        pool: dict[str, ExaSearchResult] = {}

        async def _exa_query(q: str) -> None:
            try:
                for r in await exa.search(q, num_results=8):
                    pool.setdefault(r.url, r)
            except Exception as exc:
                self.log.warning("pidaa.exa.error", query=q, error=str(exc))

        await asyncio.gather(*[_exa_query(q) for q in queries])
        resolved_portrait = await portrait_task
        if resolved_portrait:
            candidate["photo_url"] = resolved_portrait

        ranked = sorted(
            pool.values(),
            key=lambda r: r.credibility_score * (r.score if r.score is not None else 0.5),
            reverse=True,
        )[:40]

        sources_payload = [
            {
                "url": r.url,
                "title": r.title,
                "domain": r.domain,
                "published_at": r.published_at,
                "excerpt": (r.excerpt or "")[:200],
                "credibility_score": round(r.credibility_score, 2),
            }
            for r in ranked
        ]

        # --- 2. Build user prompt prefix shared across groups -----------------
        candidate_ctx = json.dumps(candidate, ensure_ascii=False)
        # One structured synthesis avoids four serial/queued model calls while
        # retaining enough evidence for the full dossier.
        _SOURCES_PER_GROUP = 24

        def _group_prompt(group: str) -> str:
            sections = ", ".join(_GROUP_SECTIONS[group])
            # Each group gets a slightly different slice for coverage breadth
            idx = list(_SECTION_GROUPS).index(group)
            start = (idx * _SOURCES_PER_GROUP) % max(1, len(sources_payload))
            slice_ = (sources_payload[start:start + _SOURCES_PER_GROUP]
                      or sources_payload[:_SOURCES_PER_GROUP])
            sources_ctx = json.dumps(slice_, ensure_ascii=False)
            return (
                f"Confirmed candidate:\n{candidate_ctx}\n\n"
                f"Source pack ({len(slice_)} of {len(sources_payload)} sources):\n{sources_ctx}\n\n"
                f"Section group: {group} — build sections: {sections}\n"
                "Return only the JSON object for these sections."
            )

        # --- 3. Parallel section-group LLM calls ------------------------------
        cost_total = 0.0
        tokens_in_total = 0
        tokens_out_total = 0
        cache_r = 0
        cache_w = 0
        used_model = ""

        async def _call_group(group: str) -> dict[str, Any]:
            nonlocal cost_total, tokens_in_total, tokens_out_total, cache_r, cache_w, used_model
            resp = await llm.complete(
                agent=self.name,
                system=system,
                messages=[{"role": "user", "content": _group_prompt(group)}],
                tier=ModelTier.default,
                max_tokens=1400,
                run_id=ctx.run_id,
                json_mode=True,
                temperature=0.25,
            )
            cost_total += resp.cost_usd
            tokens_in_total += resp.input_tokens
            tokens_out_total += resp.output_tokens
            cache_r += resp.cache_read_tokens
            cache_w += resp.cache_write_tokens
            used_model = resp.model
            return resp.json_payload or {}

        group_results = await asyncio.gather(*[_call_group(group) for group in _SECTION_GROUPS])

        # --- 4. Aggregate sections --------------------------------------------
        merged: dict[str, Any] = {}
        for result in group_results:
            for key in _IDENTITY_KEYS:
                if key in result:
                    merged[key] = result[key]
        profile_image_url = candidate.get("photo_url") or (merged.get("basics") or {}).get("profile_image_url")

        # Build source_index from top-12 sources
        source_index = {
            "sources": [
                {
                    "url": s["url"],
                    "title": s["title"],
                    "domain": s["domain"],
                    "published_at": s["published_at"],
                    "credibility_score": s["credibility_score"],
                }
                for s in sources_payload[:12]
            ]
        }
        merged["source_index"] = source_index

        # Collect coverage_gaps from all group outputs
        all_gaps: list[str] = []
        for result in group_results:
            if isinstance(result.get("coverage_gaps"), list):
                all_gaps.extend(result["coverage_gaps"])
        coverage_gaps = list(dict.fromkeys(all_gaps))

        # --- 5. Detect structured gaps ----------------------------------------
        structured_gaps = detect_gaps_from_pidaa_output(merged)
        data_completeness = calculate_data_completeness(merged)

        # --- 6. Persist PrincipalIdentity row ---------------------------------
        subject_id: UUID | None = (
            UUID(str(ctx.extra["profile_id"])) if ctx.extra.get("profile_id") else None
        )
        if subject_id:
            await self._persist(subject_id, full_name, merged, coverage_gaps, structured_gaps, data_completeness, profile_image_url)

        # --- 7. Build artifact -------------------------------------------------
        artifact = PrincipalIdentityArtifact(
            full_name=full_name,
            profile_image_url=profile_image_url,
            basics=merged.get("basics") or {},
            family=merged.get("family") or {},
            education=merged.get("education") or {},
            career_timeline=merged.get("career_timeline") or {},
            current_position=merged.get("current_position") or {},
            party_history=merged.get("party_history") or {},
            electoral_record=merged.get("electoral_record") or {},
            policy_stances=merged.get("policy_stances") or {},
            voice_signature=merged.get("voice_signature") or {},
            controversies=merged.get("controversies") or {},
            network=merged.get("network") or {},
            source_index=source_index,
            coverage_gaps=coverage_gaps,
            coverage_gaps_structured=structured_gaps,
            data_completeness_score=data_completeness,
        )

        result = AgentResult(
            agent=self.name,
            summary=f"PIDAA identity built for {full_name} — {len(sources_payload)} sources, {len(coverage_gaps)} gaps, completeness {data_completeness:.0%}.",
            payload=artifact.model_dump(),
            tokens_in=tokens_in_total,
            tokens_out=tokens_out_total,
            cache_read_tokens=cache_r,
            cache_write_tokens=cache_w,
            cost_usd=round(cost_total, 6),
            model=used_model,
            confidence=0.75,
        )

        # Auto-trigger SCDRA if gaps exist and enabled
        if structured_gaps and ctx.extra.get("auto_scdra", True):
            try:
                from app.agents.scdra import SCDRA
                scdra = SCDRA()
                scdra_ctx = AgentContext(
                    run_id=ctx.run_id,
                    situation_prompt=ctx.situation_prompt,
                    subject_slug=ctx.subject_slug,
                    pack_id=ctx.pack_id,
                    upstream={"PIDAA": result},
                    extra={
                        **ctx.extra,
                        "profile_id": str(subject_id) if subject_id else None,
                    },
                )
                await scdra.run(scdra_ctx)
            except Exception as exc:
                self.log.warning("pidaa.scdra_trigger_failed", error=str(exc))
                # Don't fail PIDAA if SCDRA fails

        return result

    async def _persist(
        self,
        profile_id: UUID,
        full_name: str,
        sections: dict[str, Any],
        coverage_gaps: list[str],
        structured_gaps: list[dict[str, Any]],
        data_completeness: float,
        profile_image_url: str | None,
    ) -> None:
        async with session_scope() as db:
            res = await db.execute(
                select(PrincipalIdentity).where(PrincipalIdentity.profile_id == profile_id)
            )
            pi = res.scalar_one_or_none()
            if not pi:
                pi = PrincipalIdentity(profile_id=profile_id)
                db.add(pi)

            for key in _IDENTITY_KEYS + ("source_index",):
                if key in sections:
                    setattr(pi, key, sections[key])
            pi.coverage_gaps = coverage_gaps
            pi.coverage_gaps_structured = structured_gaps
            pi.data_completeness_score = data_completeness
            pi.raw_dossier = sections
            # Clear stale or mismatched portraits when exact identity resolution
            # cannot verify an image on a rerun.
            pi.profile_image_url = profile_image_url
            pi.status = "ready"
            pi.built_at = datetime.now(UTC)
