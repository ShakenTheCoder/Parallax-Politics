"""I/O contracts for the Superadmin political-figure glossary."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PoliticalFigureSource(BaseModel):
    url: str
    title: str | None = None
    publisher: str | None = None
    source_type: str = "public_web"
    published_at: str | None = None
    accessed_at: str | None = None
    supports: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PoliticalFigureSocialAccount(BaseModel):
    platform: str
    url: str
    handle: str | None = None
    account_type: str = "official"
    verification: str = "unverified"
    source_url: str | None = None
    last_checked_at: str | None = None


class PoliticalFigureSummary(BaseModel):
    id: UUID
    slug: str
    canonical_name: str
    aliases: list[str] = Field(default_factory=list)
    category: str
    current_role: str | None = None
    office: str | None = None
    party: str | None = None
    region: str | None = None
    status: str
    portrait_url: str | None = None
    confidence: float
    last_verified_at: datetime | None = None
    coverage_gaps: list[str] = Field(default_factory=list)
    social_platforms: list[str] = Field(default_factory=list)


class PoliticalFigureDetail(PoliticalFigureSummary):
    jurisdiction: str | None = None
    faction: str | None = None
    portrait_source_url: str | None = None
    portrait_attribution: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    social_accounts: list[PoliticalFigureSocialAccount] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    source_ledger: list[PoliticalFigureSource] = Field(default_factory=list)
    snapshot_count: int = 0


class PoliticalFigureSeedOut(BaseModel):
    run_id: UUID
    status: str = "queued"


class PoliticalFigureRefreshOut(BaseModel):
    run_id: UUID
    status: str = "queued"
