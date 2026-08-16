import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from modules.intelligence.models import InventoryPolicy, PurchaseSuggestion, OperationalAlert
from modules.intelligence.service import IntelligenceService
from modules.inventory.models import StockBalanceProjection, StockLedgerEntry
from modules.catalog.models import SKU
from modules.purchasing.models import PurchaseOrder, PurchaseOrderLine, GoodsReceiptLine
from packages.tenant.models import Tenant, BusinessUnit

pytestmark = pytest.mark.asyncio

async def setup_intelligence_data(db_session: AsyncSession, tenant_id: uuid4):
    # Set context first for RLS
    await db_session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
    
    # Create business unit
    bu_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO business_units (id, tenant_id, name) VALUES (:bu, :t, 'Main BU')"
    ), {"bu": bu_id, "t": str(tenant_id)})

    # Create test locations
    location_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO locations (id, tenant_id, business_unit_id, name) VALUES (:loc, :t, :bu, 'Main Kitchen')"
    ), {"loc": location_id, "t": str(tenant_id), "bu": str(bu_id)})
    
    # Create UOM and Category
    uom_id = uuid4()
    cat_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:u, :t, 'Kilogram', 'kg', 'mass')"
    ), {"u": uom_id, "t": str(tenant_id)})
    await db_session.execute(text(
        "INSERT INTO categories (id, tenant_id, name) VALUES (:c, :t, 'Food')"
    ), {"c": cat_id, "t": str(tenant_id)})
    
    # Create 3 SKUs for ABC testing (High, Medium, Low consumption)
    sku_high = uuid4()
    await db_session.execute(text(
        "INSERT INTO skus (id, tenant_id, name, base_uom_id, category_id) VALUES (:id, :t, :name, :u, :c)"
    ), {"id": sku_high, "t": str(tenant_id), "name": "High Vol", "u": str(uom_id), "c": str(cat_id)})
    
    sku_med = uuid4()
    await db_session.execute(text(
        "INSERT INTO skus (id, tenant_id, name, base_uom_id, category_id) VALUES (:id, :t, :name, :u, :c)"
    ), {"id": sku_med, "t": str(tenant_id), "name": "Med Vol", "u": str(uom_id), "c": str(cat_id)})
    
    sku_low = uuid4()
    await db_session.execute(text(
        "INSERT INTO skus (id, tenant_id, name, base_uom_id, category_id) VALUES (:id, :t, :name, :u, :c)"
    ), {"id": sku_low, "t": str(tenant_id), "name": "Low Vol", "u": str(uom_id), "c": str(cat_id)})

    # Create balances
    for sku_id in [sku_high, sku_med, sku_low]:
        await db_session.execute(text(
            "INSERT INTO stock_balance_projections (id, tenant_id, location_id, sku_id, quantity, total_value) VALUES (:id, :t, :loc, :s, 10, 100)"
        ), {"id": uuid4(), "t": str(tenant_id), "loc": str(location_id), "s": str(sku_id)})
        
    # Create consumption in stock ledger
    now = datetime.now(timezone.utc)
    for _ in range(5):
        m1 = uuid4()
        m2 = uuid4()
        m3 = uuid4()
        d = now - timedelta(days=5)
        
        await db_session.execute(text(
            "INSERT INTO stock_movements (id, tenant_id, location_id, type, status, created_at, posted_at) VALUES (:m, :t, :loc, 'CONSUMPTION', 'POSTED', :d, :d)"
        ), {"m": m1, "t": str(tenant_id), "loc": str(location_id), "d": d})
        await db_session.execute(text(
            "INSERT INTO stock_ledger_entries (id, tenant_id, movement_id, sku_id, quantity, unit_cost, balance_after, created_at) "
            "VALUES (:id, :t, :m, :s, -100, 10, 10, :d)"
        ), {"id": uuid4(), "t": str(tenant_id), "m": str(m1), "s": str(sku_high), "d": d})
        
        await db_session.execute(text(
            "INSERT INTO stock_movements (id, tenant_id, location_id, type, status, created_at, posted_at) VALUES (:m, :t, :loc, 'CONSUMPTION', 'POSTED', :d, :d)"
        ), {"m": m2, "t": str(tenant_id), "loc": str(location_id), "d": d})
        await db_session.execute(text(
            "INSERT INTO stock_ledger_entries (id, tenant_id, movement_id, sku_id, quantity, unit_cost, balance_after, created_at) "
            "VALUES (:id, :t, :m, :s, -15, 10, 10, :d)"
        ), {"id": uuid4(), "t": str(tenant_id), "m": str(m2), "s": str(sku_med), "d": d})
        
        await db_session.execute(text(
            "INSERT INTO stock_movements (id, tenant_id, location_id, type, status, created_at, posted_at) VALUES (:m, :t, :loc, 'CONSUMPTION', 'POSTED', :d, :d)"
        ), {"m": m3, "t": str(tenant_id), "loc": str(location_id), "d": d})
        await db_session.execute(text(
            "INSERT INTO stock_ledger_entries (id, tenant_id, movement_id, sku_id, quantity, unit_cost, balance_after, created_at) "
            "VALUES (:id, :t, :m, :s, -5, 10, 10, :d)"
        ), {"id": uuid4(), "t": str(tenant_id), "m": str(m3), "s": str(sku_low), "d": d})
        
    await db_session.commit()
    
    return {
        "tenant_id": tenant_id,
        "location_id": location_id,
        "sku_high": sku_high,
        "sku_med": sku_med,
        "sku_low": sku_low
    }

