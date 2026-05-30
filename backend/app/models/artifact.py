from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class Artifact(Base, UUIDPK, Timestamps):
    """A decision artifact emitted by an agent (Perception Map, Action Card, ...)."""

    __tablename__ = "artifacts"

    run_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    # kinds: perception_map | action_card | source_pack | domain_briefing |
    #        demographic_briefing | person_profile_snapshot
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    produced_by: Mapped[str] = mapped_column(String(60), nullable=False)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
