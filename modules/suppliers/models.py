import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50), nullable=True) # CNPJ/CPF etc
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SupplierSKU(Base):
    __tablename__ = "supplier_skus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="CASCADE"), nullable=False)
    supplier_item_code = Column(String(100), nullable=True)
    supplier_uom_id = Column(UUID(as_uuid=True), ForeignKey("uoms.id", ondelete="RESTRICT"), nullable=True)
    default_conversion_version_id = Column(UUID(as_uuid=True), ForeignKey("sku_conversion_versions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SupplierSKUAlias(Base):
    __tablename__ = "supplier_sku_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_sku_id = Column(UUID(as_uuid=True), ForeignKey("supplier_skus.id", ondelete="CASCADE"), nullable=False)
    alias_name = Column(String(255), nullable=False) # e.g. "TOMATE CARMEM KG" from OCR
    created_at = Column(DateTime(timezone=True), server_default=func.now())
