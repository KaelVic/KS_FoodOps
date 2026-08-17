"""erp_phase9_copilot_predictive

Revision ID: 5c9d0e1f2a3b
Revises: 4b8c9d0e1f2a
Create Date: 2026-08-17 05:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5c9d0e1f2a3b'
down_revision: Union[str, None] = '4b8c9d0e1f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: copilot_conversations
    op.create_table(
        'copilot_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('app_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False, server_default='Nova Conversa com FoodOps Copilot'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. Table: copilot_messages
    op.create_table(
        'copilot_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('copilot_conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('sender', sa.String(20), nullable=False, server_default='USER'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(50), nullable=False, server_default='GENERAL'),
        sa.Column('data_payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_copilot_messages_tenant_conv', 'copilot_messages', ['tenant_id', 'conversation_id'])

    # 3. Table: executive_briefings
    op.create_table(
        'executive_briefings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('briefing_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False, server_default='DASHBOARD'),
        sa.Column('status', sa.String(50), nullable=False, server_default='GENERATED'),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('metrics_payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('IX_executive_briefings_tenant_date', 'executive_briefings', ['tenant_id', 'briefing_date'])

    # 4. Enable & Force PostgreSQL RLS
    tables = [
        'copilot_conversations',
        'copilot_messages',
        'executive_briefings',
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
        'executive_briefings',
        'copilot_messages',
        'copilot_conversations',
    ]
    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table};")
        op.drop_table(table)
