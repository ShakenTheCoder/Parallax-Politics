"""Brief agent I/O contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

TopicStance = Literal["lead", "engage", "avoid"]


class TopRisk(BaseModel):
    label: str
    severity: float = Field(ge=0.0, le=1.0)
    summary: str
    time_horizon: str = "next 14 days"


class TopOpportunity(BaseModel):
    label: str
    magnitude: float = Field(ge=0.0, le=1.0)
    summary: str
    time_horizon: str = "next 14 days"


class BriefTopic(BaseModel):
    topic: str
    stance: TopicStance
    rationale: str
    angle: str | None = None  # suggested framing if stance is lead/engage


class BriefActionCard(BaseModel):
    """The principal's next move — same shape as the old ActionCard, but Brief-scoped."""

    what: str
    who: str
    where: str
    when: str
    how: str
    proof: str
    avoid: str
    confidence: float = Field(ge=0.0, le=1.0)
    success_kpis: list[str] = Field(default_factory=list)


class BriefSource(BaseModel):
    url: str
    title: str | None = None
    domain: str | None = None
    published_at: str | None = None
    credibility_score: float = Field(ge=0.0, le=1.0, default=0.5)
    used_for: list[str] = Field(default_factory=list)  # ["risk", "opportunity", "topic:wps", ...]


# --- API I/O ----------------------------------------------------------------


class BriefSummary(BaseModel):
    """Lightweight row for history list."""

    id: UUID
    created_at: datetime
    top_risk_label: str
    top_opportunity_label: str
    action_what: str
    confidence: float
    cost_usd: float


class BriefOut(BaseModel):
    """Full brief detail."""

    id: UUID
    profile_id: UUID
    run_id: UUID | None = None
    created_at: datetime
    top_risk: TopRisk
    top_opportunity: TopOpportunity
    topics: list[BriefTopic]
    action_card: BriefActionCard
    reasoning: str
    sources: list[BriefSource]
    model: str | None = None
    cost_usd: float = 0.0
    confidence: float = 0.0
    command_view: dict[str, Any] | None = None


class BriefGenerateOut(BaseModel):
    run_id: UUID
    status: str = "queued"


class BriefActiveOut(BaseModel):
    """The current brief run, or an explicit idle state."""

    run_id: UUID | None = None
    status: str = "idle"
