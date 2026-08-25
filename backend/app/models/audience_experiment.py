"""Provider-backed qualitative audience experiment runs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class AudienceExperimentRun(Base, UUIDPK, Timestamps):
    __tablename__ = "audience_experiment_runs"

    profile_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, unique=True)
    variants: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    cohorts: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued", index=True)
    provider_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    samples: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    aggregate: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
