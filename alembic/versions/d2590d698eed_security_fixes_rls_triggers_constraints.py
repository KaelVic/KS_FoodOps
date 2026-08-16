"""security_fixes_rls_triggers_constraints

Revision ID: d2590d698eed
Revises: 1082c0f19162
Create Date: 2026-08-14 00:10:51.967862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2590d698eed'
down_revision: Union[str, Sequence[str], None] = '1082c0f19162'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import os

def upgrade() -> None:
    # 1. Update the password for ksfoodops_app from env var
    app_user = os.environ.get("POSTGRES_APP_USER", "ksfoodops_app")
    app_pass = os.environ.get("POSTGRES_APP_PASSWORD")
    if app_pass:
        op.execute(f"ALTER ROLE {app_user} WITH PASSWORD '{app_pass}'")

    # 2. Add WITH CHECK to RLS policies
    op.execute("""
    DO $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN SELECT tablename FROM pg_policies WHERE policyname = 'tenant_isolation_policy'
        LOOP
            EXECUTE 'ALTER POLICY tenant_isolation_policy ON ' || quote_ident(r.tablename) || ' WITH CHECK (tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid)';
        END LOOP;
    END;
    $$;
    """)

    # 3. Add immutability triggers for POSTED/CLOSED/PUBLISHED
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_posted_mutation() RETURNS TRIGGER AS $$
    BEGIN
      IF OLD.status = 'POSTED' THEN
        RAISE EXCEPTION 'Cannot modify a POSTED movement';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    DROP TRIGGER IF EXISTS trg_stock_movements_immutable ON stock_movements;
    """)

    op.execute("""
    CREATE TRIGGER trg_stock_movements_immutable 
      BEFORE UPDATE OR DELETE ON stock_movements 
      FOR EACH ROW EXECUTE FUNCTION prevent_posted_mutation();
    """)
    
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_closed_mutation() RETURNS TRIGGER AS $$
    BEGIN
      IF OLD.status = 'CLOSED' THEN
        RAISE EXCEPTION 'Cannot modify a CLOSED session';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    DROP TRIGGER IF EXISTS trg_inventory_sessions_immutable ON inventory_sessions;
    """)

    op.execute("""
    CREATE TRIGGER trg_inventory_sessions_immutable
      BEFORE UPDATE OR DELETE ON inventory_sessions
      FOR EACH ROW EXECUTE FUNCTION prevent_closed_mutation();
    """)

    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_published_mutation() RETURNS TRIGGER AS $$
    BEGIN
      IF OLD.status = 'PUBLISHED' THEN
        RAISE EXCEPTION 'Cannot modify a PUBLISHED recipe version';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    DROP TRIGGER IF EXISTS trg_recipe_versions_immutable ON recipe_versions;
    """)

    op.execute("""
    CREATE TRIGGER trg_recipe_versions_immutable
      BEFORE UPDATE OR DELETE ON recipe_versions
      FOR EACH ROW EXECUTE FUNCTION prevent_published_mutation();
    """)

    # 4. Add UNIQUE constraint to stock_balance_projections to prevent race conditions
    op.create_unique_constraint('uq_stock_balance_projections_tenant_location_sku', 'stock_balance_projections', ['tenant_id', 'location_id', 'sku_id'])

def downgrade() -> None:
    op.drop_constraint('uq_stock_balance_projections_tenant_location_sku', 'stock_balance_projections', type_='unique')
    op.execute("DROP TRIGGER IF EXISTS trg_recipe_versions_immutable ON recipe_versions")
    op.execute("DROP FUNCTION IF EXISTS prevent_published_mutation()")
    op.execute("DROP TRIGGER IF EXISTS trg_inventory_sessions_immutable ON inventory_sessions")
    op.execute("DROP FUNCTION IF EXISTS prevent_closed_mutation()")
    op.execute("DROP TRIGGER IF EXISTS trg_stock_movements_immutable ON stock_movements")
    op.execute("DROP FUNCTION IF EXISTS prevent_posted_mutation()")
