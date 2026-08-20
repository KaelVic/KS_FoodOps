import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class POSProductMapping(Base):
    __tablename__ = "pos_product_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    pos_product_id = Column(String(100), nullable=False)
    pos_product_name = Column(String(255), nullable=False)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SalesImport(Base):
    __tablename__ = "sales_imports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    pos_system = Column(String(100), nullable=False) # e.g. 'TOAST', 'SQUARE'
    import_reference = Column(String(255), nullable=False) # For idempotency, e.g. 'TOAST_20260813'
    status = Column(String(50), nullable=False) # 'PENDING', 'COMPLETED', 'FAILED'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Sale(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    sales_import_id = Column(UUID(as_uuid=True), ForeignKey("sales_imports.id", ondelete="CASCADE"), nullable=False, index=True)
    pos_sale_id = Column(String(100), nullable=False)
    sale_date = Column(DateTime(timezone=True), nullable=False)
    total_amount = Column(Numeric(precision=24, scale=12), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SaleLine(Base):
    __tablename__ = "sale_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    pos_product_id = Column(String(100), nullable=False)
    quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    unit_price = Column(Numeric(precision=24, scale=12), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
