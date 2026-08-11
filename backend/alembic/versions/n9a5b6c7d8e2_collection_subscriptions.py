"""collection subscriptions

Revision ID: n9a5b6c7d8e2
Revises: m8f4a5b6c7d1
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "n9a5b6c7d8e2"
down_revision: str | None = "m8f4a5b6c7d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "collection_subscriptions",
        sa.Column("collection_source_id", sa.UUID(), nullable=False),
        sa.Column("subject_id", sa.UUID(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("css_selector", sa.String(length=240), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["collection_source_id"], ["collection_sources.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["subject_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "collection_source_id",
            "subject_id",
            "path",
            name="uq_collection_subscription_target",
        ),
    )
    op.create_index(
        "ix_collection_subscriptions_collection_source_id",
        "collection_subscriptions",
        ["collection_source_id"],
    )
    op.create_index(
        "ix_collection_subscriptions_subject_id",
        "collection_subscriptions",
        ["subject_id"],
    )
    op.create_index(
        "ix_collection_subscriptions_next_due_at",
        "collection_subscriptions",
        ["next_due_at"],
    )


def downgrade() -> None:
    op.drop_table("collection_subscriptions")
