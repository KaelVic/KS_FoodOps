import pytest
import uuid
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy import text

from packages.tenant.database import async_session_maker
from packages.tenant.models import Tenant, BusinessUnit, Location
from modules.catalog.models import UOM, Category, SKU, SKUConversionVersion
from modules.suppliers.models import Supplier, SupplierSKU
from modules.purchasing.models import GoodsReceipt, GoodsReceiptLine
from modules.inventory.models import StockMovement, StockLedgerEntry, StockBalanceProjection
from modules.inventory.service import InventoryService

pytestmark = pytest.mark.asyncio

async def setup_test_data(session, tenant_id: uuid.UUID):
    # Setup Tenant Context
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
    
    # 1. Basic Tenant and Location setup
    bu_id = uuid.uuid4()
    loc_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :t_id, :name)"),
        {"id": str(bu_id), "t_id": str(tenant_id), "name": "BU Test"}
    )
    await session.execute(
        text("INSERT INTO locations (id, tenant_id, business_unit_id, name) VALUES (:id, :t_id, :bu_id, :name)"),
        {"id": str(loc_id), "t_id": str(tenant_id), "bu_id": str(bu_id), "name": "Main Kitchen"}
    )
    
    # 2. UOM and SKU
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

    # 3. Supplier
    supp_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO suppliers (id, tenant_id, name) VALUES (:id, :t_id, 'Fresh Farms')"),
        {"id": str(supp_id), "t_id": str(tenant_id)}
    )
    
    return loc_id, uom_id, sku_id, supp_id


async def test_goods_receipt_posting_and_idempotency():
    tenant_id = uuid.uuid4()
    
    async with async_session_maker() as session:
        # Create tenant manually
        await session.execute(text("INSERT INTO tenants (id, name) VALUES (:id, :name)"), {"id": str(tenant_id), "name": "Ledger Tenant"})
        
        loc_id, uom_id, sku_id, supp_id = await setup_test_data(session, tenant_id)
        
        # Create GoodsReceipt
        receipt_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        await session.execute(
            text("INSERT INTO goods_receipts (id, tenant_id, supplier_id, location_id, receipt_date, status) VALUES (:id, :t_id, :s_id, :l_id, :r_date, 'DRAFT')"),
            {"id": str(receipt_id), "t_id": str(tenant_id), "s_id": str(supp_id), "l_id": str(loc_id), "r_date": now}
        )
        await session.execute(
            text("INSERT INTO goods_receipt_lines (id, tenant_id, receipt_id, sku_id, quantity, unit_price) VALUES (:id, :t_id, :r_id, :sku_id, 10.5, 2.0)"),
            {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "r_id": str(receipt_id), "sku_id": str(sku_id)}
        )
        await session.commit()
        
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        service = InventoryService(session)
        
        # Post the receipt
        movement = await service.post_goods_receipt(receipt_id, tenant_id)
        await session.commit()
        
        # New transaction begins here, must re-set context for RLS
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        assert movement is not None
        assert movement.status == 'POSTED'
        assert movement.reference_id == receipt_id
        
        # Verify Balance Projection
        stmt = select(StockBalanceProjection).where(StockBalanceProjection.sku_id == sku_id)
        balance = (await session.execute(stmt)).scalar_one()
        assert balance.quantity == Decimal("10.5")
        assert balance.total_value == Decimal("21.0")
        
        # Verify Ledger Entry
        stmt = select(StockLedgerEntry).where(StockLedgerEntry.movement_id == movement.id)
        entry = (await session.execute(stmt)).scalar_one()
        assert entry.quantity == Decimal("10.5")
        assert entry.unit_cost == Decimal("2.0")
        assert entry.balance_after == Decimal("10.5")

    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        service = InventoryService(session)
        
        # Test Idempotency
        movement_second = await service.post_goods_receipt(receipt_id, tenant_id)
        await session.commit()
        
        # New transaction begins here, must re-set context for RLS
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        assert movement_second.id == movement.id
        
        # Ensure balances did not double
        stmt = select(StockBalanceProjection).where(StockBalanceProjection.sku_id == sku_id)
        balance = (await session.execute(stmt)).scalar_one()
        assert balance.quantity == Decimal("10.5")
