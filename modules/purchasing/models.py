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


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    rfq_number = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="DRAFT") # DRAFT, OPEN, EVALUATING, AWARDED, CANCELLED
    deadline = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RFQItem(Base):
    __tablename__ = "rfq_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    target_price = Column(Numeric(precision=24, scale=12), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RFQSupplier(Base):
    __tablename__ = "rfq_suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="INVITED") # INVITED, SUBMITTED, DECLINED
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RFQProposal(Base):
    __tablename__ = "rfq_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    rfq_id = Column(UUID(as_uuid=True), ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    freight_cost = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    delivery_days = Column(String(50), nullable=True, default="0")
    payment_terms = Column(String(100), nullable=True)
    min_order_value = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    notes = Column(String(500), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())


class RFQProposalItem(Base):
    __tablename__ = "rfq_proposal_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("rfq_proposals.id", ondelete="CASCADE"), nullable=False, index=True)
    rfq_item_id = Column(UUID(as_uuid=True), ForeignKey("rfq_items.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_price = Column(Numeric(precision=24, scale=12), nullable=False)
    available_quantity = Column(Numeric(precision=24, scale=12), nullable=True)
    brand_or_spec = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

