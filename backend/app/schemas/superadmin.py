"""Superadmin-specific request/response schemas."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SuperadminVerifyIn(BaseModel):
    code: str


class SuperadminVerifyOut(BaseModel):
    token: str


class DisambiguateIn(BaseModel):
    name_query: str = Field(min_length=2, max_length=200)
    hint: str | None = Field(default=None, max_length=400)


class IdentityCandidate(BaseModel):
    full_name: str
    aliases: list[str] = Field(default_factory=list)
    current_role: str | None = None
    party: str | None = None
    region: str | None = None
    born: str | None = None
    birthplace: str | None = None
    photo_url: str | None = None
    one_line_bio: str | None = None
    top_sources: list[dict[str, str]] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    ambiguity_notes: str | None = None


class CreatePrincipalIn(BaseModel):
    name_query: str = Field(min_length=2, max_length=200)
    candidate: IdentityCandidate


class GeneratedCredentials(BaseModel):
    username: str
    password: str


class CreatePrincipalOut(BaseModel):
    profile_id: UUID
    identity_id: UUID
    run_id: UUID
    credentials: GeneratedCredentials


class PrincipalIdentitySection(BaseModel):
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


class PrincipalSummary(BaseModel):
    profile_id: UUID
    identity_id: UUID
    full_name: str
    role_title: str | None = None
    party: str | None = None
    pack_id: str
    pidaa_status: str
    built_at: str | None = None
    username: str
    profile_image_url: str | None = None
    overview: str | None = None


class PrincipalDetail(BaseModel):
    profile_id: UUID
    identity_id: UUID
    full_name: str
    role_title: str | None = None
    party: str | None = None
    pack_id: str
    username: str
    pidaa_status: str
    built_at: str | None = None
    identity: PrincipalIdentitySection
