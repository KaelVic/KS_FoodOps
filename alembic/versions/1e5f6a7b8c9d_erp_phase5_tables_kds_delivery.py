"""erp_phase5_tables_kds_delivery

Revision ID: 1e5f6a7b8c9d
Revises: 0d4e5f6a7b8c
Create Date: 2026-08-17 00:10:00.000000

"""
import os
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1e5f6a7b8c9d'
down_revision: Union[str, Sequence[str], None] = '0d4e5f6a7b8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")

    # 1. dining_tables
    op.create_table('dining_tables',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('table_number', sa.String(length=50), nullable=False),
        sa.Column('capacity', sa.Integer(), server_default='4', nullable=False),
        sa.Column('section', sa.String(length=50), server_default='Salão Principal', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='AVAILABLE', nullable=False),
        sa.Column('active_order_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dining_tables_tenant_id'), 'dining_tables', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_dining_tables_status'), 'dining_tables', ['status'], unique=False)

    # 2. orders
    op.create_table('orders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=30), server_default='DINE_IN', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='PENDING', nullable=False),
        sa.Column('table_id', sa.UUID(), nullable=True),
        sa.Column('customer_name', sa.String(length=150), nullable=True),
        sa.Column('customer_phone', sa.String(length=50), nullable=True),
        sa.Column('delivery_address', sa.Text(), nullable=True),
        sa.Column('waiter_name', sa.String(length=100), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('delivery_fee', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('is_paid', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['table_id'], ['dining_tables.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_tenant_id'), 'orders', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_channel'), 'orders', ['channel'], unique=False)
    op.create_index(op.f('ix_orders_table_id'), 'orders', ['table_id'], unique=False)

    # 3. order_items
    op.create_table('order_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.UUID(), nullable=False),
        sa.Column('menu_item_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=24, scale=12), server_default='1', nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('total_price', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('preparation_notes', sa.String(length=300), nullable=True),
        sa.Column('production_station', sa.String(length=50), server_default='KITCHEN', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='QUEUED', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ready_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('served_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_items_tenant_id'), 'order_items', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_status'), 'order_items', ['status'], unique=False)
    op.create_index(op.f('ix_order_items_production_station'), 'order_items', ['production_station'], unique=False)

    # RLS Policies
    tables = ['dining_tables', 'orders', 'order_items']
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation_policy ON {table} USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)")

    tables_str = ", ".join(tables)
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {tables_str} TO {app_user}")


def downgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")
    tables = ['order_items', 'orders', 'dining_tables']
    tables_str = ", ".join(tables)
    op.execute(f"REVOKE ALL PRIVILEGES ON {tables_str} FROM {app_user}")
    
    for table in tables:
        op.drop_table(table)
