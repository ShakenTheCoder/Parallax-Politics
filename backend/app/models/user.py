from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models._mixins import UUIDPK, Timestamps

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile


class User(Base, UUIDPK, Timestamps):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, default="principal")
    access_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    principal_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user_profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False)
