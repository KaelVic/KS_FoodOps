import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from modules.purchasing.models import (
    PurchaseOrder, PurchaseOrderLine, GoodsReceipt, GoodsReceiptLine,
    SupplierInvoice, SupplierInvoiceLine, PurchaseReconciliation
)
from modules.inventory.service import InventoryService


class PurchasingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def receive_purchase_order(self, po_id: uuid.UUID, tenant_id: uuid.UUID, receipt_lines_data: List[Dict]) -> GoodsReceipt:
        """
        Receives a Purchase Order, generating a Goods Receipt and updating PO status.
        receipt_lines_data format: [{'po_line_id': UUID, 'sku_id': UUID, 'quantity': Decimal, 'unit_price': Decimal}]
        """
        now = datetime.now(timezone.utc)
        
        # 1. Fetch the PO
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.tenant_id == tenant_id
        ).with_for_update()
        po = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if not po:
            raise ValueError("Purchase Order not found.")
        if po.status == "CANCELLED":
            raise ValueError("Cannot receive a cancelled Purchase Order.")
            
        # 2. Create Goods Receipt
        receipt = GoodsReceipt(
            tenant_id=tenant_id,
            supplier_id=po.supplier_id,
            location_id=po.location_id,
            purchase_order_id=po.id,
            receipt_date=now,
            status="DRAFT"
        )
        self.session.add(receipt)
        await self.session.flush()
        
        # 3. Process Lines
        for line_data in receipt_lines_data:
            receipt_line = GoodsReceiptLine(
                tenant_id=tenant_id,
                receipt_id=receipt.id,
                sku_id=line_data['sku_id'],
                quantity=Decimal(line_data['quantity']),
                unit_price=Decimal(line_data['unit_price']),
                purchase_order_line_id=line_data.get('po_line_id')
            )
            self.session.add(receipt_line)
            await self.session.flush()
            
            # Create a reconciliation record for this receipt line
            if line_data.get('po_line_id'):
                recon = PurchaseReconciliation(
                    tenant_id=tenant_id,
                    purchase_order_line_id=line_data['po_line_id'],
                    receipt_line_id=receipt_line.id,
                    status="UNMATCHED"
                )
                self.session.add(recon)
        
        await self.session.flush()
        
        # 4. Check if fully received
        # Sum of ordered
        stmt = select(func.sum(PurchaseOrderLine.ordered_quantity)).where(PurchaseOrderLine.purchase_order_id == po_id)
        total_ordered = (await self.session.execute(stmt)).scalar_one() or Decimal('0')
        
        # Sum of received
        stmt = select(func.sum(GoodsReceiptLine.quantity)).where(
            GoodsReceiptLine.receipt_id == receipt.id, # wait, we need all receipts for this PO
        )
        # Actually, sum across ALL receipts for this PO:
        stmt = select(func.sum(GoodsReceiptLine.quantity)).join(
            GoodsReceipt, GoodsReceipt.id == GoodsReceiptLine.receipt_id
        ).where(
            GoodsReceipt.purchase_order_id == po_id,
            GoodsReceipt.tenant_id == tenant_id,
            GoodsReceiptLine.tenant_id == tenant_id
        )
        total_received = (await self.session.execute(stmt)).scalar_one() or Decimal('0')
        
        if total_received >= total_ordered and total_ordered > 0:
            po.status = "FULLY_RECEIVED"
        else:
            po.status = "PARTIAL_RECEIPT"
            
        # 5. Post the Goods Receipt using InventoryService to affect stock
        inv_service = InventoryService(self.session)
        await inv_service.post_goods_receipt(receipt.id, tenant_id)
        
        # Call reconciliation logic for the lines we just added
        await self._evaluate_reconciliations(po_id, tenant_id)
        
        return receipt

    async def register_supplier_invoice(self, po_id: uuid.UUID, tenant_id: uuid.UUID, invoice_data: Dict, invoice_lines_data: List[Dict]) -> SupplierInvoice:
        """
        Registers a Supplier Invoice against a Purchase Order.
        invoice_lines_data format: [{'po_line_id': UUID, 'sku_id': UUID, 'invoiced_quantity': Decimal, 'unit_price': Decimal}]
        """
        # 1. Fetch PO to ensure it exists
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == tenant_id
        )
        po = (await self.session.execute(stmt)).scalar_one_or_none()
        if not po:
            raise ValueError("Purchase Order not found.")
            
        # 2. Create Invoice
        invoice = SupplierInvoice(
            tenant_id=tenant_id,
            supplier_id=po.supplier_id,
            invoice_number=invoice_data['invoice_number'],
            issue_date=invoice_data['issue_date'],
            due_date=invoice_data.get('due_date'),
            total_amount=Decimal(invoice_data['total_amount'])
        )
        self.session.add(invoice)
        await self.session.flush()
        
        # 3. Create Invoice Lines
        for line_data in invoice_lines_data:
            inv_line = SupplierInvoiceLine(
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                sku_id=line_data['sku_id'],
                invoiced_quantity=Decimal(line_data['invoiced_quantity']),
                unit_price=Decimal(line_data['unit_price'])
            )
            self.session.add(inv_line)
            await self.session.flush()
            
            # Create a reconciliation record for this invoice line (or update an existing one if possible)
            # For simplicity, we create a new reconciliation record for the invoice line
            if line_data.get('po_line_id'):
                recon = PurchaseReconciliation(
                    tenant_id=tenant_id,
                    purchase_order_line_id=line_data['po_line_id'],
                    invoice_line_id=inv_line.id,
                    status="UNMATCHED"
                )
                self.session.add(recon)
                
        await self.session.flush()
        
        # 4. Evaluate reconciliations
        await self._evaluate_reconciliations(po_id, tenant_id)
        
        return invoice
        
    async def _evaluate_reconciliations(self, po_id: uuid.UUID, tenant_id: uuid.UUID):
        """
        Evaluates and updates the reconciliation status of all lines belonging to a Purchase Order.
        """
        # Fetch all PO lines
        stmt = select(PurchaseOrderLine).where(
            PurchaseOrderLine.purchase_order_id == po_id,
            PurchaseOrderLine.tenant_id == tenant_id
        )
        po_lines = (await self.session.execute(stmt)).scalars().all()
        
        for po_line in po_lines:
            ordered_qty = po_line.ordered_quantity
            ordered_price = po_line.unit_price
            
            # Fetch all receipt lines for this PO line
            stmt_recv = select(func.coalesce(func.sum(GoodsReceiptLine.quantity), 0)).where(
                GoodsReceiptLine.purchase_order_line_id == po_line.id,
                GoodsReceiptLine.tenant_id == tenant_id
            )
            received_qty = Decimal((await self.session.execute(stmt_recv)).scalar_one())
            
            # Fetch all invoice lines for this PO line (linked via PurchaseReconciliation)
            stmt_inv = select(func.coalesce(func.sum(SupplierInvoiceLine.invoiced_quantity), 0)).select_from(PurchaseReconciliation).join(
                SupplierInvoiceLine, PurchaseReconciliation.invoice_line_id == SupplierInvoiceLine.id
            ).where(
                PurchaseReconciliation.purchase_order_line_id == po_line.id,
                PurchaseReconciliation.tenant_id == tenant_id,
                SupplierInvoiceLine.tenant_id == tenant_id
            )
            invoiced_qty = Decimal((await self.session.execute(stmt_inv)).scalar_one())
            
            # We also check for price discrepancies on the invoices
            # Get max invoiced price
            stmt_price = select(func.max(SupplierInvoiceLine.unit_price)).select_from(PurchaseReconciliation).join(
                SupplierInvoiceLine, PurchaseReconciliation.invoice_line_id == SupplierInvoiceLine.id
            ).where(
                PurchaseReconciliation.purchase_order_line_id == po_line.id,
                PurchaseReconciliation.tenant_id == tenant_id,
                SupplierInvoiceLine.tenant_id == tenant_id
            )
            max_inv_price = (await self.session.execute(stmt_price)).scalar_one_or_none()
            
            status = "MATCHED"
            
            if ordered_qty != received_qty or ordered_qty != invoiced_qty:
                status = "QUANTITY_DISCREPANCY"
            elif max_inv_price is not None and max_inv_price != ordered_price:
                status = "PRICE_DISCREPANCY"
                
            # Update all recon records for this PO line
            stmt_update = select(PurchaseReconciliation).where(
                PurchaseReconciliation.purchase_order_line_id == po_line.id,
                PurchaseReconciliation.tenant_id == tenant_id
            )
            recons = (await self.session.execute(stmt_update)).scalars().all()
            for r in recons:
                r.status = status
