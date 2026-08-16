"""phase6_document_ingestion

Revision ID: b809285d5d9f
Revises: 215abd7f4dfc
Create Date: 2026-08-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b809285d5d9f'
down_revision: Union[str, Sequence[str], None] = '215abd7f4dfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
