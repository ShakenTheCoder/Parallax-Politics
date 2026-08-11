"""intelligence control plane

Revision ID: m8f4a5b6c7d1
Revises: e1a2b3c4d5e6
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "m8f4a5b6c7d1"
down_revision: str | None = "e1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "collection_sources",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("connector_kind", sa.String(length=40), nullable=False),
        sa.Column("authority", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("schedule_minutes", sa.Integer(), nullable=False),
        sa.Column("robots_observed", sa.Boolean(), nullable=False),
        sa.Column("allowed_paths", postgresql.JSONB(), nullable=False),
        sa.Column("source_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("base_url"),
    )
    op.create_table(
        "signal_events",
        sa.Column("subject_id", sa.UUID(), nullable=True),
        sa.Column("collection_source_id", sa.UUID(), nullable=True),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("external_id", sa.String(length=240), nullable=True),
        sa.Column("platform", sa.String(length=60), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("engagement", postgresql.JSONB(), nullable=False),
        sa.Column("geography", postgresql.JSONB(), nullable=False),
        sa.Column("provenance", postgresql.JSONB(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["collection_source_id"], ["collection_sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash", name="uq_signal_events_content_hash"),
    )
    op.create_index("ix_signal_events_subject_id", "signal_events", ["subject_id"])
    op.create_index("ix_signal_events_collection_source_id", "signal_events", ["collection_source_id"])
    op.create_index("ix_signal_events_source_id", "signal_events", ["source_id"])
    op.create_index("ix_signal_events_published_at", "signal_events", ["published_at"])
    op.create_index("ix_signal_events_observed_at", "signal_events", ["observed_at"])
    op.create_index("ix_signal_events_content_hash", "signal_events", ["content_hash"])
    op.create_table(
        "intelligence_snapshots",
        sa.Column("subject_id", sa.UUID(), nullable=True),
        sa.Column("kind", sa.String(length=60), nullable=False),
        sa.Column("scope_key", sa.String(length=180), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("produced_by", sa.String(length=80), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["subject_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intelligence_snapshots_subject_id", "intelligence_snapshots", ["subject_id"])
    op.create_index("ix_intelligence_snapshots_kind", "intelligence_snapshots", ["kind"])
    op.create_index("ix_intelligence_snapshots_effective_at", "intelligence_snapshots", ["effective_at"])
    op.create_table(
        "intelligence_scenarios",
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("proposed_action", sa.Text(), nullable=False),
        sa.Column("cohort", postgresql.JSONB(), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("forecast", postgresql.JSONB(), nullable=False),
        sa.Column("assumptions", postgresql.JSONB(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("model_version", sa.String(length=80), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intelligence_scenarios_subject_id", "intelligence_scenarios", ["subject_id"])
    op.create_table(
        "strategy_verdicts",
        sa.Column("scenario_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("critic", postgresql.JSONB(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", sa.UUID(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["scenario_id"], ["intelligence_scenarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_id"),
    )
    op.create_index("ix_strategy_verdicts_scenario_id", "strategy_verdicts", ["scenario_id"], unique=True)
    op.create_table(
        "intelligence_audit_events",
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=60), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=True),
        sa.Column("purpose", sa.String(length=240), nullable=False),
        sa.Column("audit_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intelligence_audit_events_actor_id", "intelligence_audit_events", ["actor_id"])
    op.create_index("ix_intelligence_audit_events_action", "intelligence_audit_events", ["action"])
    op.create_index("ix_intelligence_audit_events_occurred_at", "intelligence_audit_events", ["occurred_at"])


def downgrade() -> None:
    op.drop_table("intelligence_audit_events")
    op.drop_table("strategy_verdicts")
    op.drop_table("intelligence_scenarios")
    op.drop_table("intelligence_snapshots")
    op.drop_table("signal_events")
    op.drop_table("collection_sources")
