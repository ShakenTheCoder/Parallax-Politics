"""add principal_briefs table

Revision ID: j6d2e3f4a5b6
Revises: h5c1d2e3f4a5
Create Date: 2026-05-28 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "j6d2e3f4a5b6"
down_revision: Union[str, None] = "h5c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "principal_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),

        sa.Column("top_risk", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("top_opportunity", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("action_card", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("reasoning", sa.Text(), nullable=False, server_default=""),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),

        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0"),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),

        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_principal_briefs_profile_id", "principal_briefs", ["profile_id"], unique=False)
    op.create_index("ix_principal_briefs_run_id", "principal_briefs", ["run_id"], unique=False)
    op.create_index(
        "ix_principal_briefs_profile_created",
        "principal_briefs",
        ["profile_id", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_principal_briefs_profile_created", table_name="principal_briefs")
    op.drop_index("ix_principal_briefs_run_id", table_name="principal_briefs")
    op.drop_index("ix_principal_briefs_profile_id", table_name="principal_briefs")
    op.drop_table("principal_briefs")
