import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from modules.suppliers.models import Supplier

class SupplierService:

    @staticmethod
    async def list_suppliers(db: AsyncSession, tenant_id: uuid.UUID) -> List[Supplier]:
        stmt = select(Supplier).where(Supplier.tenant_id == tenant_id).order_by(Supplier.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_supplier(db: AsyncSession, tenant_id: uuid.UUID, supplier_id: uuid.UUID) -> Optional[Supplier]:
        stmt = select(Supplier).where(Supplier.tenant_id == tenant_id, Supplier.id == supplier_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_supplier(db: AsyncSession, tenant_id: uuid.UUID, name: str, tax_id: Optional[str] = None) -> Supplier:
        supplier = Supplier(tenant_id=tenant_id, name=name, tax_id=tax_id, is_active=True)
        db.add(supplier)
        await db.flush()
        return supplier

    @staticmethod
    async def update_supplier(db: AsyncSession, tenant_id: uuid.UUID, supplier_id: uuid.UUID, name: Optional[str] = None, tax_id: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[Supplier]:
        supplier = await SupplierService.get_supplier(db, tenant_id, supplier_id)
        if not supplier:
            return None
        if name is not None:
            supplier.name = name
        if tax_id is not None:
            supplier.tax_id = tax_id
        if is_active is not None:
            supplier.is_active = is_active
        await db.flush()
        return supplier
