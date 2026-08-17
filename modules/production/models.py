import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class ProductionOrder(Base):
    __tablename__ = "production_orders"
    __table_args__ = (
        Index("IX_production_orders_tenant_status", "tenant_id", "status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    order_number = Column(String(50), nullable=False) # e.g. "OP-2026-0001"
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False, index=True)
    recipe_version_id = Column(UUID(as_uuid=True), ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=False)
    produced_sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    status = Column(String(50), nullable=False, default="PLANNED") # 'PLANNED', 'IN_PRODUCTION', 'COMPLETED', 'CANCELLED'
    
    planned_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    actual_quantity = Column(Numeric(precision=24, scale=12), nullable=True) # Real yield obtained
    
    batch_number = Column(String(100), nullable=True) # Lot / Lote de fabricação
    produced_at = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True) # Shelf life
    
    total_cost = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    unit_cost = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProductionOrderIngredient(Base):
    __tablename__ = "production_order_ingredients"
    __table_args__ = (
        Index("IX_production_order_ingredients_tenant_order", "tenant_id", "production_order_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    production_order_id = Column(UUID(as_uuid=True), ForeignKey("production_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    planned_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    actual_quantity = Column(Numeric(precision=24, scale=12), nullable=True)
    
    unit_cost = Column(Numeric(precision=24, scale=12), nullable=False, default=0) # CMP at production time
    total_cost = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
