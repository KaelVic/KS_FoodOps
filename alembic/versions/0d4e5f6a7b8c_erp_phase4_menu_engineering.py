"""erp_phase4_menu_engineering

Revision ID: 0d4e5f6a7b8c
Revises: 9c3d4e5f6a7b
Create Date: 2026-08-16 23:48:00.000000

"""
import os
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0d4e5f6a7b8c'
down_revision: Union[str, Sequence[str], None] = '9c3d4e5f6a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")

    # 1. menu_categories
    op.create_table('menu_categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_categories_tenant_id'), 'menu_categories', ['tenant_id'], unique=False)

    # 2. menu_items
    op.create_table('menu_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('category_id', sa.UUID(), nullable=True),
        sa.Column('recipe_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('pos_code', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sale_price', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('cost_price', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('target_cmv_percentage', sa.Numeric(precision=5, scale=2), server_default='30.00', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['menu_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_items_tenant_id'), 'menu_items', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_menu_items_category_id'), 'menu_items', ['category_id'], unique=False)
    op.create_index(op.f('ix_menu_items_recipe_id'), 'menu_items', ['recipe_id'], unique=False)
    op.create_index(op.f('ix_menu_items_pos_code'), 'menu_items', ['pos_code'], unique=False)

    # RLS Policies
    tables = ['menu_categories', 'menu_items']
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation_policy ON {table} USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)")

    tables_str = ", ".join(tables)
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {tables_str} TO {app_user}")


def downgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")
    tables = ['menu_items', 'menu_categories']
    tables_str = ", ".join(tables)
    op.execute(f"REVOKE ALL PRIVILEGES ON {tables_str} FROM {app_user}")
    
    for table in tables:
        op.drop_table(table)
