"""CompetitorsAudienceAgent — creates extraction instructions for rival monitoring."""

from __future__ import annotations

import json

from app.agents._helpers import identity_brief
from app.agents.base import AgentContext, BaseAgent
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.schemas.agents import AgentResult
from app.schemas.audience import CompetitorsAudienceInstructions


class CompetitorsAudienceAgent(BaseAgent):
    name = "CompetitorsAudience"
    default_tier = ModelTier.default
    max_cost_usd = 0.08

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        system = load_prompt("competitors_audience", pack_id=ctx.pack_id)

        # Grab domain context output if available in upstream
        dcaa_res = ctx.get("DCAA")
        dcaa_brief = ""
        if dcaa_res:
            dcaa_brief = (
                f"\n\nDomain Context output:\n{json.dumps(dcaa_res.payload, ensure_ascii=False)}"
            )

        user = (
            f"Principal identity digest:\n{identity_brief(ctx, max_chars=1500)}{dcaa_brief}\n\n"
            f"Situation prompt/focus (if any):\n{ctx.situation_prompt or '(none)'}\n\n"
            "Identify the political rivals and competitors for this principal, and produce "
            "a CompetitorsAudienceInstructions JSON object containing primary competitors, "
            "comparison keywords, topics of contention, and specific tracking priorities."
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
        instructions = CompetitorsAudienceInstructions(
            primary_competitors=list(payload.get("primary_competitors") or []),
            comparison_keywords=list(payload.get("comparison_keywords") or []),
            topics_of_contention=list(payload.get("topics_of_contention") or []),
            tracking_priorities=list(payload.get("tracking_priorities") or []),
            instructions_summary=str(
                payload.get("instructions_summary")
                or "Extract competitor brand/faction activities."
            ),
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
