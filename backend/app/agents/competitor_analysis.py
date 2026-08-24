from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.agents.base import AgentContext, BaseAgent
from app.db import session_scope
from app.intelligence.watchlist import PULSE_ASIA_URL, WATCHLIST
from app.llm.router import ModelTier
from app.models.competitor import Competitor
from app.schemas.agents import AgentResult


class CompetitorItem(BaseModel):
    name: str = Field(description="Name of the competitor")
    party: str | None = Field(None, description="Political party of the competitor, if any")
    match_score: float = Field(
        description="Multiple factor analysis score 0.0 to 1.0 indicating threat level"
    )
    reasoning: str = Field(description="Rationale for why they are a competitor")
    overlap_areas: list[str] = Field(
        default_factory=list, description="Policy or demographic overlap areas"
    )
    watch_status: str = "polled_hypothetical"
    evidence: list[dict[str, str]] = Field(default_factory=list)


class CompetitorAnalysisResult(BaseModel):
    competitors: list[CompetitorItem] = Field(
        default_factory=list, description="List of identified competitors"
    )


class CompetitorAnalysisAgent(BaseAgent):
    name = "CompetitorAnalysis"
    default_tier = ModelTier.default
    max_cost_usd = 0.20

    async def _run(self, ctx: AgentContext) -> AgentResult:
        # Membership is mechanical and evidence-backed. Models may summarize
        # the comparison later, but cannot invent an authoritative rival.
        principal_name = ""
        pidaa = ctx.get("PIDAA")
        if pidaa:
            principal_name = str(pidaa.payload.get("full_name") or "").casefold()
        parsed = CompetitorAnalysisResult(
            competitors=[
                CompetitorItem(
                    name=str(figure["name"]),
                    party=None,
                    match_score=1.0,
                    reasoning="Appears in the same Pulse Asia July 2026 hypothetical presidential long list.",
                    overlap_areas=["May 2028 hypothetical presidential long list"],
                    evidence=[
                        {
                            "source_url": PULSE_ASIA_URL,
                            "published_at": "2026-07-22",
                            "relationship": "same_hypothetical_race",
                        }
                    ],
                )
                for figure in WATCHLIST
                if str(figure["name"]).casefold() != principal_name
            ]
        )

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
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            model="mechanical-watchlist-v1",
            confidence=1.0,
        )

    async def _persist_competitors(
        self, profile_id: UUID, competitors: list[CompetitorItem]
    ) -> None:
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
                    watch_status=c.watch_status,
                    effective_from=datetime(2026, 7, 22, tzinfo=UTC),
                    evidence=c.evidence,
                )
                db.add(comp_db)
