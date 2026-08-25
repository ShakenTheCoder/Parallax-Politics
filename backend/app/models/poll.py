"""Verified representative-poll releases and their provenance."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class Poll(Base, UUIDPK, Timestamps):
    __tablename__ = "polls"

    pollster: Mapped[str] = mapped_column(String(200), nullable=False)
    sponsor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    published_at: Mapped[date] = mapped_column(Date, nullable=False)
    field_start: Mapped[date] = mapped_column(Date, nullable=False)
    field_end: Mapped[date] = mapped_column(Date, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    population: Mapped[str] = mapped_column(String(240), nullable=False)
    mode: Mapped[str] = mapped_column(String(160), nullable=False)
    margin_of_error: Mapped[str] = mapped_column(String(160), nullable=False)
    confidence_level: Mapped[str | None] = mapped_column(String(80), nullable=True)
    exact_question: Mapped[str] = mapped_column(Text, nullable=False)
    geography: Mapped[str] = mapped_column(String(160), nullable=False)
    results: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    source_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unreviewed")
    verified_by: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
