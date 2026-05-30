"""GapRetrievalAttempt — audit trail for SCDRA data retrieval attempts."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class GapRetrievalAttempt(Base, UUIDPK, Timestamps):
    __tablename__ = "gap_retrieval_attempts"

    principal_identity_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("principal_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Gap classification
    gap_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    gap_severity: Mapped[str] = mapped_column(String(10), nullable=False)  # high/medium/low

    # Attempt tracking
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    strategy: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # exa_search, api_lookup, inference, etc.
    search_query: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Results
    sources_found: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    resolution_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending/resolved/failed/manual
    resolved_fields: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )  # JSON paths to fields that were filled

    # Cost tracking
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
