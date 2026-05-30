"""DCAA — Domain Context Aware Agent (Philippine politics)."""
from __future__ import annotations

from app.agents._helpers import identity_brief, upstream_brief
from app.agents.base import AgentContext, BaseAgent
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.schemas.agents import AgentResult, DomainBriefing, EvidenceRef


class DCAA(BaseAgent):
    name = "DCAA"
    default_tier = ModelTier.default
    max_cost_usd = 0.08

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        system = load_prompt("dcaa", pack_id=ctx.pack_id)

        user = (
            f"Principal identity digest:\n{identity_brief(ctx, max_chars=1500)}\n\n"
            f"Upstream agent outputs (e.g. SGA source pack):\n{upstream_brief(ctx)}\n\n"
            "Produce a DomainBriefing JSON object focused on the principal's CURRENT "
            "institutional and political context (no situation prompt). Surface concepts, "
            "institutional constraints, precedent cases, and risk flags relevant to the "
            "principal right now."
        )

        resp = await llm.complete(
            agent=self.name,
            system=system,
            messages=[{"role": "user", "content": user}],
            tier=self.default_tier,
            max_tokens=2500,
            run_id=ctx.run_id,
            json_mode=True,
            temperature=0.3,
        )

        payload = resp.json_payload or {}
        briefing = DomainBriefing(
            relevant_concepts=list(payload.get("relevant_concepts") or []),
            institutional_constraints=list(payload.get("institutional_constraints") or []),
            precedent_cases=list(payload.get("precedent_cases") or []),
            risk_flags=list(payload.get("risk_flags") or []),
            notes=payload.get("notes"),
        )

        evidence = [
            EvidenceRef(claim=f"DCAA risk flag: {f}", confidence=0.6)
            for f in briefing.risk_flags
        ]

        return AgentResult(
            agent=self.name,
            summary=briefing.notes or f"{len(briefing.relevant_concepts)} concepts surfaced.",
            payload=briefing.model_dump(),
            evidence=evidence,
            tokens_in=resp.input_tokens,
            tokens_out=resp.output_tokens,
            cache_read_tokens=resp.cache_read_tokens,
            cache_write_tokens=resp.cache_write_tokens,
            cost_usd=resp.cost_usd,
            model=resp.model,
            confidence=0.65,
        )
