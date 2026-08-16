"""add_app_users_table_and_seed

Revision ID: 3267132022e5
Revises: d2590d698eed
Create Date: 2026-08-14 06:47:48.150647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3267132022e5'
down_revision: Union[str, Sequence[str], None] = 'd2590d698eed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None




def upgrade() -> None:
    # 1. Create table app_users
    op.execute("""
        CREATE TABLE app_users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );
    """)

    # 2. Hardcoded hash for 'Admin@123!' (bypassing passlib bug during migration)
    hashed_password = "$2b$12$kmSre8sqkyKBFFWXZ1cRkOnIIPW0ndO.2SOauw/.opGimXVFQWPjG"

    # 3. Seed data
    admin_id = "00000000-0000-0000-0000-000000000001"
    tenant_id = "00000000-0000-0000-0000-000000000002"
    membership_id = "00000000-0000-0000-0000-000000000003"

    op.execute(f"""
        INSERT INTO app_users (id, email, password_hash, full_name, is_active)
        VALUES ('{admin_id}', 'admin@ksfoodops.local', '{hashed_password}', 'Admin KS FoodOps', TRUE)
        ON CONFLICT (email) DO NOTHING;
    """)

    op.execute(f"""
        INSERT INTO tenants (id, name)
        VALUES ('{tenant_id}', 'Demo Restaurant')
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute(f"""
        INSERT INTO tenant_memberships (id, tenant_id, user_id, role)
        VALUES ('{membership_id}', '{tenant_id}', '{admin_id}', 'admin')
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    admin_id = "00000000-0000-0000-0000-000000000001"
    tenant_id = "00000000-0000-0000-0000-000000000002"
    membership_id = "00000000-0000-0000-0000-000000000003"

    op.execute(f"DELETE FROM tenant_memberships WHERE id = '{membership_id}';")
    op.execute(f"DELETE FROM tenants WHERE id = '{tenant_id}';")
    op.execute(f"DELETE FROM app_users WHERE id = '{admin_id}';")
    
    op.execute("DROP TABLE app_users;")
