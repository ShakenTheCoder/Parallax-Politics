"""DEMCAA — Demographic Context Aware Agent (Philippines)."""

from __future__ import annotations

from app.agents._helpers import identity_brief, upstream_brief
from app.agents.base import AgentContext, BaseAgent
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.schemas.agents import AgentResult, DemographicBriefing, DemographicCohort


class DEMCAA(BaseAgent):
    name = "DEMCAA"
    default_tier = ModelTier.default
    max_cost_usd = 0.08

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        system = load_prompt("demcaa", pack_id=ctx.pack_id)

        user = (
            f"Principal identity digest:\n{identity_brief(ctx, max_chars=1500)}\n\n"
            f"Upstream agent outputs (e.g. SGA source pack):\n{upstream_brief(ctx)}\n\n"
            "Produce a DemographicBriefing JSON object describing the principal's "
            "audience cohorts in the Philippines (no situation prompt). For each cohort, "
            "identify salient issues and media mix relevant to the principal's standing."
        )

        resp = await llm.complete(
            agent=self.name,
            system=system,
            messages=[{"role": "user", "content": user}],
            tier=self.default_tier,
            max_tokens=1000,
            run_id=ctx.run_id,
            json_mode=True,
            temperature=0.3,
        )

        payload = resp.json_payload or {}
        cohorts: list[DemographicCohort] = []
        for c in payload.get("cohorts") or []:
            if not isinstance(c, dict) or not c.get("name"):
                continue
            cohorts.append(
                DemographicCohort(
                    name=str(c["name"]),
                    share_pct=c.get("share_pct"),
                    salient_issues=list(c.get("salient_issues") or []),
                    media_mix={
                        k: float(v)
                        for k, v in (c.get("media_mix") or {}).items()
                        if isinstance(v, (int, float))
                    },
                )
            )

        brief = DemographicBriefing(
            region=str(payload.get("region") or "Philippines"),
            cohorts=cohorts,
            notes=payload.get("notes"),
        )

        return AgentResult(
            agent=self.name,
            summary=brief.notes or f"{len(cohorts)} cohorts profiled.",
            payload=brief.model_dump(),
            tokens_in=resp.input_tokens,
            tokens_out=resp.output_tokens,
            cache_read_tokens=resp.cache_read_tokens,
            cache_write_tokens=resp.cache_write_tokens,
            cost_usd=resp.cost_usd,
            model=resp.model,
            confidence=0.6,
        )
