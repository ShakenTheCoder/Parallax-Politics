"""add soft archiving to principal briefs

Revision ID: p1c7d8e9f0a4
Revises: o0b6c7d8e9f3
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "p1c7d8e9f0a4"
down_revision: str | None = "o0b6c7d8e9f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "principal_briefs",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_principal_briefs_archived_at", "principal_briefs", ["archived_at"])
    # Earlier local templates must not remain visible as product intelligence.
    op.execute(
        "UPDATE principal_briefs SET archived_at = CURRENT_TIMESTAMP "
        "WHERE model = 'development-fallback'"
    )


def downgrade() -> None:
    op.drop_index("ix_principal_briefs_archived_at", table_name="principal_briefs")
    op.drop_column("principal_briefs", "archived_at")
