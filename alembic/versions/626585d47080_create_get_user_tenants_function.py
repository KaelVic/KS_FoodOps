"""create_get_user_tenants_function

Revision ID: 626585d47080
Revises: 01cf6be2cc97
Create Date: 2026-08-14 06:56:55.645218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '626585d47080'
down_revision: Union[str, Sequence[str], None] = '01cf6be2cc97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a SECURITY DEFINER function so that the auth endpoints can fetch 
    # a user's tenants without being blocked by RLS on tenant_memberships.
    op.execute("""
    CREATE OR REPLACE FUNCTION get_user_tenants(p_user_id VARCHAR)
    RETURNS TABLE(tenant_id UUID, role VARCHAR, name VARCHAR)
    SECURITY DEFINER
    AS $$
    BEGIN
        RETURN QUERY
        SELECT tm.tenant_id, tm.role, t.name
        FROM tenant_memberships tm
        JOIN tenants t ON t.id = tm.tenant_id
        WHERE tm.user_id = p_user_id;
    END;
    $$ LANGUAGE plpgsql;
    """)

def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS get_user_tenants(VARCHAR);")
