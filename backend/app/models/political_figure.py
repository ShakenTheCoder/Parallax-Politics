"""Superadmin political-figure glossary records and immutable research snapshots."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class PoliticalFigure(Base, UUIDPK, Timestamps):
    __tablename__ = "political_figures"

    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    aliases: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    current_role: Mapped[str | None] = mapped_column(String(240), nullable=True)
    office: Mapped[str | None] = mapped_column(String(240), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(160), nullable=True)
    party: Mapped[str | None] = mapped_column(String(160), nullable=True)
    faction: Mapped[str | None] = mapped_column(String(160), nullable=True)
    region: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(60), nullable=False, default="unknown", index=True)
    portrait_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    portrait_source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    portrait_attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    social_accounts: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    relationships: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    source_ledger: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    coverage_gaps: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class PoliticalFigureSnapshot(Base, UUIDPK, Timestamps):
    __tablename__ = "political_figure_snapshots"

    figure_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("political_figures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(nullable=False)
    trigger: Mapped[str] = mapped_column(String(40), nullable=False)
    produced_by: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_ledger: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
