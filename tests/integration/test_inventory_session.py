import pytest
import uuid
import asyncio
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy import text

from packages.tenant.database import async_session_maker
from packages.tenant.models import Tenant, BusinessUnit, Location
from modules.inventory.models import StockMovement, StockLedgerEntry, StockBalanceProjection, InventorySession, InventorySessionLocation, InventoryCountLine, InventoryCloseResult
from modules.inventory.service import InventoryService

pytestmark = pytest.mark.asyncio

async def setup_test_data(session, tenant_id: uuid.UUID):
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
    
    bu_id = uuid.uuid4()
    loc_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :t_id, 'BU Test')"),
        {"id": str(bu_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO locations (id, tenant_id, business_unit_id, name) VALUES (:id, :t_id, :bu_id, 'Main Kitchen')"),
        {"id": str(loc_id), "t_id": str(tenant_id), "bu_id": str(bu_id)}
    )
    
    uom_id = uuid.uuid4()
    sku_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Kilogram', 'KG', 'mass')"),
        {"id": str(uom_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO skus (id, tenant_id, name, base_uom_id) VALUES (:id, :t_id, 'Tomatoes', :uom_id)"),
        {"id": str(sku_id), "t_id": str(tenant_id), "uom_id": str(uom_id)}
    )
    
    # Pre-populate some stock via movement
    now = datetime.now(timezone.utc) - timedelta(days=1)
    movement_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO stock_movements (id, tenant_id, location_id, type, status, posted_at) VALUES (:id, :t_id, :l_id, 'RECEIPT', 'POSTED', :now)"),
        {"id": str(movement_id), "t_id": str(tenant_id), "l_id": str(loc_id), "now": now}
    )
    await session.execute(
        text("INSERT INTO stock_ledger_entries (id, tenant_id, movement_id, sku_id, quantity, unit_cost, balance_after) VALUES (:id, :t_id, :m_id, :sku_id, 50.0, 2.5, 50.0)"),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "m_id": str(movement_id), "sku_id": str(sku_id)}
    )
    await session.execute(
        text("INSERT INTO stock_balance_projections (id, tenant_id, location_id, sku_id, quantity, total_value) VALUES (:id, :t_id, :l_id, :sku_id, 50.0, 125.0)"),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "l_id": str(loc_id), "sku_id": str(sku_id)}
    )
    
    return loc_id, sku_id

async def test_inventory_close_and_cmv():
    tenant_id = uuid.uuid4()
    
    async with async_session_maker() as session:
        await session.execute(text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant Session')"), {"id": str(tenant_id)})
        loc_id, sku_id = await setup_test_data(session, tenant_id)
        
        # Create an inventory session
        sess_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        await session.execute(
            text("INSERT INTO inventory_sessions (id, tenant_id, status, cutoff_at) VALUES (:id, :t_id, 'REVIEW', :now)"),
            {"id": str(sess_id), "t_id": str(tenant_id), "now": now}
        )
        await session.execute(
            text("INSERT INTO inventory_session_locations (id, tenant_id, session_id, location_id) VALUES (:id, :t_id, :s_id, :l_id)"),
            {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "s_id": str(sess_id), "l_id": str(loc_id)}
        )
        
        # User counted 45.0 (expected is 50.0) -> negative variance of 5.0
        await session.execute(
            text("INSERT INTO inventory_count_lines (id, tenant_id, session_id, location_id, sku_id, counted_quantity) VALUES (:id, :t_id, :s_id, :l_id, :sku_id, 45.0)"),
            {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "s_id": str(sess_id), "l_id": str(loc_id), "sku_id": str(sku_id)}
        )
        await session.commit()
        
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        service = InventoryService(session)
        
        # Close session
        inv_session = await service.close_inventory_session(sess_id, tenant_id)
        await session.commit()
        
        assert inv_session.status == 'CLOSED'
        
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        # Check variance and ledger entry
        stmt = select(InventoryCloseResult).where(InventoryCloseResult.session_id == sess_id)
        result = (await session.execute(stmt)).scalar_one()
        assert result.expected_quantity == Decimal("50.0")
        assert result.counted_quantity == Decimal("45.0")
        assert result.variance_quantity == Decimal("-5.0")
        assert result.variance_value == Decimal("-12.5") # (125.0 / 50.0 = 2.5) * -5 = -12.5
        
        # Check stock balance
        stmt = select(StockBalanceProjection).where(StockBalanceProjection.sku_id == sku_id)
        balance = (await session.execute(stmt)).scalar_one()
        assert balance.quantity == Decimal("45.0")
        assert balance.total_value == Decimal("112.5") # 125.0 - 12.5
        
        # Test Idempotency
        service = InventoryService(session)
        inv_session_second = await service.close_inventory_session(sess_id, tenant_id)
        await session.commit()
        assert inv_session_second.id == inv_session.id
        
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        # Calculate CMV
        start_date = now - timedelta(days=2)
        end_date = now + timedelta(days=1)
        
        # Opening value = 0
        # Receipts value = 125.0
        # Closing value = 112.5
        # CMV = 0 + 125.0 - 112.5 = 12.5
        cmv = await service.calculate_operational_cmv(loc_id, start_date, end_date, tenant_id)
        assert cmv == Decimal("12.5")
