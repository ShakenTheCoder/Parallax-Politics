"""add scdra gap columns and gap_retrieval_attempts table

Revision ID: k7e3f4a5b6c0
Revises: j6d2e3f4a5b6
Create Date: 2026-05-29 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "k7e3f4a5b6c0"
down_revision: Union[str, None] = "j6d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to principal_identities
    op.add_column(
        "principal_identities",
        sa.Column("coverage_gaps_structured", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
    )
    op.add_column(
        "principal_identities",
        sa.Column("scdra_runs", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "principal_identities",
        sa.Column("scdra_last_run", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "principal_identities",
        sa.Column("data_completeness_score", sa.Float(), nullable=False, server_default="0.0"),
    )

    # Create gap_retrieval_attempts table
    op.create_table(
        "gap_retrieval_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("principal_identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gap_type", sa.String(length=50), nullable=False),
        sa.Column("gap_severity", sa.String(length=10), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("strategy", sa.String(length=100), nullable=True),
        sa.Column("search_query", sa.Text(), nullable=True),
        sa.Column("sources_found", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("resolution_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("resolved_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), onupdate=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["principal_identity_id"], ["principal_identities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gap_retrieval_attempts_principal_id", "gap_retrieval_attempts", ["principal_identity_id"], unique=False)
    op.create_index("ix_gap_retrieval_attempts_gap_type", "gap_retrieval_attempts", ["gap_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_gap_retrieval_attempts_gap_type", table_name="gap_retrieval_attempts")
    op.drop_index("ix_gap_retrieval_attempts_principal_id", table_name="gap_retrieval_attempts")
    op.drop_table("gap_retrieval_attempts")
    # Note: updated_at is dropped with the table
    
    op.drop_column("principal_identities", "data_completeness_score")
    op.drop_column("principal_identities", "scdra_last_run")
    op.drop_column("principal_identities", "scdra_runs")
    op.drop_column("principal_identities", "coverage_gaps_structured")
