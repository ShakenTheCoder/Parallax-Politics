from __future__ import annotations

import contextlib
from uuid import UUID

from pydantic import BaseModel, Field

from app.agents._helpers import identity_brief
from app.agents.base import AgentContext, BaseAgent
from app.db import session_scope
from app.llm.client import get_llm_client
from app.llm.router import ModelTier
from app.models.competitor import Competitor
from app.schemas.agents import AgentResult


class CompetitorItem(BaseModel):
    name: str = Field(description="Name of the competitor")
    party: str | None = Field(None, description="Political party of the competitor, if any")
    match_score: float = Field(description="Multiple factor analysis score 0.0 to 1.0 indicating threat level")
    reasoning: str = Field(description="Rationale for why they are a competitor")
    overlap_areas: list[str] = Field(default_factory=list, description="Policy or demographic overlap areas")


class CompetitorAnalysisResult(BaseModel):
    competitors: list[CompetitorItem] = Field(default_factory=list, description="List of identified competitors")


class CompetitorAnalysisAgent(BaseAgent):
    name = "CompetitorAnalysis"
    default_tier = ModelTier.default
    max_cost_usd = 0.20

    async def _run(self, ctx: AgentContext) -> AgentResult:
        llm = get_llm_client()
        
        system_prompt = (
            "You are a political intelligence analyst. Perform a multiple-factor analysis "
            "to identify the top political competitors to the given principal candidate.\n"
            "Factors to consider:\n"
            "1. Geographic overlap\n"
            "2. Demographic target audience overlap\n"
            "3. Policy stances (opposing or competing for same base)\n"
            "4. Electoral history and upcoming races\n\n"
            "Return a JSON object matching the requested schema with a list of competitors."
        )

        user_content = (
            f"Principal Identity:\n{identity_brief(ctx, max_chars=3000)}\n\n"
            "Identify 3-5 top political competitors. Score them from 0.0 (low threat) to 1.0 (high threat)."
        )

        resp = await llm.complete(
            agent=self.name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
            tier=self.default_tier,
            max_tokens=2000,
            run_id=ctx.run_id,
            json_mode=True,
            temperature=0.4,
        )

        payload = resp.json_payload or {}
        
        try:
            parsed = CompetitorAnalysisResult.model_validate(payload)
        except Exception:
            parsed = CompetitorAnalysisResult(competitors=[])
            if isinstance(payload.get("competitors"), list):
                for c in payload["competitors"]:
                    with contextlib.suppress(Exception):
                        parsed.competitors.append(CompetitorItem.model_validate(c))

        # Persist to database if we have a profile_id
        profile_id_raw = ctx.extra.get("profile_id")
        if profile_id_raw:
            try:
                profile_id = UUID(str(profile_id_raw))
                await self._persist_competitors(profile_id, parsed.competitors)
            except ValueError as e:
                self.log.warning("competitor_analysis.invalid_profile_id", error=str(e))

        return AgentResult(
            agent=self.name,
            summary=f"Identified {len(parsed.competitors)} competitors through multi-factor analysis.",
            payload=parsed.model_dump(),
            tokens_in=resp.input_tokens,
            tokens_out=resp.output_tokens,
            cache_read_tokens=resp.cache_read_tokens,
            cache_write_tokens=resp.cache_write_tokens,
            cost_usd=resp.cost_usd,
            model=resp.model,
            confidence=0.8,
        )

    async def _persist_competitors(self, profile_id: UUID, competitors: list[CompetitorItem]) -> None:
        async with session_scope() as db:
            from sqlalchemy import delete
            # Delete old competitors if re-running
            await db.execute(delete(Competitor).where(Competitor.profile_id == profile_id))
            
            for c in competitors:
                comp_db = Competitor(
                    profile_id=profile_id,
                    name=c.name,
                    party=c.party,
                    match_score=c.match_score,
                    reasoning=c.reasoning,
                    overlap_areas=c.overlap_areas,
                )
                db.add(comp_db)
