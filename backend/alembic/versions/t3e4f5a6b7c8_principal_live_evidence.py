"""polls, audience experiments, and brief review state

Revision ID: t3e4f5a6b7c8
Revises: s4f0a1b2c3d7
"""

from collections.abc import Sequence
from datetime import date
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "t3e4f5a6b7c8"
down_revision: str | None = "s4f0a1b2c3d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("principal_briefs", sa.Column("review_status", sa.String(length=24), server_default="agent_draft", nullable=False))
    op.add_column("principal_briefs", sa.Column("reviewed_by", sa.UUID(), nullable=True))
    op.add_column("principal_briefs", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("principal_briefs", sa.Column("review_note", sa.Text(), nullable=True))
    op.create_index("ix_principal_briefs_review_status", "principal_briefs", ["review_status"])
    op.create_foreign_key("fk_principal_briefs_reviewed_by", "principal_briefs", "users", ["reviewed_by"], ["id"], ondelete="SET NULL")

    op.create_table(
        "polls",
        sa.Column("pollster", sa.String(length=200), nullable=False),
        sa.Column("sponsor", sa.String(length=200), nullable=True),
        sa.Column("published_at", sa.Date(), nullable=False),
        sa.Column("field_start", sa.Date(), nullable=False),
        sa.Column("field_end", sa.Date(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("population", sa.String(length=240), nullable=False),
        sa.Column("mode", sa.String(length=160), nullable=False),
        sa.Column("margin_of_error", sa.String(length=160), nullable=False),
        sa.Column("confidence_level", sa.String(length=80), nullable=True),
        sa.Column("exact_question", sa.Text(), nullable=False),
        sa.Column("geography", sa.String(length=160), nullable=False),
        sa.Column("results", postgresql.JSONB(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("verification_status", sa.String(length=32), server_default="unreviewed", nullable=False),
        sa.Column("verified_by", sa.UUID(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_note", sa.Text(), nullable=True),
        sa.Column("methodology_notes", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("source_url"),
    )
    op.create_index("ix_polls_published_at", "polls", ["published_at"])

    op.create_table(
        "audience_experiment_runs",
        sa.Column("profile_id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("variants", postgresql.JSONB(), nullable=False),
        sa.Column("cohorts", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(length=24), server_default="queued", nullable=False),
        sa.Column("provider_status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("samples", postgresql.JSONB(), nullable=False),
        sa.Column("aggregate", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_audience_experiment_runs_profile_id", "audience_experiment_runs", ["profile_id"])
    op.create_index("ix_audience_experiment_runs_status", "audience_experiment_runs", ["status"])
    polls = sa.table(
        "polls",
        sa.column("id", sa.UUID), sa.column("pollster", sa.String), sa.column("published_at", sa.Date),
        sa.column("field_start", sa.Date), sa.column("field_end", sa.Date), sa.column("sample_size", sa.Integer),
        sa.column("population", sa.String), sa.column("mode", sa.String), sa.column("margin_of_error", sa.String),
        sa.column("confidence_level", sa.String), sa.column("exact_question", sa.Text), sa.column("geography", sa.String),
        sa.column("results", postgresql.JSONB), sa.column("source_url", sa.Text), sa.column("verification_status", sa.String),
    )
    op.bulk_insert(polls, [{
        "id": uuid4(), "pollster": "Pulse Asia Research, Inc.", "published_at": date(2026, 7, 22),
        "field_start": date(2026, 6, 28), "field_end": date(2026, 7, 6), "sample_size": 2400,
        "population": "Representative adults aged 18+", "mode": "Face-to-face interviews",
        "margin_of_error": "±2 percentage points nationally at 95% confidence", "confidence_level": "95%",
        "exact_question": "Who would you vote for as President if the May 2028 election were held during the survey period and the listed people were candidates?",
        "geography": "Philippines", "results": [{"name": "Sara Duterte", "value": 49.0}, {"name": "Leni Robredo", "value": 26.0}, {"name": "Raffy Tulfo", "value": 14.0}, {"name": "Vince Dizon", "value": 1.0}, {"name": "Benjamin Magalong", "value": 1.0}, {"name": "Nicolas Torre III", "value": 0.1}],
        "source_url": "https://pulseasia.ph/wp-content/uploads/2026/07/MR2-UB2026-2-MR-on-the-May-2028-Elections-Final.pdf",
        "verification_status": "verified",
    }])


def downgrade() -> None:
    op.drop_index("ix_audience_experiment_runs_status", table_name="audience_experiment_runs")
    op.drop_index("ix_audience_experiment_runs_profile_id", table_name="audience_experiment_runs")
    op.drop_table("audience_experiment_runs")
    op.drop_index("ix_polls_published_at", table_name="polls")
    op.drop_table("polls")
    op.drop_constraint("fk_principal_briefs_reviewed_by", "principal_briefs", type_="foreignkey")
    op.drop_index("ix_principal_briefs_review_status", table_name="principal_briefs")
    op.drop_column("principal_briefs", "review_note")
    op.drop_column("principal_briefs", "reviewed_at")
    op.drop_column("principal_briefs", "reviewed_by")
    op.drop_column("principal_briefs", "review_status")
