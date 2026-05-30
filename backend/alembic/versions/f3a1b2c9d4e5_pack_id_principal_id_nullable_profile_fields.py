"""pack_id on profiles, principal_id on users, nullable user_profile fields

Revision ID: f3a1b2c9d4e5
Revises: d780e4133bea
Create Date: 2026-05-27 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'f3a1b2c9d4e5'
down_revision: Union[str, None] = 'd780e4133bea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # profiles.pack_id — which context pack governs this principal
    op.add_column('profiles',
        sa.Column('pack_id', sa.String(length=80), nullable=False,
                  server_default='philippines_politics')
    )

    # users.principal_id — the Profile row that IS this user's public persona
    op.add_column('users',
        sa.Column('principal_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index(op.f('ix_users_principal_id'), 'users', ['principal_id'], unique=False)
    op.create_foreign_key(
        'fk_users_principal_id_profiles',
        'users', 'profiles',
        ['principal_id'], ['id'],
        ondelete='SET NULL',
    )

    # user_profiles: make country, age, birthdate nullable for name-only onboarding
    op.alter_column('user_profiles', 'country', nullable=True, existing_type=sa.String(120))
    op.alter_column('user_profiles', 'age', nullable=True, existing_type=sa.Integer())
    op.alter_column('user_profiles', 'birthdate', nullable=True, existing_type=sa.String(40))


def downgrade() -> None:
    op.alter_column('user_profiles', 'birthdate', nullable=False, existing_type=sa.String(40))
    op.alter_column('user_profiles', 'age', nullable=False, existing_type=sa.Integer())
    op.alter_column('user_profiles', 'country', nullable=False, existing_type=sa.String(120))

    op.drop_constraint('fk_users_principal_id_profiles', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_principal_id'), table_name='users')
    op.drop_column('users', 'principal_id')

    op.drop_column('profiles', 'pack_id')
