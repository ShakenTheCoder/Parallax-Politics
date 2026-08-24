"""add glossary-linked political activity monitor

Revision ID: s4f0a1b2c3d7
Revises: r3e9f0a1b2c6
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "s4f0a1b2c3d7"
down_revision: str | None = "r3e9f0a1b2c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "political_activity_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("figure_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source_class", sa.String(length=40), nullable=False),
        sa.Column("platform", sa.String(length=40), nullable=False),
        sa.Column("access_method", sa.String(length=40), nullable=False),
        sa.Column("publisher", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("schedule_minutes", sa.Integer(), nullable=False),
        sa.Column("rights", sa.String(length=120), nullable=False),
        sa.Column("reliability_tier", sa.String(length=20), nullable=False),
        sa.Column("robots_observed", sa.Boolean(), nullable=False),
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["figure_id"], ["political_figures.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(
        "ix_political_activity_sources_figure_id", "political_activity_sources", ["figure_id"]
    )
    op.create_index(
        "ix_political_activity_sources_source_class", "political_activity_sources", ["source_class"]
    )
    op.create_index(
        "ix_political_activity_sources_platform", "political_activity_sources", ["platform"]
    )

    op.create_table(
        "political_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("figure_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("primary_source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("appearance_type", sa.String(length=60), nullable=False),
        sa.Column("evidence_layer", sa.String(length=40), nullable=False),
        sa.Column("initiation", sa.String(length=40), nullable=False),
        sa.Column("venue_program", sa.String(length=300), nullable=True),
        sa.Column("topic", sa.String(length=240), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("direct_source_url", sa.Text(), nullable=False),
        sa.Column("publisher", sa.String(length=160), nullable=False),
        sa.Column("evidence_confidence", sa.Float(), nullable=False),
        sa.Column("confidence_basis", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("identity_basis", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("geography", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("claims", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_links", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("cluster_key", sa.String(length=64), nullable=False),
        sa.Column("analyzer", sa.String(length=80), nullable=False),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("review_status", sa.String(length=24), nullable=False),
        sa.ForeignKeyConstraint(["figure_id"], ["political_figures.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["primary_source_id"], ["political_activity_sources.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("figure_id", "cluster_key", name="uq_political_activity_cluster"),
    )
    op.create_index("ix_political_activities_figure_id", "political_activities", ["figure_id"])
    op.create_index(
        "ix_political_activities_primary_source_id", "political_activities", ["primary_source_id"]
    )
    op.create_index("ix_political_activities_occurred_at", "political_activities", ["occurred_at"])
    op.create_index(
        "ix_political_activities_published_at", "political_activities", ["published_at"]
    )
    op.create_index(
        "ix_political_activities_appearance_type", "political_activities", ["appearance_type"]
    )
    op.create_index(
        "ix_political_activities_evidence_layer", "political_activities", ["evidence_layer"]
    )
    op.create_index(
        "ix_political_activities_content_hash", "political_activities", ["content_hash"]
    )
    op.create_index("ix_political_activities_cluster_key", "political_activities", ["cluster_key"])


def downgrade() -> None:
    op.drop_table("political_activities")
    op.drop_table("political_activity_sources")
