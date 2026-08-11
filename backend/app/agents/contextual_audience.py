"""ContextualAudienceAgent — creates macro-demographic/regional extraction instructions."""
from __future__ import annotations

import json
from app.agents._helpers import identity_brief
from app.agents.base import AgentContext, BaseAgent
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.schemas.agents import AgentResult
from app.schemas.audience import ContextualAudienceInstructions


class ContextualAudienceAgent(BaseAgent):
    name = "ContextualAudience"
    default_tier = ModelTier.default
    max_cost_usd = 0.08

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        system = load_prompt("contextual_audience", pack_id=ctx.pack_id)

        # Grab demographic context output if available in upstream
        demcaa_res = ctx.get("DEMCAA")
        demcaa_brief = ""
        if demcaa_res:
            demcaa_brief = f"\n\nDemographic Context output:\n{json.dumps(demcaa_res.payload, ensure_ascii=False)}"

        user = (
            f"Principal identity digest:\n{identity_brief(ctx, max_chars=1500)}{demcaa_brief}\n\n"
            f"Situation prompt/focus (if any):\n{ctx.situation_prompt or '(none)'}\n\n"
            "Produce a ContextualAudienceInstructions JSON object identifying geographic focus areas, "
            "demographic segments, trending local issues, and optimal scraping channels/media mix."
        )

        resp = await llm.complete(
            agent=self.name,
            system=system,
            messages=[{"role": "user", "content": user}],
            tier=self.default_tier,
            max_tokens=2000,
            run_id=ctx.run_id,
            json_mode=True,
            temperature=0.3,
        )

        payload = resp.json_payload or {}
        instructions = ContextualAudienceInstructions(
            target_regions=list(payload.get("target_regions") or []),
            demographic_segments=list(payload.get("demographic_segments") or []),
            salient_issues=list(payload.get("salient_issues") or []),
            channel_mix=list(payload.get("channel_mix") or []),
            instructions_summary=str(payload.get("instructions_summary") or "Extract contextual regional and demographic insights."),
        )

        return AgentResult(
            agent=self.name,
            summary=instructions.instructions_summary,
            payload=instructions.model_dump(),
            tokens_in=resp.input_tokens,
            tokens_out=resp.output_tokens,
            cache_read_tokens=resp.cache_read_tokens,
            cache_write_tokens=resp.cache_write_tokens,
            cost_usd=resp.cost_usd,
            model=resp.model,
            confidence=0.75,
        )
