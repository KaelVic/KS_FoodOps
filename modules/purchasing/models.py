import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=True, index=True)
    receipt_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="DRAFT") # 'DRAFT', 'POSTED'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    posted_at = Column(DateTime(timezone=True), nullable=True)

class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_order_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="RESTRICT"), nullable=True, index=True)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    supplier_sku_id = Column(UUID(as_uuid=True), ForeignKey("supplier_skus.id", ondelete="SET NULL"), nullable=True)
    quantity = Column(Numeric(precision=24, scale=12), nullable=False) # Received quantity in supplier UOM or base UOM
    unit_price = Column(Numeric(precision=24, scale=12), nullable=False) # Price per received unit
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(50), nullable=False, default="DRAFT") # DRAFT, APPROVED, SENT, PARTIAL_RECEIPT, FULLY_RECEIVED, CANCELLED
    order_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_order_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    supplier_sku_id = Column(UUID(as_uuid=True), ForeignKey("supplier_skus.id", ondelete="SET NULL"), nullable=True)
    ordered_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    unit_price = Column(Numeric(precision=24, scale=12), nullable=False)

class SupplierInvoice(Base):
    __tablename__ = "supplier_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    invoice_number = Column(String(100), nullable=False)
    issue_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    total_amount = Column(Numeric(precision=24, scale=12), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SupplierInvoiceLine(Base):
    __tablename__ = "supplier_invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("supplier_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    supplier_sku_id = Column(UUID(as_uuid=True), ForeignKey("supplier_skus.id", ondelete="SET NULL"), nullable=True)
    invoiced_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    unit_price = Column(Numeric(precision=24, scale=12), nullable=False)

class PurchaseReconciliation(Base):
    __tablename__ = "purchase_reconciliations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_order_line_id = Column(UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    receipt_line_id = Column(UUID(as_uuid=True), ForeignKey("goods_receipt_lines.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_line_id = Column(UUID(as_uuid=True), ForeignKey("supplier_invoice_lines.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="UNMATCHED") # MATCHED, QUANTITY_DISCREPANCY, PRICE_DISCREPANCY, UNMATCHED
