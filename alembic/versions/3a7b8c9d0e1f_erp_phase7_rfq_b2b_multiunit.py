"""erp_phase7_rfq_b2b_multiunit

Revision ID: 3a7b8c9d0e1f
Revises: 2f6a7b8c9d0e
Create Date: 2026-08-17 04:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3a7b8c9d0e1f'
down_revision: Union[str, None] = '2f6a7b8c9d0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: rfqs
    op.create_table(
        'rfqs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rfq_number', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('locations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_rfqs_tenant_status', 'rfqs', ['tenant_id', 'status'])

    # 2. Table: rfq_items
    op.create_table(
        'rfq_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rfq_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rfqs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sku_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skus.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('quantity', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('target_price', sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_rfq_items_tenant_rfq', 'rfq_items', ['tenant_id', 'rfq_id'])

    # 3. Table: rfq_suppliers
    op.create_table(
        'rfq_suppliers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rfq_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rfqs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='INVITED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_rfq_suppliers_tenant_rfq', 'rfq_suppliers', ['tenant_id', 'rfq_id'])

    # 4. Table: rfq_proposals
    op.create_table(
        'rfq_proposals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rfq_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rfqs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('freight_cost', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('delivery_days', sa.String(50), nullable=True, server_default='0'),
        sa.Column('payment_terms', sa.String(100), nullable=True),
        sa.Column('min_order_value', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_rfq_proposals_tenant_rfq', 'rfq_proposals', ['tenant_id', 'rfq_id'])

    # 5. Table: rfq_proposal_items
    op.create_table(
        'rfq_proposal_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('proposal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rfq_proposals.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('rfq_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rfq_items.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('unit_price', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('available_quantity', sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column('brand_or_spec', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_rfq_proposal_items_tenant_proposal', 'rfq_proposal_items', ['tenant_id', 'proposal_id'])

    # 6. Enable & Force PostgreSQL RLS
    tables = [
        'rfqs',
        'rfq_items',
        'rfq_suppliers',
        'rfq_proposals',
        'rfq_proposal_items',
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
        'rfq_proposal_items',
        'rfq_proposals',
        'rfq_suppliers',
        'rfq_items',
        'rfqs',
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table};")
        op.drop_table(table)
