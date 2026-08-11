"""PrincipalBrief — strategic brief generated on demand by the Brief agent.

Append-only history. Each row is one snapshot of recommendations for a principal.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class PrincipalBrief(Base, UUIDPK, Timestamps):
    __tablename__ = "principal_briefs"

    profile_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Core content (one Brief shape, JSONB for forward-compat)
    top_risk: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    top_opportunity: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    topics: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    action_card: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)

    # Cost / model accounting
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False, default=0.0)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.0)
