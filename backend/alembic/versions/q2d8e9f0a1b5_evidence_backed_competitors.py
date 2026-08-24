"""evidence-backed competitor relationships

Revision ID: q2d8e9f0a1b5
Revises: p1c7d8e9f0a4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "q2d8e9f0a1b5"
down_revision: str | None = "p1c7d8e9f0a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("competitors", sa.Column("competitor_profile_id", sa.UUID(), nullable=True))
    op.add_column(
        "competitors",
        sa.Column("watch_status", sa.String(length=40), nullable=False, server_default="polled_hypothetical"),
    )
    op.add_column("competitors", sa.Column("effective_from", sa.DateTime(timezone=True)))
    op.add_column("competitors", sa.Column("effective_to", sa.DateTime(timezone=True)))
    op.add_column(
        "competitors",
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.create_foreign_key(
        "fk_competitors_competitor_profile_id_profiles",
        "competitors",
        "profiles",
        ["competitor_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_competitors_competitor_profile_id", "competitors", ["competitor_profile_id"])
    op.alter_column("competitors", "watch_status", server_default=None)
    op.alter_column("competitors", "evidence", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_competitors_competitor_profile_id", table_name="competitors")
    op.drop_constraint("fk_competitors_competitor_profile_id_profiles", "competitors", type_="foreignkey")
    op.drop_column("competitors", "evidence")
    op.drop_column("competitors", "effective_to")
    op.drop_column("competitors", "effective_from")
    op.drop_column("competitors", "watch_status")
    op.drop_column("competitors", "competitor_profile_id")

