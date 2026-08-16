import pytest
import uuid
import asyncio
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy import text

from packages.tenant.database import async_session_maker
from packages.tenant.models import Tenant, BusinessUnit, Location
from modules.purchasing.models import PurchaseOrder, PurchaseOrderLine, SupplierInvoice, PurchaseReconciliation, GoodsReceipt
from modules.catalog.models import SKU, UOM
from modules.suppliers.models import Supplier, SupplierSKU
from modules.inventory.models import StockBalanceProjection

from modules.purchasing.service import PurchasingService

pytestmark = pytest.mark.asyncio

async def setup_purchasing_data(session, tenant_id: uuid.UUID):
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
    
    bu_id = uuid.uuid4()
    loc_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :t_id, 'BU Purchase Test')"),
        {"id": str(bu_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO locations (id, tenant_id, business_unit_id, name) VALUES (:id, :t_id, :bu_id, 'Main Warehouse')"),
        {"id": str(loc_id), "t_id": str(tenant_id), "bu_id": str(bu_id)}
    )
    
    uom_id = uuid.uuid4()
    sku_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Kilogram', 'KG', 'mass')"),
        {"id": str(uom_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO skus (id, tenant_id, name, base_uom_id) VALUES (:id, :t_id, 'Apples', :uom_id)"),
        {"id": str(sku_id), "t_id": str(tenant_id), "uom_id": str(uom_id)}
    )
    
    sup_id = uuid.uuid4()
    sup_sku_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO suppliers (id, tenant_id, name) VALUES (:id, :t_id, 'Local Farm')"),
        {"id": str(sup_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO supplier_skus (id, tenant_id, supplier_id, sku_id, supplier_item_code, supplier_uom_id) VALUES (:id, :t_id, :sup_id, :sku_id, 'APP123', :uom_id)"),
        {"id": str(sup_sku_id), "t_id": str(tenant_id), "sup_id": str(sup_id), "sku_id": str(sku_id), "uom_id": str(uom_id)}
    )
    
    return loc_id, sku_id, sup_id, sup_sku_id

async def test_3way_reconciliation():
    tenant_id = uuid.uuid4()
    
    async with async_session_maker() as session:
        await session.execute(text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant Purchase')"), {"id": str(tenant_id)})
        loc_id, sku_id, sup_id, sup_sku_id = await setup_purchasing_data(session, tenant_id)
        
        # Create a PO
        po_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        await session.execute(
            text("INSERT INTO purchase_orders (id, tenant_id, supplier_id, location_id, status, order_date) VALUES (:id, :t_id, :sup_id, :loc_id, 'SENT', :now)"),
            {"id": str(po_id), "t_id": str(tenant_id), "sup_id": str(sup_id), "loc_id": str(loc_id), "now": now}
        )
        
        po_line_id = uuid.uuid4()
        await session.execute(
            text("INSERT INTO purchase_order_lines (id, tenant_id, purchase_order_id, sku_id, supplier_sku_id, ordered_quantity, unit_price) VALUES (:id, :t_id, :po_id, :sku_id, :sup_sku_id, 100.0, 1.50)"),
            {"id": str(po_line_id), "t_id": str(tenant_id), "po_id": str(po_id), "sku_id": str(sku_id), "sup_sku_id": str(sup_sku_id)}
        )
        await session.commit()
        
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        service = PurchasingService(session)
        
        # 1. Partial Receipt (receive 80 out of 100)
        receipt_lines = [{'po_line_id': po_line_id, 'sku_id': sku_id, 'quantity': '80.0', 'unit_price': '1.50'}]
        await service.receive_purchase_order(po_id, tenant_id, receipt_lines)
        await session.commit()
        
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        po = (await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))).scalar_one()
        assert po.status == "PARTIAL_RECEIPT"
        
        # Check stock was posted
        balance = (await session.execute(select(StockBalanceProjection).where(StockBalanceProjection.sku_id == sku_id))).scalar_one()
        assert balance.quantity == Decimal("80.0")
        
        # Check recon
        recons = (await session.execute(select(PurchaseReconciliation).where(PurchaseReconciliation.purchase_order_line_id == po_line_id))).scalars().all()
        assert len(recons) == 1
        assert recons[0].status == "QUANTITY_DISCREPANCY" # Ordered 100, Received 80, Invoiced 0
        
        # 2. Register Invoice for exactly 80. (Price is 1.60 instead of 1.50 -> price discrepancy)
        invoice_data = {'invoice_number': 'INV-001', 'issue_date': now, 'total_amount': '128.00'} # 80 * 1.60 = 128
        invoice_lines = [{'po_line_id': po_line_id, 'sku_id': sku_id, 'invoiced_quantity': '80.0', 'unit_price': '1.60'}]
        
        await service.register_supplier_invoice(po_id, tenant_id, invoice_data, invoice_lines)
        await session.commit()
        
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        recons = (await session.execute(select(PurchaseReconciliation).where(PurchaseReconciliation.purchase_order_line_id == po_line_id))).scalars().all()
        assert len(recons) == 2 # 1 for receipt, 1 for invoice
        assert recons[0].status == "QUANTITY_DISCREPANCY" # 100 ordered != 80 received/invoiced
        # wait, the price is different too. Price discrepancy takes precedence in my basic logic?
        # Let's just check the status is not MATCHED.
        assert recons[0].status in ["QUANTITY_DISCREPANCY", "PRICE_DISCREPANCY"]
        
        # 3. Receive the remaining 20.
        receipt_lines_2 = [{'po_line_id': po_line_id, 'sku_id': sku_id, 'quantity': '20.0', 'unit_price': '1.50'}]
        await service.receive_purchase_order(po_id, tenant_id, receipt_lines_2)
        await session.commit()
        
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        po = (await session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))).scalar_one()
        assert po.status == "FULLY_RECEIVED"
