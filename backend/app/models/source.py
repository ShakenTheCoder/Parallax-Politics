from typing import Any

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class Source(Base, UUIDPK, Timestamps):
    """Cached/normalized record of an external information source."""

    __tablename__ = "sources"

    url: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    content_hash: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
