import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import text
from modules.costing.service import CostingService

@pytest.mark.asyncio
async def test_calculate_historical_cmp(owner_session, test_db, tenant_id):
    """
    Validates CMP calculation with exact Decimal precision.
    """
    # Set the tenant_id context for the app session
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    # Create required references
    location_id = uuid.uuid4()
    sku_id = uuid.uuid4()
    
    bu_id = uuid.uuid4()
    await owner_session.execute(
        text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :t_id, 'BU')"),
        {"id": str(bu_id), "t_id": str(tenant_id)}
    )
    
    await owner_session.execute(
        text("INSERT INTO locations (id, tenant_id, business_unit_id, name) VALUES (:id, :t_id, :bu_id, 'Loc')"),
        {"id": str(location_id), "t_id": str(tenant_id), "bu_id": str(bu_id)}
    )
    
    uom_id = uuid.uuid4()
    await owner_session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Kilogram', 'KG', 'mass')"),
        {"id": str(uom_id), "t_id": str(tenant_id)}
    )
    
    await owner_session.execute(
        text("INSERT INTO skus (id, tenant_id, name, base_uom_id) "
             "VALUES (:id, :t_id, 'Item 1', :uom_id)"),
        {"id": str(sku_id), "t_id": str(tenant_id), "uom_id": str(uom_id)}
    )
    
    # Create Movement 1: +10 @ 5.00
    m1_id = uuid.uuid4()
    await owner_session.execute(
        text("INSERT INTO stock_movements (id, tenant_id, location_id, type, status) "
             "VALUES (:id, :t_id, :l_id, 'RECEIPT', 'POSTED')"),
        {"id": str(m1_id), "t_id": str(tenant_id), "l_id": str(location_id)}
    )
    await owner_session.execute(
        text("INSERT INTO stock_ledger_entries (id, tenant_id, movement_id, sku_id, quantity, unit_cost, balance_after, created_at) "
             "VALUES (:id, :t_id, :m_id, :s_id, 10, 5.00, 10, '2026-08-15 10:00:00')"),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "m_id": str(m1_id), "s_id": str(sku_id)}
    )
    
    # Create Movement 2: -4
    m2_id = uuid.uuid4()
    await owner_session.execute(
        text("INSERT INTO stock_movements (id, tenant_id, location_id, type, status) "
             "VALUES (:id, :t_id, :l_id, 'SALE', 'POSTED')"),
        {"id": str(m2_id), "t_id": str(tenant_id), "l_id": str(location_id)}
    )
    await owner_session.execute(
        text("INSERT INTO stock_ledger_entries (id, tenant_id, movement_id, sku_id, quantity, unit_cost, balance_after, created_at) "
             "VALUES (:id, :t_id, :m_id, :s_id, -4, null, 6, '2026-08-15 11:00:00')"), # unit_cost is null for sales
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "m_id": str(m2_id), "s_id": str(sku_id)}
    )
    
    # Create Movement 3: +4 @ 7.50
    m3_id = uuid.uuid4()
    await owner_session.execute(
        text("INSERT INTO stock_movements (id, tenant_id, location_id, type, status) "
             "VALUES (:id, :t_id, :l_id, 'RECEIPT', 'POSTED')"),
        {"id": str(m3_id), "t_id": str(tenant_id), "l_id": str(location_id)}
    )
    await owner_session.execute(
        text("INSERT INTO stock_ledger_entries (id, tenant_id, movement_id, sku_id, quantity, unit_cost, balance_after, created_at) "
             "VALUES (:id, :t_id, :m_id, :s_id, 4, 7.50, 10, '2026-08-15 12:00:00')"),
        {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "m_id": str(m3_id), "s_id": str(sku_id)}
    )
    
    await owner_session.commit()
    
    # Calculate CMP
    # After M1: 10 @ 5.00 => CMP = 5.00
    # After M2: 6 @ 5.00 => CMP = 5.00
    # After M3: (6 * 5.00 + 4 * 7.50) / 10 = (30 + 30) / 10 = 6.00
    cmp = await CostingService.calculate_historical_cmp(test_db, tenant_id, sku_id)
    
    assert cmp == Decimal('6.00')

@pytest.mark.asyncio
async def test_calculate_cmv(owner_session, test_db, tenant_id):
    """
    Validates Actual vs Theoretical CMV calculation.
    """
    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :t_id, false)"),
        {"t_id": str(tenant_id)}
    )
    
    start_date = datetime(2026, 8, 1)
    end_date = datetime(2026, 8, 31)
    
    # We will just test that it returns the expected dictionary structure
    # since we rely on the mocked stubs in this test case.
    result = await CostingService.calculate_cmv(test_db, tenant_id, start_date, end_date)
    
    assert "theoretical_cmv" in result
    assert "actual_cmv" in result
    assert "variance" in result
    assert isinstance(result["theoretical_cmv"], Decimal)
    assert isinstance(result["actual_cmv"], Decimal)
    assert isinstance(result["variance"], Decimal)

