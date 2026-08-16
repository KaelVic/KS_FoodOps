import uuid
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from modules.catalog.models import SKU, Category, UOM, SKUConversionVersion

class CatalogService:

    @staticmethod
    async def list_uoms(db: AsyncSession, tenant_id: uuid.UUID) -> List[UOM]:
        stmt = select(UOM).where(UOM.tenant_id == tenant_id).order_by(UOM.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_uom(db: AsyncSession, tenant_id: uuid.UUID, name: str, symbol: str, base_type: str) -> UOM:
        uom = UOM(tenant_id=tenant_id, name=name, symbol=symbol, base_type=base_type)
        db.add(uom)
        await db.flush()
        return uom

    @staticmethod
    async def list_categories(db: AsyncSession, tenant_id: uuid.UUID) -> List[Category]:
        stmt = select(Category).where(Category.tenant_id == tenant_id).order_by(Category.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_category(db: AsyncSession, tenant_id: uuid.UUID, name: str, parent_id: Optional[uuid.UUID] = None) -> Category:
        cat = Category(tenant_id=tenant_id, name=name, parent_id=parent_id)
        db.add(cat)
        await db.flush()
        return cat

    @staticmethod
    async def list_skus(db: AsyncSession, tenant_id: uuid.UUID) -> List[SKU]:
        stmt = select(SKU).where(SKU.tenant_id == tenant_id).order_by(SKU.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_sku(db: AsyncSession, tenant_id: uuid.UUID, sku_id: uuid.UUID) -> Optional[SKU]:
        stmt = select(SKU).where(SKU.tenant_id == tenant_id, SKU.id == sku_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_sku(db: AsyncSession, tenant_id: uuid.UUID, name: str, base_uom_id: uuid.UUID, category_id: Optional[uuid.UUID] = None) -> SKU:
        sku = SKU(tenant_id=tenant_id, name=name, base_uom_id=base_uom_id, category_id=category_id, is_active=True)
        db.add(sku)
        await db.flush()
        return sku

    @staticmethod
    async def update_sku(db: AsyncSession, tenant_id: uuid.UUID, sku_id: uuid.UUID, name: Optional[str] = None, category_id: Optional[uuid.UUID] = None, is_active: Optional[bool] = None) -> Optional[SKU]:
        sku = await CatalogService.get_sku(db, tenant_id, sku_id)
        if not sku:
            return None
        if name is not None:
            sku.name = name
        if category_id is not None:
            sku.category_id = category_id
        if is_active is not None:
            sku.is_active = is_active
        await db.flush()
        return sku

    @staticmethod
    async def create_sku_conversion(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        sku_id: uuid.UUID,
        from_uom_id: uuid.UUID,
        to_uom_id: uuid.UUID,
        factor: Decimal
    ) -> SKUConversionVersion:
        # Determine the next version number
        stmt = select(SKUConversionVersion).where(
            SKUConversionVersion.tenant_id == tenant_id,
            SKUConversionVersion.sku_id == sku_id,
            SKUConversionVersion.from_uom_id == from_uom_id,
            SKUConversionVersion.to_uom_id == to_uom_id
        ).order_by(SKUConversionVersion.version_number.desc()).limit(1)
        
        result = await db.execute(stmt)
        latest = result.scalar_one_or_none()
        
        next_version = 1 if not latest else latest.version_number + 1
        
        conversion = SKUConversionVersion(
            tenant_id=tenant_id,
            sku_id=sku_id,
            from_uom_id=from_uom_id,
            to_uom_id=to_uom_id,
            factor=factor,
            version_number=next_version
        )
        db.add(conversion)
        await db.flush()
        return conversion
