"""Normalized public-activity records linked to the political glossary."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class PoliticalActivitySource(Base, UUIDPK, Timestamps):
    """One attributable acquisition target from the approved source registry."""

    __tablename__ = "political_activity_sources"

    figure_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("political_figures.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_class: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    access_method: Mapped[str] = mapped_column(String(40), nullable=False)
    publisher: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="needs_review")
    schedule_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    rights: Mapped[str] = mapped_column(String(120), nullable=False)
    reliability_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    robots_observed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)


class PoliticalActivity(Base, UUIDPK, Timestamps):
    """A deduplicated appearance, statement, coverage item, or reaction record."""

    __tablename__ = "political_activities"
    __table_args__ = (
        UniqueConstraint("figure_id", "cluster_key", name="uq_political_activity_cluster"),
    )

    figure_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("political_figures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    primary_source_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("political_activity_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    appearance_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    evidence_layer: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    initiation: Mapped[str] = mapped_column(String(40), nullable=False)
    venue_program: Mapped[str | None] = mapped_column(String(300), nullable=True)
    topic: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    direct_source_url: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(String(160), nullable=False)
    evidence_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_basis: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    identity_basis: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    geography: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    claims: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    source_links: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cluster_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    analyzer: Mapped[str] = mapped_column(String(80), nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    review_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="machine_reviewed"
    )
