"""PersonalAudienceAgent — translates principal profile into data scraping instructions."""

from __future__ import annotations

from app.agents._helpers import identity_brief
from app.agents.base import AgentContext, BaseAgent
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.schemas.agents import AgentResult
from app.schemas.audience import PersonalAudienceInstructions


class PersonalAudienceAgent(BaseAgent):
    name = "PersonalAudience"
    default_tier = ModelTier.default
    max_cost_usd = 0.08

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        system = load_prompt("personal_audience", pack_id=ctx.pack_id)

        user = (
            f"Principal identity digest:\n{identity_brief(ctx, max_chars=2000)}\n\n"
            f"Situation prompt/focus (if any):\n{ctx.situation_prompt or '(none)'}\n\n"
            "Produce a PersonalAudienceInstructions JSON object specifying extraction queries, "
            "focus keywords, domains to monitor, priority topics, and data extraction fields "
            "tailored to the principal's personal brand and profile."
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
        instructions = PersonalAudienceInstructions(
            target_name=str(payload.get("target_name") or ctx.subject_slug or "Unknown Principal"),
            aliases=list(payload.get("aliases") or []),
            focus_keywords=list(payload.get("focus_keywords") or []),
            domains_to_monitor=list(payload.get("domains_to_monitor") or []),
            priority_topics=list(payload.get("priority_topics") or []),
            extraction_fields=list(payload.get("extraction_fields") or []),
            instructions_summary=str(
                payload.get("instructions_summary") or "Extract personal brand information."
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
            confidence=0.8,
        )
