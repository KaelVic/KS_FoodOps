"""grant_app_users_privileges

Revision ID: 01cf6be2cc97
Revises: 3267132022e5
Create Date: 2026-08-14 06:55:26.323121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01cf6be2cc97'
down_revision: Union[str, Sequence[str], None] = '3267132022e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import os

def upgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON app_users TO {app_user};")


def downgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")
    op.execute(f"REVOKE ALL PRIVILEGES ON app_users FROM {app_user};")
