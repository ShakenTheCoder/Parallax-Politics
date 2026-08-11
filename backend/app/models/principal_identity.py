"""PrincipalIdentity — PIDAA knowledge base for a confirmed Philippine principal."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class PrincipalIdentity(Base, UUIDPK, Timestamps):
    __tablename__ = "principal_identities"

    profile_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    built_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pidaa_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")
    profile_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 11 identity sections — all JSONB with provenance sub-keys
    basics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    family: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    education: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    career_timeline: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    current_position: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    party_history: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    electoral_record: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    policy_stances: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    voice_signature: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    controversies: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    network: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_index: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    coverage_gaps: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)

    # SCDRA (Specific Candidate Data Retrieval Agent) tracking
    coverage_gaps_structured: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    scdra_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scdra_last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_completeness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    raw_dossier: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
