"""Personal Profile — principal's public identity record (created by superadmin via PIDAA)."""
from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps


class Profile(Base, UUIDPK, Timestamps):
    __tablename__ = "profiles"

    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    party: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pack_id: Mapped[str] = mapped_column(String(80), nullable=False, default="philippines_politics")

    # Structured PPA knowledge bundle. Each field carries provenance metadata.
    # See app/schemas/profile.py for the canonical shape.
    identity: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    career: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    stances: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    voice_patterns: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    vulnerabilities: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    allies_rivals: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    media_footprint: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
