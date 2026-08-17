"""erp_phase3_financial_cashflow_dre

Revision ID: 9c3d4e5f6a7b
Revises: 8b2c3d4e5f6a
Create Date: 2026-08-16 23:25:00.000000

"""
import os
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9c3d4e5f6a7b'
down_revision: Union[str, Sequence[str], None] = '8b2c3d4e5f6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")

    # 1. bank_statement_transactions
    op.create_table('bank_statement_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('bank_account_id', sa.UUID(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), server_default='CREDIT', nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('fitid', sa.String(length=255), nullable=True),
        sa.Column('check_number', sa.String(length=100), nullable=True),
        sa.Column('is_reconciled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('reconciled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settlement_type', sa.String(length=50), nullable=True),
        sa.Column('settlement_id', sa.UUID(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_statement_transactions_tenant_id'), 'bank_statement_transactions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_bank_statement_transactions_bank_account_id'), 'bank_statement_transactions', ['bank_account_id'], unique=False)
    op.create_index(op.f('ix_bank_statement_transactions_fitid'), 'bank_statement_transactions', ['fitid'], unique=False)
    op.create_index(op.f('ix_bank_statement_transactions_settlement_id'), 'bank_statement_transactions', ['settlement_id'], unique=False)

    # 2. bank_reconciliation_rules
    op.create_table('bank_reconciliation_rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('pattern', sa.String(length=255), nullable=False),
        sa.Column('category_id', sa.UUID(), nullable=True),
        sa.Column('cost_center_id', sa.UUID(), nullable=True),
        sa.Column('action_type', sa.String(length=50), server_default='AUTO_EXPENSE', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['financial_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cost_center_id'], ['cost_centers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bank_reconciliation_rules_tenant_id'), 'bank_reconciliation_rules', ['tenant_id'], unique=False)

    # RLS Policies
    tables = ['bank_statement_transactions', 'bank_reconciliation_rules']
    for table in tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY tenant_isolation_policy ON {table} USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)")

    tables_str = ", ".join(tables)
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {tables_str} TO {app_user}")


def downgrade() -> None:
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")
    tables = ['bank_reconciliation_rules', 'bank_statement_transactions']
    tables_str = ", ".join(tables)
    op.execute(f"REVOKE ALL PRIVILEGES ON {tables_str} FROM {app_user}")
    
    for table in tables:
        op.drop_table(table)