async def test_calculate_abc_classification(db_session: AsyncSession, admin_user, tenant_id):
    data = await setup_intelligence_data(db_session, tenant_id)
    # Set context
    await db_session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(data['tenant_id'])})
    
    service = IntelligenceService(db_session)
    await service.calculate_abc_classification(data['tenant_id'], data['location_id'])
    
    # Verify policies
    res = await db_session.execute(text("SELECT sku_id, abc_class FROM inventory_policies WHERE tenant_id = :t"), {"t": data['tenant_id']})
    policies = {row[0]: row[1] for row in res.fetchall()}
    
    # High: 5 * 100 * 10 = 5000 (83%) -> A
    # Med: 5 * 15 * 10 = 750 (12.5%) -> B
    # Low: 5 * 5 * 10 = 250 (4%) -> C
    assert policies[data['sku_high']] == 'A'
    assert policies[data['sku_med']] == 'B'
    assert policies[data['sku_low']] == 'C'

async def test_generate_purchase_suggestions(db_session: AsyncSession, admin_user, tenant_id):
    data = await setup_intelligence_data(db_session, tenant_id)
    # Set context
    await db_session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(data['tenant_id'])})
    
    t_id = data['tenant_id']
    l_id = data['location_id']
    sku_id = data['sku_high']
    
    # Create policy with target stock
    await db_session.execute(text(
        "INSERT INTO inventory_policies (id, tenant_id, location_id, sku_id, abc_class, target_stock, min_stock, lead_time_days) "
        "VALUES (:id, :t, :l, :s, 'A', 50, 20, 3)"
    ), {"id": uuid4(), "t": t_id, "l": l_id, "s": sku_id})
    
    # On hand is 10 (from setup)
    # Target is 50. Suggestion should be 40.
    
    service = IntelligenceService(db_session)
    suggestions = await service.generate_purchase_suggestions(t_id, l_id)
    
    assert len(suggestions) == 1
    assert suggestions[0].sku_id == sku_id
    assert suggestions[0].suggested_quantity == Decimal('40')
    assert "Target(50.000000000000) - OnHand(10.000000000000) - Inbound(0)" in suggestions[0].reason

async def test_generate_operational_alerts(db_session: AsyncSession, admin_user, tenant_id):
    data = await setup_intelligence_data(db_session, tenant_id)
    # Set context
    await db_session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(data['tenant_id'])})
    
    t_id = data['tenant_id']
    l_id = data['location_id']
    sku_id = data['sku_high'] # monthly cons = 500
    
    # Create policy with lead time and min stock
    await db_session.execute(text(
        "INSERT INTO inventory_policies (id, tenant_id, location_id, sku_id, abc_class, lead_time_days, min_stock, target_stock) "
        "VALUES (:id, :t, :l, :s, 'A', 3, 20, 50)"
    ), {"id": uuid4(), "t": t_id, "l": l_id, "s": sku_id})
    
    # daily baseline = 500 / 30 = 16.66
    # rop = 16.66 * 3 + 20 = 70
    # on hand = 10
    # Alert should trigger
    
    service = IntelligenceService(db_session)
    alerts = await service.generate_operational_alerts(t_id, l_id)
    
    assert len(alerts) == 1
    assert alerts[0].sku_id == sku_id
    assert alerts[0].metric == 'STOCKOUT_RISK'
    assert alerts[0].reference_value >= 70
