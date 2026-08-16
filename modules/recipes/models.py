import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False) # e.g. 'MENU_ITEM', 'PREPARED_ITEM'
    pos_code = Column(String(100), nullable=True) # Optional direct link
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RecipeVersion(Base):
    __tablename__ = "recipe_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False) # 'DRAFT', 'PUBLISHED', 'ARCHIVED'
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    
    yield_quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    yield_uom_id = Column(UUID(as_uuid=True), ForeignKey("uoms.id", ondelete="RESTRICT"), nullable=False)
    
    portion_size = Column(Numeric(precision=24, scale=12), nullable=False)
    portion_uom_id = Column(UUID(as_uuid=True), ForeignKey("uoms.id", ondelete="RESTRICT"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    recipe_version_id = Column(UUID(as_uuid=True), ForeignKey("recipe_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id", ondelete="RESTRICT"), nullable=False)
    
    quantity = Column(Numeric(precision=24, scale=12), nullable=False)
    uom_id = Column(UUID(as_uuid=True), ForeignKey("uoms.id", ondelete="RESTRICT"), nullable=False)
    loss_percentage = Column(Numeric(precision=5, scale=2), nullable=False, default=0) # 0 to 100
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
