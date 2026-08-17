import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("menu_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    pos_code = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    sale_price = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    cost_price = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    target_cmv_percentage = Column(Numeric(precision=5, scale=2), nullable=False, default=30.00) # e.g. 30.00%
    
    is_active = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
