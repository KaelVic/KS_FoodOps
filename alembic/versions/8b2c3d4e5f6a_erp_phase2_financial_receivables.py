"""erp_phase2_financial_receivables

Revision ID: 8b2c3d4e5f6a
Revises: 7a1b2c3d4e5f
Create Date: 2026-08-16 23:15:00.000000

"""
import os
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8b2c3d4e5f6a'
down_revision: Union[str, Sequence[str], None] = '7a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")

    # 1. payment_acquirers
    op.create_table('payment_acquirers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('acquirer_type', sa.String(length=50), nullable=False, server_default='CREDIT_DEBIT'),
        sa.Column('debit_fee_percentage', sa.Numeric(precision=10, scale=4), server_default='1.50', nullable=False),
        sa.Column('credit_1x_fee_percentage', sa.Numeric(precision=10, scale=4), server_default='2.80', nullable=False),
        sa.Column('credit_inst_fee_percentage', sa.Numeric(precision=10, scale=4), server_default='3.80', nullable=False),
        sa.Column('voucher_fee_percentage', sa.Numeric(precision=10, scale=4), server_default='5.50', nullable=False),
        sa.Column('delivery_fee_percentage', sa.Numeric(precision=10, scale=4), server_default='23.00', nullable=False),
        sa.Column('pix_fee_percentage', sa.Numeric(precision=10, scale=4), server_default='0.00', nullable=False),
        sa.Column('fixed_fee', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('settlement_days_debit', sa.Integer(), server_default='1', nullable=False),
        sa.Column('settlement_days_credit', sa.Integer(), server_default='30', nullable=False),
        sa.Column('settlement_days_voucher', sa.Integer(), server_default='30', nullable=False),
        sa.Column('settlement_days_delivery', sa.Integer(), server_default='7', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_acquirers_tenant_id'), 'payment_acquirers', ['tenant_id'], unique=False)

    # 2. receivable_invoices
    op.create_table('receivable_invoices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_tax_id', sa.String(length=50), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default='POS'),
        sa.Column('category_id', sa.UUID(), nullable=True),
        sa.Column('cost_center_id', sa.UUID(), nullable=True),
        sa.Column('document_number', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('gross_amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('deductions_amount', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('net_amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('issue_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['financial_categories.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['cost_center_id'], ['cost_centers.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receivable_invoices_tenant_id'), 'receivable_invoices', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_receivable_invoices_category_id'), 'receivable_invoices', ['category_id'], unique=False)
    op.create_index(op.f('ix_receivable_invoices_cost_center_id'), 'receivable_invoices', ['cost_center_id'], unique=False)

    # 3. receivable_installments
    op.create_table('receivable_installments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=False),
        sa.Column('acquirer_id', sa.UUID(), nullable=True),
        sa.Column('installment_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('total_installments', sa.Integer(), server_default='1', nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False, server_default='CREDIT_CARD'),
        sa.Column('card_brand', sa.String(length=50), nullable=True),
        sa.Column('gross_amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('fee_percentage', sa.Numeric(precision=10, scale=4), server_default='0', nullable=False),
        sa.Column('fee_amount', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('net_amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('expected_settlement_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('nsu', sa.String(length=100), nullable=True),
        sa.Column('authorization_code', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invoice_id'], ['receivable_invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['acquirer_id'], ['payment_acquirers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receivable_installments_tenant_id'), 'receivable_installments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_receivable_installments_invoice_id'), 'receivable_installments', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_receivable_installments_acquirer_id'), 'receivable_installments', ['acquirer_id'], unique=False)

    # 4. receivable_settlements
    op.create_table('receivable_settlements',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('installment_id', sa.UUID(), nullable=False),
        sa.Column('bank_account_id', sa.UUID(), nullable=False),
        sa.Column('settlement_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('gross_amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('fee_deducted', sa.Numeric(precision=24, scale=12), server_default='0', nullable=False),
        sa.Column('net_received_amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('bank_transaction_ref', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['installment_id'], ['receivable_installments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_receivable_settlements_tenant_id'), 'receivable_settlements', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_receivable_settlements_installment_id'), 'receivable_settlements', ['installment_id'], unique=False)
    op.create_index(op.f('ix_receivable_settlements_bank_account_id'), 'receivable_settlements', ['bank_account_id'], unique=False)

    # RLS Policies
    tables = [
        'payment_acquirers', 'receivable_invoices', 
        'receivable_installments', 'receivable_settlements'
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
        'receivable_settlements', 'receivable_installments', 
        'receivable_invoices', 'payment_acquirers'
    ]
    tables_str = ", ".join(tables)
    op.execute(f"REVOKE ALL PRIVILEGES ON {tables_str} FROM {app_user}")
    
    for table in tables:
        op.drop_table(table)
