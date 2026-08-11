"""Persistent control-plane records for political intelligence.

High-volume storage can be projected into ClickHouse/OpenSearch later. These
tables remain the authoritative, provenance-bearing records used by the API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class CollectionSource(Base, UUIDPK, Timestamps):
    __tablename__ = "collection_sources"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    connector_kind: Mapped[str] = mapped_column(String(40), nullable=False, default="scrapling")
    authority: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    schedule_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    robots_observed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allowed_paths: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    source_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    last_collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class CollectionSubscription(Base, UUIDPK, Timestamps):
    __tablename__ = "collection_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "collection_source_id",
            "subject_id",
            "path",
            name="uq_collection_subscription_target",
        ),
    )

    collection_source_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("collection_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    css_selector: Mapped[str | None] = mapped_column(String(240), nullable=True)
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="und")
    event_type: Mapped[str] = mapped_column(
        String(60), nullable=False, default="public_document"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    next_due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    last_collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class SignalEvent(Base, UUIDPK, Timestamps):
    __tablename__ = "signal_events"
    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "content_hash",
            name="uq_signal_events_subject_content_hash",
        ),
    )

    subject_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), index=True
    )
    collection_source_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("collection_sources.id", ondelete="SET NULL"), index=True
    )
    source_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(240), nullable=True)
    platform: Mapped[str] = mapped_column(String(60), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, default="public_document")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="und")
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    engagement: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    geography: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class IntelligenceSnapshot(Base, UUIDPK, Timestamps):
    __tablename__ = "intelligence_snapshots"

    subject_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    scope_key: Mapped[str] = mapped_column(String(180), nullable=False, default="national")
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    produced_by: Mapped[str] = mapped_column(String(80), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class IntelligenceScenario(Base, UUIDPK, Timestamps):
    __tablename__ = "intelligence_scenarios"

    subject_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_action: Mapped[str] = mapped_column(Text, nullable=False)
    cohort: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    forecast: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    assumptions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False, default="scenario-baseline-v1")


class StrategyVerdict(Base, UUIDPK, Timestamps):
    __tablename__ = "strategy_verdicts"

    scenario_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("intelligence_scenarios.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    critic: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IntelligenceAuditEvent(Base, UUIDPK):
    __tablename__ = "intelligence_audit_events"

    actor_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(60), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    purpose: Mapped[str] = mapped_column(String(240), nullable=False)
    audit_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
