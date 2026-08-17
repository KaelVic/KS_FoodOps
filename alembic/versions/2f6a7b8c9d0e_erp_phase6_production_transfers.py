"""erp_phase6_production_transfers

Revision ID: 2f6a7b8c9d0e
Revises: 1e5f6a7b8c9d
Create Date: 2026-08-17 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2f6a7b8c9d0e'
down_revision: Union[str, None] = '1e5f6a7b8c9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: production_orders
    op.create_table(
        'production_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('order_number', sa.String(50), nullable=False),
        sa.Column('recipe_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipes.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('recipe_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recipe_versions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('produced_sku_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skus.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('locations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='PLANNED'),
        sa.Column('planned_quantity', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('actual_quantity', sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column('batch_number', sa.String(100), nullable=True),
        sa.Column('produced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_cost', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('unit_cost', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_production_orders_tenant_status', 'production_orders', ['tenant_id', 'status'])

    # 2. Table: production_order_ingredients
    op.create_table(
        'production_order_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('production_order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_orders.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sku_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skus.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('planned_quantity', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('actual_quantity', sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column('unit_cost', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_production_order_ingredients_tenant_order', 'production_order_ingredients', ['tenant_id', 'production_order_id'])

    # 3. Table: stock_transfers
    op.create_table(
        'stock_transfers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transfer_number', sa.String(50), nullable=False),
        sa.Column('origin_location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('locations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('destination_location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('locations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_stock_transfers_tenant_status', 'stock_transfers', ['tenant_id', 'status'])

    # 4. Table: stock_transfer_items
    op.create_table(
        'stock_transfer_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transfer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('stock_transfers.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sku_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skus.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quantity_sent', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('quantity_received', sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column('unit_cost', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_stock_transfer_items_tenant_transfer', 'stock_transfer_items', ['tenant_id', 'transfer_id'])

    # 5. Enable & Force PostgreSQL RLS
    tables = [
        'production_orders',
        'production_order_ingredients',
        'stock_transfers',
        'stock_transfer_items',
    ]

    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            FOR ALL
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
        """)
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO ksfoodops_app;")


def downgrade() -> None:
    tables = [
        'stock_transfer_items',
        'stock_transfers',
        'production_order_ingredients',
        'production_orders',
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table};")
        op.drop_table(table)
