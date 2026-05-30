from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.agents import RunArtifacts


class PrincipalOut(BaseModel):
    id: UUID
    slug: str
    full_name: str
    role_title: str | None = None
    party: str | None = None
    pack_id: str
    identity: dict[str, Any] = Field(default_factory=dict)
    career: dict[str, Any] = Field(default_factory=dict)
    stances: dict[str, Any] = Field(default_factory=dict)
    voice_patterns: dict[str, Any] = Field(default_factory=dict)
    vulnerabilities: dict[str, Any] = Field(default_factory=dict)
    allies_rivals: dict[str, Any] = Field(default_factory=dict)
    media_footprint: dict[str, Any] = Field(default_factory=dict)


class RunOut(BaseModel):
    id: UUID
    status: str
    run_kind: str = "brief_build"  # "pidaa_build" | "brief_build"
    situation_prompt: str
    total_cost_usd: float
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    artifacts: RunArtifacts = Field(default_factory=RunArtifacts)
    principal: PrincipalOut | None = None
