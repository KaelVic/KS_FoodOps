"""erp_phase1_financial_payables

Revision ID: 7a1b2c3d4e5f
Revises: 626585d47080
Create Date: 2026-08-16 23:00:00.000000

"""
import os
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '4fada10c5809'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")

    # 1. financial_categories
    op.create_table('financial_categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='EXPENSE_OPERATIONAL'),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['financial_categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_financial_categories_tenant_id'), 'financial_categories', ['tenant_id'], unique=False)

    # 2. cost_centers
    op.create_table('cost_centers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cost_centers_tenant_id'), 'cost_centers', ['tenant_id'], unique=False)

    # 3. bank_accounts
    op.create_table('bank_accounts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False, server_default='CHECKING'),
        sa.Column('bank_code', sa.String(length=20), nullable=True),
        sa.Column('agency_number', sa.String(length=50), nullable=True),
        sa.Column('account_number', sa.String(length=50), nullable=True),
        sa.Column('pix_key', sa.String(length=255), nullable=True),
        sa.Column('initial_balance', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('current_balance', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_accounts_tenant_id'), 'bank_accounts', ['tenant_id'], unique=False)

    # 4. payment_methods
    op.create_table('payment_methods',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='PIX'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_methods_tenant_id'), 'payment_methods', ['tenant_id'], unique=False)

    # 5. payable_bills
    op.create_table('payable_bills',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('category_id', sa.UUID(), nullable=True),
        sa.Column('cost_center_id', sa.UUID(), nullable=True),
        sa.Column('purchase_order_id', sa.UUID(), nullable=True),
        sa.Column('supplier_invoice_id', sa.UUID(), nullable=True),
        sa.Column('document_number', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('issue_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('first_due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['category_id'], ['financial_categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['cost_center_id'], ['cost_centers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_invoice_id'], ['supplier_invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payable_bills_tenant_id'), 'payable_bills', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_payable_bills_supplier_id'), 'payable_bills', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_payable_bills_category_id'), 'payable_bills', ['category_id'], unique=False)
    op.create_index(op.f('ix_payable_bills_cost_center_id'), 'payable_bills', ['cost_center_id'], unique=False)

    # 6. payable_installments
    op.create_table('payable_installments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('payable_bill_id', sa.UUID(), nullable=False),
        sa.Column('installment_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('total_installments', sa.Integer(), server_default='1', nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('barcode', sa.String(length=255), nullable=True),
        sa.Column('pix_code', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['payable_bill_id'], ['payable_bills.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payable_installments_tenant_id'), 'payable_installments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_payable_installments_payable_bill_id'), 'payable_installments', ['payable_bill_id'], unique=False)

    # 7. payable_settlements
    op.create_table('payable_settlements',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('installment_id', sa.UUID(), nullable=False),
        sa.Column('bank_account_id', sa.UUID(), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False, server_default='PIX'),
        sa.Column('settlement_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('principal_amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('interest_amount', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('fine_amount', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('discount_amount', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('total_paid', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('transaction_reference', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['installment_id'], ['payable_installments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payable_settlements_tenant_id'), 'payable_settlements', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_payable_settlements_installment_id'), 'payable_settlements', ['installment_id'], unique=False)
    op.create_index(op.f('ix_payable_settlements_bank_account_id'), 'payable_settlements', ['bank_account_id'], unique=False)

    # RLS Policies
    tables = [
        'financial_categories', 'cost_centers', 'bank_accounts', 
        'payment_methods', 'payable_bills', 'payable_installments', 'payable_settlements'
    ]
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation_policy ON {table} USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)")

    tables_str = ", ".join(tables)
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {tables_str} TO {app_user}")


def downgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")
    tables = [
        'payable_settlements', 'payable_installments', 'payable_bills',
        'payment_methods', 'bank_accounts', 'cost_centers', 'financial_categories'
    ]
    tables_str = ", ".join(tables)
    op.execute(f"REVOKE ALL PRIVILEGES ON {tables_str} FROM {app_user}")
    
    for table in tables:
        op.drop_table(table)
