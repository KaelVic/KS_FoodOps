import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    type = Column(String(50), nullable=False) # e.g. 'RECEIPT', 'ADJUSTMENT', 'TRANSFER', 'REVERSAL'
    status = Column(String(50), nullable=False) # 'DRAFT', 'POSTED', 'REVERSED'
    reference_id = Column(UUID(as_uuid=True), nullable=True) # ID of the triggering entity (e.g. GoodsReceipt)
    reference_type = Column(String(100), nullable=True) # e.g. 'GoodsReceipt', 'StockMovement' (for reversal)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    posted_at = Column(DateTime(timezone=True), nullable=True)

class StockLedgerEntry(Base):
    __tablename__ = "stock_ledger_entries"
    __table_args__ = (
        Index('IX_stock_ledger_entries_tenant_sku_date', 'tenant_id', 'sku_id', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_id = Column(UUID(as_uuid=True), ForeignKey("stock_movements.id", ondelete="RESTRICT"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(precision=24, scale=12), nullable=False) # Positive or negative
    unit_cost = Column(Numeric(precision=24, scale=12), nullable=True) # Cost at the time of entry
    conversion_version_id = Column(UUID(as_uuid=True), ForeignKey("sku_conversion_versions.id", ondelete="RESTRICT"), nullable=True)
    balance_after = Column(Numeric(precision=24, scale=12), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StockBalanceProjection(Base):
    __tablename__ = "stock_balance_projections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    total_value = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class InventorySession(Base):
    __tablename__ = "inventory_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False) # 'DRAFT', 'OPEN', 'COUNTING', 'REVIEW', 'CLOSED'
    cutoff_at = Column(DateTime(timezone=True), nullable=True) # Timestamp for exact expected stock reproduction
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

class InventorySessionLocation(Base):
    __tablename__ = "inventory_session_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("inventory_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)

class InventoryCountLine(Base):
    __tablename__ = "inventory_count_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("inventory_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    counted_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class InventoryCloseResult(Base):
    __tablename__ = "inventory_close_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("inventory_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    expected_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    counted_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    variance_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    variance_value = Column(Numeric(precision=24, scale=12), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LossRecord(Base):
    __tablename__ = "loss_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    movement_id = Column(UUID(as_uuid=True), ForeignKey("stock_movements.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    actor = Column(String(100), nullable=True) # e.g. employee name
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TheoreticalConsumption(Base):
    __tablename__ = "theoretical_consumptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_line_id = Column(UUID(as_uuid=True), ForeignKey("sale_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    recipe_version_id = Column(UUID(as_uuid=True), ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=False)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Numeric(precision=24, scale=12), nullable=False) # In SKU's base UOM
    unit_cost_at_time = Column(Numeric(precision=24, scale=12), nullable=True) # Preserved cost for variance
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default='OPEN') # 'OPEN', 'CLOSED'
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StockTransfer(Base):
    __tablename__ = "stock_transfers"
    __table_args__ = (
        Index("IX_stock_transfers_tenant_status", "tenant_id", "status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    transfer_number = Column(String(50), nullable=False) # e.g. "TRF-0001"
    origin_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    destination_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    status = Column(String(50), nullable=False, default="DRAFT") # 'DRAFT', 'IN_TRANSIT', 'RECEIVED', 'CANCELLED'
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"
    __table_args__ = (
        Index("IX_stock_transfer_items_tenant_transfer", "tenant_id", "transfer_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    transfer_id = Column(UUID(as_uuid=True), ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_sent = Column(Numeric(precision=24, scale=12), nullable=False)
    quantity_received = Column(Numeric(precision=24, scale=12), nullable=True)
    unit_cost = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

