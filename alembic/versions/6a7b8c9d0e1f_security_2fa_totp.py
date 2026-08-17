"""security_2fa_totp

Revision ID: 6a7b8c9d0e1f
Revises: 5c9d0e1f2a3b
Create Date: 2026-08-17 05:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6a7b8c9d0e1f'
down_revision: Union[str, None] = '5c9d0e1f2a3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 2FA columns to app_users table
    op.add_column('app_users', sa.Column('is_2fa_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('app_users', sa.Column('totp_secret', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('app_users', 'totp_secret')
    op.drop_column('app_users', 'is_2fa_enabled')
