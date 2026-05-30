"""Brief agent — on-demand strategic synthesizer.

Pipeline:
1. Load PrincipalIdentity from DB → ctx.upstream["PIDAA"] (so SGA/DCAA/DEMCAA can read it).
2. Run SGA (identity-driven) → ctx.upstream["SGA"].
3. Run DCAA + DEMCAA sequentially (rate-limit safe) → ctx.upstream.
4. Single Sonnet synthesis call → produces the full brief JSON.
5. Persist a PrincipalBrief row.
6. Auto-escalate to Opus once if confidence < 0.6 (budget permitting).
"""
from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.agents.base import AgentContext, BaseAgent
from app.agents.dcaa import DCAA
from app.agents.demcaa import DEMCAA
from app.agents.sga import SGA
from app.db import session_scope
from app.eventbus.bus import publish_event
from app.llm.budget import BudgetExhaustedError
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.models.principal_brief import PrincipalBrief
from app.models.principal_identity import PrincipalIdentity
from app.schemas.agents import AgentResult
from app.schemas.brief import (
    BriefActionCard,
    BriefSource,
    BriefTopic,
    TopOpportunity,
    TopRisk,
)

_VALID_STANCES = {"lead", "engage", "avoid"}


class BriefAgent(BaseAgent):
    name = "Brief"
    default_tier = ModelTier.default
    max_cost_usd = 0.40

    async def _run(self, ctx: AgentContext) -> AgentResult:
        # --- 1. Hydrate PIDAA into ctx.upstream -------------------------------
        await self._inject_pidaa_upstream(ctx)

        ch = f"run.{ctx.run_id}" if ctx.run_id else None

        async def _step_event(step: str, label: str | None = None) -> None:
            if ch:
                await publish_event(ch, {"type": "step.started", "step": step, **(({"label": label}) if label else {})})

        async def _done_event(step: str) -> None:
            if ch:
                await publish_event(ch, {"type": "step.completed", "step": step})

        # --- 2. SGA (identity-driven, fresh news) -----------------------------
        await _step_event("sga", "Pulling sources")
        ctx.upstream["SGA"] = await SGA().run(ctx)
        await _done_event("sga")

        # --- 3. DCAA + DEMCAA (parallelized for performance) -------------------
        await _step_event("analysis", "Domain and audience analysis")
        
        # Run DCAA and DEMCAA in parallel since they don't depend on each other
        async def run_dcaa():
            try:
                return await DCAA().run(ctx)
            except Exception as exc:
                self.log.warning("brief.dcaa_failed", error=str(exc))
                return None
        
        async def run_demcaa():
            try:
                return await DEMCAA().run(ctx)
            except Exception as exc:
                self.log.warning("brief.demcaa_failed", error=str(exc))
                return None
        
        # Execute both agents in parallel
        dcaa_task = asyncio.create_task(run_dcaa())
        demcaa_task = asyncio.create_task(run_demcaa())
        
        # Wait for both to complete
        dcaa_result, demcaa_result = await asyncio.gather(dcaa_task, demcaa_task)
        
        if dcaa_result:
            ctx.upstream["DCAA"] = dcaa_result
        if demcaa_result:
            ctx.upstream["DEMCAA"] = demcaa_result
            
        await _done_event("analysis")

        await _step_event("brief", "Synthesising brief")

        # --- 4. Synthesis -----------------------------------------------------
        llm = get_llm_client()
        system = load_prompt("brief", pack_id=ctx.pack_id)

        sga_payload = ctx.upstream["SGA"].payload if "SGA" in ctx.upstream else {}
        sources_payload = (sga_payload.get("sources") or [])[:12]  # cap context
        valid_urls = {s.get("url") for s in sources_payload if s.get("url")}

        identity_payload = (
            ctx.upstream["PIDAA"].payload if "PIDAA" in ctx.upstream else {}
        )
        # Trim identity to keep prompt under rate limits
        identity_compact = self._compact_identity(identity_payload)

        domain_payload = (
            ctx.upstream["DCAA"].payload if "DCAA" in ctx.upstream else {}
        )
        demo_payload = (
            ctx.upstream["DEMCAA"].payload if "DEMCAA" in ctx.upstream else {}
        )

        user_msg = (
            f"## Principal identity\n{json.dumps(identity_compact, ensure_ascii=False)}\n\n"
            f"## Source pack ({len(sources_payload)} recent sources)\n"
            f"{json.dumps(sources_payload, ensure_ascii=False)}\n\n"
            f"## Domain briefing (DCAA)\n{json.dumps(domain_payload, ensure_ascii=False)}\n\n"
            f"## Demographic briefing (DEMCAA)\n{json.dumps(demo_payload, ensure_ascii=False)}\n\n"
            "Produce the Brief JSON object per the system contract. "
            "Every sources[].url MUST be one of the URLs in the source pack above."
        )

        resp = await llm.complete(
            agent=self.name,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
            tier=ModelTier.default,
            max_tokens=3600,
            run_id=ctx.run_id,
            json_mode=True,
            temperature=0.35,
        )

        cost_total = resp.cost_usd
        tokens_in_total = resp.input_tokens
        tokens_out_total = resp.output_tokens
        cache_r = resp.cache_read_tokens
        cache_w = resp.cache_write_tokens
        used_model = resp.model

        parsed = self._parse(resp.json_payload, valid_urls)
        if parsed is None:
            self.log.warning(
                "brief.parse_failed",
                model=resp.model,
                json_keys=list((resp.json_payload or {}).keys()) if resp.json_payload else [],
                text_preview=(resp.text or "")[:400],
            )

        # --- 5. Auto-escalate to Opus if low confidence -----------------------
        if parsed is None or parsed["confidence"] < 0.6:
            try:
                escalate = await llm.complete(
                    agent=self.name,
                    system=system,
                    messages=[
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": resp.text or ""},
                        {
                            "role": "user",
                            "content": (
                                "Your previous answer was low-confidence or malformed. "
                                "Re-derive with deeper reasoning. Same JSON contract. "
                                "Cite at least 2 sources by title or domain in `reasoning`."
                            ),
                        },
                    ],
                    tier=ModelTier.escalate,
                    max_tokens=3800,
                    run_id=ctx.run_id,
                    json_mode=True,
                    temperature=0.3,
                )
                new_parsed = self._parse(escalate.json_payload, valid_urls)
                if new_parsed is not None and (
                    parsed is None or new_parsed["confidence"] > parsed["confidence"]
                ):
                    parsed = new_parsed
                    used_model = escalate.model
                cost_total += escalate.cost_usd
                tokens_in_total += escalate.input_tokens
                tokens_out_total += escalate.output_tokens
                cache_r += escalate.cache_read_tokens
                cache_w += escalate.cache_write_tokens
            except BudgetExhaustedError as exc:
                self.log.warning("brief.opus_skip", reason=str(exc))

        if parsed is None:
            self.log.error(
                "brief.fallback_used",
                reason="both Sonnet and Opus passes failed to produce parseable JSON",
            )
            parsed = self._fallback_brief()

        await _done_event("brief")

        # --- 6. Persist PrincipalBrief row ------------------------------------
        profile_id_str = ctx.extra.get("profile_id") if isinstance(ctx.extra, dict) else None
        run_id_str = ctx.run_id if isinstance(ctx.run_id, str) else (str(ctx.run_id) if ctx.run_id else None)
        brief_row_id: str | None = None
        if profile_id_str:
            try:
                profile_uuid = UUID(str(profile_id_str))
                run_uuid = UUID(str(run_id_str)) if run_id_str else None
                async with session_scope() as db:
                    row = PrincipalBrief(
                        profile_id=profile_uuid,
                        run_id=run_uuid,
                        top_risk=parsed["top_risk"].model_dump(),
                        top_opportunity=parsed["top_opportunity"].model_dump(),
                        topics=[t.model_dump() for t in parsed["topics"]],
                        action_card=parsed["action_card"].model_dump(),
                        reasoning=parsed["reasoning"],
                        sources=[s.model_dump() for s in parsed["sources"]],
                        model=used_model,
                        cost_usd=round(cost_total, 6),
                        tokens_in=tokens_in_total,
                        tokens_out=tokens_out_total,
                        confidence=round(parsed["confidence"], 3),
                    )
                    db.add(row)
                    await db.flush()
                    brief_row_id = str(row.id)
            except Exception as exc:
                self.log.exception("brief.persist_failed", error=str(exc))

        return AgentResult(
            agent=self.name,
            summary=parsed["action_card"].what,
            payload={
                "brief_id": brief_row_id,
                "top_risk": parsed["top_risk"].model_dump(),
                "top_opportunity": parsed["top_opportunity"].model_dump(),
                "topics": [t.model_dump() for t in parsed["topics"]],
                "action_card": parsed["action_card"].model_dump(),
                "sources": [s.model_dump() for s in parsed["sources"]],
                "reasoning": parsed["reasoning"],
            },
            tokens_in=tokens_in_total,
            tokens_out=tokens_out_total,
            cache_read_tokens=cache_r,
            cache_write_tokens=cache_w,
            cost_usd=round(cost_total, 6),
            model=used_model,
            confidence=parsed["confidence"],
        )

    # --- helpers ------------------------------------------------------------

    async def _inject_pidaa_upstream(self, ctx: AgentContext) -> None:
        """Load PrincipalIdentity from DB and put it into ctx.upstream as a pseudo-AgentResult."""
        profile_id_raw = ctx.extra.get("profile_id") if isinstance(ctx.extra, dict) else None
        if not profile_id_raw:
            return
        try:
            profile_uuid = UUID(str(profile_id_raw))
        except (TypeError, ValueError):
            return
        async with session_scope() as db:
            res = await db.execute(
                select(PrincipalIdentity).where(PrincipalIdentity.profile_id == profile_uuid)
            )
            pi = res.scalar_one_or_none()
            if not pi:
                return
            payload = {
                "full_name": (pi.basics or {}).get("full_name", "")
                or (ctx.extra.get("full_name") if isinstance(ctx.extra, dict) else "") or "",
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

    @staticmethod
    def _compact_identity(p: dict[str, Any]) -> dict[str, Any]:
        """Trim PIDAA payload to keep prompt size reasonable."""
        keep = [
            "full_name", "basics", "current_position", "party_history",
            "electoral_record", "policy_stances", "controversies", "network",
            "coverage_gaps",
        ]
        return {k: p.get(k) for k in keep if p.get(k) is not None}

    @staticmethod
    def _parse(payload: dict[str, Any] | None, valid_urls: set[str]) -> dict[str, Any] | None:
        if not payload:
            return None
        try:
            tr = payload.get("top_risk") or {}
            top_risk = TopRisk(
                label=str(tr.get("label") or ""),
                severity=float(tr.get("severity") or 0.0),
                summary=str(tr.get("summary") or ""),
                time_horizon=str(tr.get("time_horizon") or "next 14 days"),
            )
            top_op_raw = payload.get("top_opportunity") or {}
            top_opportunity = TopOpportunity(
                label=str(top_op_raw.get("label") or ""),
                magnitude=float(top_op_raw.get("magnitude") or 0.0),
                summary=str(top_op_raw.get("summary") or ""),
                time_horizon=str(top_op_raw.get("time_horizon") or "next 14 days"),
            )

            topics: list[BriefTopic] = []
            for t in payload.get("topics") or []:
                if not isinstance(t, dict) or not t.get("topic"):
                    continue
                stance = str(t.get("stance") or "engage").lower()
                if stance not in _VALID_STANCES:
                    stance = "engage"
                topics.append(
                    BriefTopic(
                        topic=str(t["topic"]),
                        stance=stance,  # type: ignore[arg-type]
                        rationale=str(t.get("rationale") or ""),
                        angle=t.get("angle") or None,
                    )
                )
            topics = topics[:7]

            ac_raw = payload.get("action_card") or {}
            action_card = BriefActionCard(
                what=str(ac_raw.get("what") or ""),
                who=str(ac_raw.get("who") or ""),
                where=str(ac_raw.get("where") or ""),
                when=str(ac_raw.get("when") or ""),
                how=str(ac_raw.get("how") or ""),
                proof=str(ac_raw.get("proof") or ""),
                avoid=str(ac_raw.get("avoid") or ""),
                confidence=float(ac_raw.get("confidence") or 0.5),
                success_kpis=list(ac_raw.get("success_kpis") or []),
            )

            sources: list[BriefSource] = []
            for s in payload.get("sources") or []:
                url = (s or {}).get("url")
                if not url or url not in valid_urls:
                    continue  # reject invented urls
                sources.append(
                    BriefSource(
                        url=url,
                        title=s.get("title"),
                        domain=s.get("domain"),
                        published_at=s.get("published_at"),
                        credibility_score=float(s.get("credibility_score") or 0.5),
                        used_for=list(s.get("used_for") or []),
                    )
                )

            reasoning = str(payload.get("reasoning") or "")
            confidence = float(payload.get("confidence") or 0.5)

            # Lenient acceptance: only reject if literally every key field is empty.
            if not action_card.what and not top_risk.label and not top_opportunity.label:
                return None
            # Backfill any missing label so the UI never shows an empty card.
            if not top_risk.label:
                top_risk.label = "(top risk not identified)"
            if not top_opportunity.label:
                top_opportunity.label = "(top opportunity not identified)"
            if not action_card.what:
                action_card.what = "Hold posture; reassess after fresh source pull."

            return {
                "top_risk": top_risk,
                "top_opportunity": top_opportunity,
                "topics": topics,
                "action_card": action_card,
                "sources": sources,
                "reasoning": reasoning,
                "confidence": confidence,
            }
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _fallback_brief() -> dict[str, Any]:
        return {
            "top_risk": TopRisk(
                label="Insufficient signal — defer high-risk moves",
                severity=0.4,
                summary="The brief pipeline could not surface a confident top risk this run. Hold posture.",
                time_horizon="next 7 days",
            ),
            "top_opportunity": TopOpportunity(
                label="Re-run after coverage gaps are filled",
                magnitude=0.3,
                summary="Coverage is too thin to identify a confident opportunity. Re-run after fresh sources.",
                time_horizon="next 7 days",
            ),
            "topics": [],
            "action_card": BriefActionCard(
                what="Hold — do not initiate public messaging in the next 24 hours.",
                who="Principal + chief of staff only.",
                where="Internal only.",
                when="Next 24h; reassess after fresh source pull.",
                how="Silent monitoring. Pre-clear two contingency statements.",
                proof="None required.",
                avoid="Any social post, any spokesperson statement, any leak.",
                confidence=0.3,
                success_kpis=[
                    "No new broadcast pickup before next reassessment",
                    "No unforced narrative drift",
                ],
            ),
            "sources": [],
            "reasoning": "Fallback brief: synthesis pass did not produce a usable JSON payload.",
            "confidence": 0.3,
        }
