"""add principal_identities table

Revision ID: h5c1d2e3f4a5
Revises: f3a1b2c9d4e5
Create Date: 2026-05-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'h5c1d2e3f4a5'
down_revision: Union[str, None] = 'f3a1b2c9d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'principal_identities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('built_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pidaa_version', sa.String(length=20), nullable=False, server_default='v1'),

        # 11 identity sections
        sa.Column('basics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('family', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('education', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('career_timeline', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('current_position', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('party_history', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('electoral_record', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('policy_stances', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('voice_signature', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('controversies', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('network', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('source_index', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('coverage_gaps', postgresql.ARRAY(sa.Text()), nullable=False, server_default='{}'),

        sa.Column('raw_dossier', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_principal_identities_profile_id', 'principal_identities', ['profile_id'], unique=True)
    op.create_index('ix_principal_identities_status', 'principal_identities', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_principal_identities_status', table_name='principal_identities')
    op.drop_index('ix_principal_identities_profile_id', table_name='principal_identities')
    op.drop_table('principal_identities')
