"""phase8_intelligence

Revision ID: 4fada10c5809
Revises: 3635da773fa4
Create Date: 2026-08-16 05:43:18.588997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fada10c5809'
down_revision: Union[str, Sequence[str], None] = '3635da773fa4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f('app_users_email_key'), 'app_users', type_='unique')
    op.create_index(op.f('ix_app_users_email'), 'app_users', ['email'], unique=True)
    op.drop_constraint(op.f('uq_stock_balance_projections_tenant_location_sku'), 'stock_balance_projections', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    op.create_unique_constraint(op.f('uq_stock_balance_projections_tenant_location_sku'), 'stock_balance_projections', ['tenant_id', 'location_id', 'sku_id'], postgresql_nulls_not_distinct=False)
    op.drop_index(op.f('ix_app_users_email'), table_name='app_users')
    op.create_unique_constraint(op.f('app_users_email_key'), 'app_users', ['email'], postgresql_nulls_not_distinct=False)
    # ### end Alembic commands ###
