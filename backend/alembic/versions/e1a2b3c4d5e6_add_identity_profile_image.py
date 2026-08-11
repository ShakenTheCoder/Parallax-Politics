"""add sourced profile image to principal identities

Revision ID: e1a2b3c4d5e6
Revises: d603aa29f954
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, None] = "d603aa29f954"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("principal_identities", sa.Column("profile_image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("principal_identities", "profile_image_url")
