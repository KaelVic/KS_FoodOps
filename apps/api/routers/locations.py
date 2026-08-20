import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from packages.security.dependencies import get_secure_session, get_tenant_id_from_header, require_permission
from packages.tenant.service import TenantService

router = APIRouter()

class LocationBase(BaseModel):
    name: str = Field(..., example="Estoque Seco")
    business_unit_id: uuid.UUID

class LocationUpdate(BaseModel):
    name: str

class LocationResponse(LocationBase):
    id: uuid.UUID
    tenant_id: uuid.UUID

    class Config:
        from_attributes = True

@router.get("", response_model=List[LocationResponse])
async def list_locations(
    _perm: bool = Depends(require_permission("inventory.read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await TenantService.list_locations(db, tenant_id)

@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: LocationBase,
    _perm: bool = Depends(require_permission("inventory.adjust")),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        loc = await TenantService.create_location(db, tenant_id, payload.business_unit_id, payload.name)
        await db.commit()
        return loc
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: uuid.UUID,
    payload: LocationUpdate,
    _perm: bool = Depends(require_permission("inventory.adjust")),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        loc = await TenantService.update_location(db, tenant_id, location_id, payload.name)
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")
        await db.commit()
        return loc
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
