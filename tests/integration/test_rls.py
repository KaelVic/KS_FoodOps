import pytest
import uuid
from sqlalchemy.future import select
from sqlalchemy import text
from packages.tenant.models import Tenant, BusinessUnit
from packages.tenant.database import async_session_maker

pytestmark = pytest.mark.asyncio

async def test_rls_isolation():
    # Setup two tenants using the owner engine (which bypasses RLS since it's the owner)
    # However, since we're using async_session_maker which binds to app engine, we might hit RLS directly
    # For this test, we assume the app role CAN insert if it sets the context.
    
    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    
    async with async_session_maker() as session:
        # Create tenants (Tenants table itself might not have RLS, but if it does we need to be careful)
        # Let's use raw SQL for setup to ensure it works
        await session.execute(text("INSERT INTO tenants (id, name) VALUES (:id, :name)"), {"id": str(tenant_a_id), "name": "Tenant A"})
        await session.execute(text("INSERT INTO tenants (id, name) VALUES (:id, :name)"), {"id": str(tenant_b_id), "name": "Tenant B"})
        
        # Create Business Units using RLS context for A
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_a_id)})
        bu_a_id = uuid.uuid4()
        await session.execute(
            text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :t_id, :name)"),
            {"id": str(bu_a_id), "t_id": str(tenant_a_id), "name": "BU A"}
        )
        
        # Create Business Units using RLS context for B
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_b_id)})
        bu_b_id = uuid.uuid4()
        await session.execute(
            text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :t_id, :name)"),
            {"id": str(bu_b_id), "t_id": str(tenant_b_id), "name": "BU B"}
        )
        await session.commit()
        
    # Now TEST RLS Isolation
    async with async_session_maker() as session:
        # Set context to Tenant A
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_a_id)})
        
        result = await session.execute(select(BusinessUnit))
        bus = result.scalars().all()
        
        assert len(bus) == 1
        assert bus[0].name == "BU A"
        assert bus[0].tenant_id == tenant_a_id
        
    async with async_session_maker() as session:
        # Set context to Tenant B
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_b_id)})
        
        result = await session.execute(select(BusinessUnit))
        bus = result.scalars().all()
        
        assert len(bus) == 1
        assert bus[0].name == "BU B"
        assert bus[0].tenant_id == tenant_b_id

    # Test Missing Context fails closed
    async with async_session_maker() as session:
        # We don't set context. RLS should block reading.
        # Actually in Postgres, if current_setting is missing and we used current_setting(..., true), 
        # it might raise an error or return null. We used current_setting(..., true) which means missing returns null.
        # So tenant_id = NULL is false, returning 0 rows.
        result = await session.execute(select(BusinessUnit))
        bus = result.scalars().all()
        assert len(bus) == 0
