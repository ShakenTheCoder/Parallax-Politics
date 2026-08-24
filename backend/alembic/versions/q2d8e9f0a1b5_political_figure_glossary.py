"""add Superadmin political figure glossary

Revision ID: q2d8e9f0a1b5
Revises: p1c7d8e9f0a4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "r3e9f0a1b2c6"
down_revision: str | None = "q2d8e9f0a1b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "political_figures",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("canonical_name", sa.String(length=240), nullable=False),
        sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("current_role", sa.String(length=240), nullable=True),
        sa.Column("office", sa.String(length=240), nullable=True),
        sa.Column("jurisdiction", sa.String(length=160), nullable=True),
        sa.Column("party", sa.String(length=160), nullable=True),
        sa.Column("faction", sa.String(length=160), nullable=True),
        sa.Column("region", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("portrait_url", sa.Text(), nullable=True),
        sa.Column("portrait_source_url", sa.Text(), nullable=True),
        sa.Column("portrait_attribution", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("social_accounts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("relationships", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_ledger", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("coverage_gaps", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_political_figures_canonical_name", "political_figures", ["canonical_name"])
    op.create_index("ix_political_figures_category", "political_figures", ["category"])
    op.create_index("ix_political_figures_status", "political_figures", ["status"])
    op.create_index("ix_political_figures_archived_at", "political_figures", ["archived_at"])
    op.create_table(
        "political_figure_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("figure_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(length=40), nullable=False),
        sa.Column("produced_by", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_ledger", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["figure_id"], ["political_figures.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_political_figure_snapshots_figure_id", "political_figure_snapshots", ["figure_id"])


def downgrade() -> None:
    op.drop_index("ix_political_figure_snapshots_figure_id", table_name="political_figure_snapshots")
    op.drop_table("political_figure_snapshots")
    op.drop_index("ix_political_figures_archived_at", table_name="political_figures")
    op.drop_index("ix_political_figures_status", table_name="political_figures")
    op.drop_index("ix_political_figures_category", table_name="political_figures")
    op.drop_index("ix_political_figures_canonical_name", table_name="political_figures")
    op.drop_table("political_figures")
