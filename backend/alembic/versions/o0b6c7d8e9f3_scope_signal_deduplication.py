"""scope signal deduplication

Revision ID: o0b6c7d8e9f3
Revises: n9a5b6c7d8e2
"""
from collections.abc import Sequence

from alembic import op

revision: str = "o0b6c7d8e9f3"
down_revision: str | None = "n9a5b6c7d8e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_signal_events_content_hash",
        "signal_events",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_signal_events_subject_content_hash",
        "signal_events",
        ["subject_id", "content_hash"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_signal_events_subject_content_hash",
        "signal_events",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_signal_events_content_hash",
        "signal_events",
        ["content_hash"],
    )
