from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class Competitor(Base, UUIDPK, Timestamps):
    __tablename__ = "competitors"

    profile_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competitor_profile_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    party: Mapped[str | None] = mapped_column(String(120), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    overlap_areas: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    watch_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="polled_hypothetical"
    )
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
