"""erp_phase8_labor_prime_cost

Revision ID: 4b8c9d0e1f2a
Revises: 3a7b8c9d0e1f
Create Date: 2026-08-17 05:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4b8c9d0e1f2a'
down_revision: Union[str, None] = '3a7b8c9d0e1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: employees
    op.create_table(
        'employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('role_title', sa.String(100), nullable=False),
        sa.Column('department', sa.String(50), nullable=False, server_default='FLOOR'),
        sa.Column('monthly_salary', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('hourly_rate', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('tip_points', sa.Numeric(precision=24, scale=12), nullable=False, server_default='1.0'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_employees_tenant_dept', 'employees', ['tenant_id', 'department'])

    # 2. Table: work_shifts
    op.create_table(
        'work_shifts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('locations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('shift_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='SCHEDULED'),
        sa.Column('notes', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_work_shifts_tenant_date', 'work_shifts', ['tenant_id', 'shift_date'])

    # 3. Table: time_clock_entries
    op.create_table(
        'time_clock_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('locations.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('clock_in', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('clock_out', sa.DateTime(timezone=True), nullable=True),
        sa.Column('break_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_hours', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='OPEN'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_time_clock_tenant_emp', 'time_clock_entries', ['tenant_id', 'employee_id'])

    # 4. Table: tip_distributions
    op.create_table(
        'tip_distributions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reference_period', sa.String(50), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_tips_collected', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('house_retention_percentage', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('net_tips_pool', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_tip_distrib_tenant_period', 'tip_distributions', ['tenant_id', 'reference_period'])

    # 5. Table: tip_distribution_items
    op.create_table(
        'tip_distribution_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('distribution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tip_distributions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('employee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('hours_worked', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('points', sa.Numeric(precision=24, scale=12), nullable=False, server_default='1.0'),
        sa.Column('calculated_share', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
        sa.Column('allocated_tip_amount', sa.Numeric(precision=24, scale=12), nullable=False, server_default='0'),
    )
    op.create_index('IX_tip_items_tenant_distrib', 'tip_distribution_items', ['tenant_id', 'distribution_id'])

    # 6. Enable & Force PostgreSQL RLS
    tables = [
        'employees',
        'work_shifts',
        'time_clock_entries',
        'tip_distributions',
        'tip_distribution_items',
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
        'tip_distribution_items',
        'tip_distributions',
        'time_clock_entries',
        'work_shifts',
        'employees',
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table};")
        op.drop_table(table)
