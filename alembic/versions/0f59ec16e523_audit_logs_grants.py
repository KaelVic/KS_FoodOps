"""audit_logs_grants

Revision ID: 0f59ec16e523
Revises: 1b84a25817a7
Create Date: 2026-08-15 20:16:47.283226

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f59ec16e523'
down_revision: Union[str, Sequence[str], None] = '1b84a25817a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON audit_logs TO ksfoodops_app;")


def downgrade() -> None:
    op.execute("REVOKE SELECT, INSERT, UPDATE, DELETE ON audit_logs FROM ksfoodops_app;")
