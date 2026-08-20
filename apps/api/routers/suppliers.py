import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from packages.security.dependencies import get_secure_session, get_tenant_id_from_header, require_permission
from modules.suppliers.service import SupplierService

router = APIRouter()

class SupplierBase(BaseModel):
    name: str = Field(..., example="Distribuidora de Bebidas Ltda")
    tax_id: Optional[str] = Field(None, example="12.345.678/0001-99")

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    is_active: Optional[bool] = None

class SupplierResponse(SupplierBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool

    class Config:
        from_attributes = True

@router.get("", response_model=List[SupplierResponse])
async def list_suppliers(
    _perm: bool = Depends(require_permission("purchasing.read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await SupplierService.list_suppliers(db, tenant_id)

@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    payload: SupplierBase,
    _perm: bool = Depends(require_permission("purchasing.create")),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        supplier = await SupplierService.create_supplier(db, tenant_id, payload.name, payload.tax_id)
        await db.commit()
        return supplier
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: uuid.UUID,
    payload: SupplierUpdate,
    _perm: bool = Depends(require_permission("purchasing.create")),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        supplier = await SupplierService.update_supplier(db, tenant_id, supplier_id, payload.name, payload.tax_id, payload.is_active)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        await db.commit()
        return supplier
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
