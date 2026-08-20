"""phase1_ledger_identity_and_sales_location

Revision ID: 7b8c9d0e1f2a
Revises: 6a7b8c9d0e1f
Create Date: 2026-08-20 07:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7b8c9d0e1f2a'
down_revision: Union[str, None] = '6a7b8c9d0e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add actor identity and notes to stock_movements
    op.add_column('stock_movements', sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('stock_movements', sa.Column('reason_code', sa.String(length=100), nullable=True))
    op.add_column('stock_movements', sa.Column('notes', sa.String(length=500), nullable=True))
    op.create_index('ix_stock_movements_actor', 'stock_movements', ['tenant_id', 'actor_user_id'])

    # 2. Add location_id to sales
    op.add_column('sales', sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_sales_location_id',
        'sales', 'locations',
        ['location_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_sales_location', 'sales', ['tenant_id', 'location_id'])


def downgrade() -> None:
    op.drop_index('ix_sales_location', table_name='sales')
    op.drop_constraint('fk_sales_location_id', 'sales', type_='foreignkey')
    op.drop_column('sales', 'location_id')

    op.drop_index('ix_stock_movements_actor', table_name='stock_movements')
    op.drop_column('stock_movements', 'notes')
    op.drop_column('stock_movements', 'reason_code')
    op.drop_column('stock_movements', 'actor_user_id')
