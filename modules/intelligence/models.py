import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class InventoryPolicy(Base):
    """
    Stores baseline operational parameters for a SKU at a Location.
    """
    __tablename__ = "inventory_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="CASCADE"), nullable=False, index=True)
    
    min_stock = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    target_stock = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    lead_time_days = Column(Integer, nullable=False, default=0)
    abc_class = Column(String(1), nullable=True) # 'A', 'B', 'C'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class PurchaseSuggestion(Base):
    """
    A generated, deterministic purchase recommendation based on the policy and baseline consumption.
    """
    __tablename__ = "purchase_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="CASCADE"), nullable=False, index=True)
    
    suggested_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING") # PENDING, ACCEPTED, REJECTED
    reason = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OperationalAlert(Base):
    """
    Anomalies or thresholds breached in the inventory lifecycle (e.g. PPV, stockouts).
    """
    __tablename__ = "operational_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=True, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="CASCADE"), nullable=False, index=True)
    
    metric = Column(String(100), nullable=False) # e.g., 'STOCKOUT_RISK', 'PRICE_VARIANCE'
    observed_value = Column(Numeric(precision=24, scale=12), nullable=False)
    reference_value = Column(Numeric(precision=24, scale=12), nullable=False)
    threshold = Column(Numeric(precision=24, scale=12), nullable=False)
    
    reason = Column(String(500), nullable=False)
    is_resolved = Column(Boolean, nullable=False, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
