"""Canonical agent I/O contracts."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class URLValidationResult(BaseModel):
    """Result of URL validation check by SRCA (Source Real Check Agent)."""

    url: str
    is_valid: bool
    status_code: int | None = None
    content_type: str | None = None
    content_length: int | None = None
    error: str | None = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0
    trusted_domain: bool = False


class EvidenceRef(BaseModel):
    """A single piece of evidence supporting an agent claim."""

    claim: str
    source_url: str | None = None
    quote: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    extra: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent: str
    summary: str
    payload: dict[str, Any]
    evidence: list[EvidenceRef] = Field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    model: str | None = None
    confidence: float | None = None


# --- Specific agent payload shapes (typed for downstream consumers) ----------

class SourceItem(BaseModel):
    url: str
    title: str | None = None
    domain: str
    published_at: str | None = None
    excerpt: str | None = None
    credibility_score: float = Field(ge=0.0, le=1.0, default=0.5)


class SourcePack(BaseModel):
    query: str
    sources: list[SourceItem]
    coverage_gaps: list[str] = Field(default_factory=list)


class DomainBriefing(BaseModel):
    relevant_concepts: list[str] = Field(default_factory=list)
    institutional_constraints: list[str] = Field(default_factory=list)
    precedent_cases: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    notes: str | None = None


class DemographicCohort(BaseModel):
    name: str
    share_pct: float | None = None
    salient_issues: list[str] = Field(default_factory=list)
    media_mix: dict[str, float] = Field(default_factory=dict)


class DemographicBriefing(BaseModel):
    region: str = "Philippines"
    cohorts: list[DemographicCohort] = Field(default_factory=list)
    notes: str | None = None


class CoverageGap(BaseModel):
    """Structured coverage gap with type, severity, and resolution status."""
    gap_type: str = Field(..., description="Taxonomy gap type identifier")
    severity: str = Field(..., pattern=r"^(high|medium|low)$")
    description: str = Field(..., description="Human-readable description")
    affected_fields: list[str] = Field(default_factory=list, description="JSON paths to affected fields")
    auto_resolvable: bool = Field(default=True, description="Whether gap can be auto-resolved via SCDRA")
    status: str = Field(default="pending", pattern=r"^(pending|resolved|failed|manual)$")


class GapResolution(BaseModel):
    """Record of a single gap resolution by SCDRA."""
    gap_type: str
    fields_resolved: list[str] = Field(default_factory=list)
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class PrincipalIdentityArtifact(BaseModel):
    """Artifact shape emitted by PIDAA — mirrors principal_identities columns."""
    full_name: str
    profile_image_url: str | None = None
    basics: dict[str, Any] = Field(default_factory=dict)
    family: dict[str, Any] = Field(default_factory=dict)
    education: dict[str, Any] = Field(default_factory=dict)
    career_timeline: dict[str, Any] = Field(default_factory=dict)
    current_position: dict[str, Any] = Field(default_factory=dict)
    party_history: dict[str, Any] = Field(default_factory=dict)
    electoral_record: dict[str, Any] = Field(default_factory=dict)
    policy_stances: dict[str, Any] = Field(default_factory=dict)
    voice_signature: dict[str, Any] = Field(default_factory=dict)
    controversies: dict[str, Any] = Field(default_factory=dict)
    network: dict[str, Any] = Field(default_factory=dict)
    source_index: dict[str, Any] = Field(default_factory=dict)
    coverage_gaps: list[str] = Field(default_factory=list)
    coverage_gaps_structured: list[CoverageGap] = Field(default_factory=list)
    data_completeness_score: float = Field(ge=0.0, le=1.0, default=0.0)


class SCDRAArtifact(BaseModel):
    """Artifact emitted by SCDRA — Specific Candidate Data Retrieval Agent results."""
    principal_identity_id: UUID | None = None
    run_timestamp: datetime = Field(default_factory=datetime.utcnow)
    gaps_processed: int = 0
    gaps_resolved: int = 0
    gaps_remaining: int = 0
    resolutions: list[GapResolution] = Field(default_factory=list)
    data_completeness_before: float = Field(ge=0.0, le=1.0, default=0.0)
    data_completeness_after: float = Field(ge=0.0, le=1.0, default=0.0)
    total_cost_usd: float = 0.0


# --- Run artifacts envelope --------------------------------------------------

class RunArtifacts(BaseModel):
    """Per-run artifact envelope. The Brief is its own resource (see schemas/brief.py)."""
    source_pack: SourcePack | None = None
    domain_briefing: DomainBriefing | None = None
    demographic_briefing: DemographicBriefing | None = None
    principal_identity: PrincipalIdentityArtifact | None = None
    scdra: SCDRAArtifact | None = None
