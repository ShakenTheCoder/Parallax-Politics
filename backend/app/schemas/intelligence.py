"""Strict public contracts for intelligence collection and review."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceAuthority(StrEnum):
    official_api = "official_api"
    licensed_feed = "licensed_feed"
    public_web = "public_web"
    representative_poll = "representative_poll"
    consented_panel = "consented_panel"


class CollectionSourceCreate(StrictModel):
    name: str = Field(min_length=2, max_length=160)
    base_url: AnyHttpUrl
    authority: SourceAuthority
    connector_kind: str = Field(
        default="scrapling", pattern=r"^(scrapling|rss|official_api|licensed_feed)$"
    )
    schedule_minutes: int = Field(default=15, ge=15, le=1440)
    robots_observed: bool = True
    allowed_paths: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("allowed_paths")
    @classmethod
    def validate_paths(cls, paths: list[str]) -> list[str]:
        for path in paths:
            if not path.startswith("/") or ".." in path or len(path) > 240:
                raise ValueError("allowed paths must be bounded absolute URL paths")
        return paths

    @model_validator(mode="after")
    def validate_connector_authority(self) -> CollectionSourceCreate:
        expected = {
            SourceAuthority.public_web: {"scrapling", "rss"},
            SourceAuthority.official_api: {"official_api"},
            SourceAuthority.licensed_feed: {"licensed_feed"},
            SourceAuthority.representative_poll: {"licensed_feed"},
            SourceAuthority.consented_panel: {"licensed_feed"},
        }[self.authority]
        if self.connector_kind not in expected:
            choices = " or ".join(sorted(expected))
            raise ValueError(f"{self.authority.value} sources require the {choices} connector")
        if self.connector_kind == "scrapling" and not self.robots_observed:
            raise ValueError("public web collection must observe robots policy")
        return self


class CollectionSourceOut(BaseModel):
    id: UUID
    name: str
    base_url: str
    authority: str
    connector_kind: str
    status: str
    schedule_minutes: int
    robots_observed: bool
    allowed_paths: list[str]
    last_collected_at: datetime | None


class CollectionRequest(StrictModel):
    subject_id: UUID | None = None
    path: str = Field(default="/", min_length=1, max_length=500)
    css_selector: str | None = Field(default=None, min_length=1, max_length=240)
    language: str = Field(default="und", pattern=r"^(und|en|fil)$")
    event_type: str = Field(default="public_document", min_length=2, max_length=60)

    @field_validator("path")
    @classmethod
    def safe_path(cls, path: str) -> str:
        if not path.startswith("/") or path.startswith("//") or ".." in path:
            raise ValueError("path must be a same-origin absolute path")
        return path


class CollectionSubscriptionCreate(CollectionRequest):
    subject_id: UUID


class CollectionSubscriptionOut(BaseModel):
    id: UUID
    collection_source_id: UUID
    subject_id: UUID
    path: str
    language: str
    event_type: str
    status: str
    next_due_at: datetime
    last_collected_at: datetime | None
    last_error: str | None
    consecutive_failures: int


class SignalOut(BaseModel):
    id: UUID
    subject_id: UUID | None
    platform: str
    event_type: str
    language: str
    title: str | None
    content_excerpt: str
    url: str
    published_at: datetime | None
    observed_at: datetime
    engagement: dict[str, Any]
    provenance: dict[str, Any]


class CollectionResult(BaseModel):
    created: bool
    signal: SignalOut


class FreeFeedCollectionOut(BaseModel):
    feeds_checked: int = Field(default=0, ge=0)
    entries_seen: int = Field(default=0, ge=0)
    signals_created: int = Field(default=0, ge=0)
    duplicates: int = Field(default=0, ge=0)
    unmatched: int = Field(default=0, ge=0)
    appearances_created: int = Field(default=0, ge=0)
    opinions_created: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)


class CohortSpec(StrictModel):
    label: str = Field(min_length=2, max_length=160)
    sample_size: int = Field(ge=100, le=10_000_000)
    regions: list[str] = Field(default_factory=lambda: ["Philippines"], min_length=1, max_length=20)
    age_band: str | None = Field(default=None, max_length=40)
    evidence_basis: str = Field(min_length=3, max_length=240)


class ScenarioCreate(StrictModel):
    subject_id: UUID | None = None
    title: str = Field(min_length=3, max_length=200)
    narrative: str = Field(min_length=20, max_length=4000)
    proposed_action: str = Field(min_length=20, max_length=4000)
    cohort: CohortSpec
    effective_at: datetime | None = None


class ForecastRange(BaseModel):
    direction: str = Field(pattern=r"^(positive|negative|mixed|insufficient_evidence)$")
    lower_pct: float = Field(ge=-100, le=100)
    central_pct: float = Field(ge=-100, le=100)
    upper_pct: float = Field(ge=-100, le=100)
    confidence: float = Field(ge=0, le=1)


class ScenarioOut(BaseModel):
    id: UUID
    subject_id: UUID
    title: str
    narrative: str
    proposed_action: str
    cohort: dict[str, Any]
    effective_at: datetime
    status: str
    forecast: dict[str, Any]
    assumptions: list[str]
    evidence: list[dict[str, Any]]
    model_version: str
    created_at: datetime


class VerdictOut(BaseModel):
    id: UUID
    scenario_id: UUID
    status: str
    recommendation: str
    rationale: str
    confidence: float
    risk_level: str
    critic: dict[str, Any]
    evidence: list[dict[str, Any]]
    expires_at: datetime
    approved_by: UUID | None
    approved_at: datetime | None
    created_at: datetime


class ScenarioCreateResult(BaseModel):
    scenario: ScenarioOut
    verdict: VerdictOut


class VerdictDecision(StrictModel):
    decision: str = Field(pattern=r"^(approved|rejected)$")
    review_note: str = Field(min_length=3, max_length=1000)


class PresenceMetric(BaseModel):
    subject_id: UUID
    full_name: str
    signal_count: int
    engagement_total: int
    share_of_voice_pct: float
    latest_signal_at: datetime | None


class IntelligenceOverview(BaseModel):
    generated_at: datetime
    freshness_minutes: int | None
    monitored_candidates: int
    signals_24h: int
    sources_active: int
    scenarios_pending_review: int
    presence: list[PresenceMetric]
    recent_signals: list[SignalOut]
    data_notice: str
    election: dict[str, Any] | None = None
    command_view: dict[str, Any] | None = None
    momentum: dict[str, Any] | None = None
    coverage: dict[str, Any] | None = None
    latest_poll: dict[str, Any] | None = None


class CommandViewOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    subject: str
    watch_status: str
    score: float | None
    previous_score: float | None
    delta: float | None
    rank: int | None
    rank_suppressed: bool
    coverage_confidence: float = Field(ge=0, le=1)
    model_version: str
    headline: str


BriefImportance = Literal["critical", "high", "medium", "low", "unrated"]
ActivityWindow = Literal["6h", "24h", "7d"]
ActivityLayer = Literal[
    "direct_appearance", "public_statement", "indirect_coverage", "public_reaction"
]


class BriefIdentityOut(BaseModel):
    name: str
    position: str | None = None
    portrait_url: str | None = None


class BriefScoreOut(BaseModel):
    value: float | None = None
    delta: float | None = None
    updated_at: datetime | None = None


class BriefWatchlistRatingOut(BaseModel):
    figure_id: UUID | None = None
    is_principal: bool = False
    rank: int | None = None
    name: str
    position: str | None = None
    portrait_url: str | None = None
    score: float | None = None
    delta: float | None = None
    monitoring_state: Literal["active", "quiet", "emerging"] = "quiet"
    analyzed_appearances: int = Field(default=0, ge=0)


class BriefAppearanceOut(BaseModel):
    id: str
    caption: str
    source_name: str
    source_url: str
    appeared_at: datetime


class BriefMediaOpinionOut(BaseModel):
    id: str
    summary: str
    importance: BriefImportance = "unrated"
    generated_at: datetime
    source_count: int = Field(default=0, ge=0)


class BriefViewOut(BaseModel):
    identity: BriefIdentityOut
    score: BriefScoreOut
    watchlist: list[BriefWatchlistRatingOut]
    activity_window: ActivityWindow = "24h"
    activity_window_hours: int = 24
    appearances_window_hours: int = 36
    appearances: list[BriefAppearanceOut]
    latest_opinion: BriefMediaOpinionOut | None = None
    previous_opinions: list[BriefMediaOpinionOut] = Field(default_factory=list, max_length=3)
    data_status: Literal["live", "partial", "unavailable"]
    notice: str


class PoliticalActivitySourceOut(BaseModel):
    id: UUID
    figure_id: UUID | None = None
    figure_name: str | None = None
    name: str
    url: str
    source_class: str
    platform: str
    access_method: str
    publisher: str
    status: str
    schedule_minutes: int
    rights: str
    reliability_tier: str
    last_checked_at: datetime | None = None
    last_error: str | None = None


class PoliticalActivityOut(BaseModel):
    id: UUID
    figure_id: UUID
    person: str
    portrait_url: str | None = None
    occurred_at: datetime
    published_at: datetime | None = None
    appearance_type: str
    evidence_layer: ActivityLayer
    initiation: str
    venue_program: str | None = None
    topic: str
    summary: str
    direct_source_url: str
    publisher: str
    evidence_confidence: float = Field(ge=0, le=1)
    source_links: list[dict[str, Any]] = Field(default_factory=list)
    geography: dict[str, Any] = Field(default_factory=dict)


class PoliticalActivityPersonOut(BaseModel):
    figure_id: UUID
    slug: str
    person: str
    position: str | None = None
    portrait_url: str | None = None
    monitoring_state: Literal["active", "quiet", "emerging"]
    last_appearance_at: datetime | None = None
    main_topic: str | None = None
    current_count: int = Field(ge=0)
    previous_count: int = Field(ge=0)
    activity_change: Literal["up", "steady", "down"]
    source_count: int = Field(ge=0)
    confidence_label: Literal["high", "medium", "low", "unavailable"]
    strongest_sources: list[dict[str, Any]] = Field(default_factory=list)


class PoliticalActivityMonitorOut(BaseModel):
    window: ActivityWindow
    window_hours: int
    generated_at: datetime
    people_monitored: int
    active_sources: int
    source_gaps: int
    llm_provider: str
    llm_status: str
    people: list[PoliticalActivityPersonOut]
    recent_activity: list[PoliticalActivityOut]


class PoliticalActivityCollectionOut(BaseModel):
    sources_checked: int = 0
    entries_seen: int = 0
    activities_created: int = 0
    activities_merged: int = 0
    unmatched: int = 0
    errors: list[str] = Field(default_factory=list)


class AnalysisCenterOut(BaseModel):
    snapshot: dict[str, Any]
    election: dict[str, Any]
    command_view: CommandViewOut
    momentum_components: list[dict[str, Any]]
    timeline: list[dict[str, Any]]
    watchlist: list[dict[str, Any]]
    channels: list[dict[str, Any]]
    narratives: list[dict[str, Any]]
    appearances: list[dict[str, Any]]
    audience_lab: list[dict[str, Any]]
    latest_poll: dict[str, Any] | None = None
    coverage: dict[str, Any]
    evidence: list[dict[str, Any]]
    provider_status: dict[str, Any]


class EvidenceExplorerOut(BaseModel):
    snapshot_effective_at: datetime
    signals: list[dict[str, Any]]
    count: int


class MethodologyOut(BaseModel):
    model_version: str
    window: str
    comparison_window: str
    component_weights: dict[str, float]
    eligible_layers: list[str]
    excluded_layers: list[str]
    rank_coverage_threshold: float
    missing_data_policy: str
    documentation_path: str


class AppearanceListOut(BaseModel):
    snapshot_effective_at: datetime
    appearances: list[dict[str, Any]]


class ScenarioVariant(StrictModel):
    id: str = Field(min_length=1, max_length=60, pattern=r"^[a-zA-Z0-9_-]+$")
    title: str = Field(min_length=3, max_length=120)
    message: str = Field(min_length=20, max_length=2000)


class ScenarioComparisonCreate(StrictModel):
    variants: list[ScenarioVariant] = Field(min_length=1, max_length=3)

    @field_validator("variants")
    @classmethod
    def unique_variant_ids(cls, variants: list[ScenarioVariant]) -> list[ScenarioVariant]:
        if len({item.id for item in variants}) != len(variants):
            raise ValueError("variant ids must be unique")
        return variants


class ScenarioComparisonOut(BaseModel):
    context_pack: str
    provider_status: str
    cohorts: int
    results: list[dict[str, Any]]
    warnings: list[str]


class AgentDefinition(BaseModel):
    id: str
    name: str
    role: str
    stage: str
    verdict_authority: bool = False


class AgentFleetOut(BaseModel):
    agents: list[AgentDefinition]
    invariant: str
