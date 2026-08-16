import uuid
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from modules.catalog.service import CatalogService

router = APIRouter()

# Pydantic Schemas
class UOMBase(BaseModel):
    name: str = Field(..., example="Kilogram")
    symbol: str = Field(..., example="kg")
    base_type: str = Field(..., example="mass")

class UOMResponse(UOMBase):
    id: uuid.UUID
    tenant_id: uuid.UUID

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str = Field(..., example="Meat")
    parent_id: Optional[uuid.UUID] = None

class CategoryResponse(CategoryBase):
    id: uuid.UUID
    tenant_id: uuid.UUID

    class Config:
        from_attributes = True

class SKUBase(BaseModel):
    name: str = Field(..., example="Picanha")
    category_id: Optional[uuid.UUID] = None
    base_uom_id: uuid.UUID

class SKUUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None

class SKUResponse(SKUBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool

    class Config:
        from_attributes = True

class ConversionPayload(BaseModel):
    from_uom_id: uuid.UUID
    to_uom_id: uuid.UUID
    factor: Decimal

class ConversionResponse(ConversionPayload):
    id: uuid.UUID
    tenant_id: uuid.UUID
    sku_id: uuid.UUID
    version_number: int

    class Config:
        from_attributes = True

# UOM Endpoints
@router.get("/uoms", response_model=List[UOMResponse])
async def list_uoms(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await CatalogService.list_uoms(db, tenant_id)

@router.post("/uoms", response_model=UOMResponse, status_code=status.HTTP_201_CREATED)
async def create_uom(
    payload: UOMBase,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await CatalogService.create_uom(db, tenant_id, payload.name, payload.symbol, payload.base_type)

# Category Endpoints
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await CatalogService.list_categories(db, tenant_id)

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryBase,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await CatalogService.create_category(db, tenant_id, payload.name, payload.parent_id)

# SKU Endpoints
@router.get("/skus", response_model=List[SKUResponse])
async def list_skus(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await CatalogService.list_skus(db, tenant_id)

@router.post("/skus", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
async def create_sku(
    payload: SKUBase,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await CatalogService.create_sku(db, tenant_id, payload.name, payload.base_uom_id, payload.category_id)

@router.put("/skus/{sku_id}", response_model=SKUResponse)
async def update_sku(
    sku_id: uuid.UUID,
    payload: SKUUpdate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    sku = await CatalogService.update_sku(db, tenant_id, sku_id, payload.name, payload.category_id, payload.is_active)
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    return sku

@router.post("/skus/{sku_id}/conversions", response_model=ConversionResponse, status_code=status.HTTP_201_CREATED)
async def create_sku_conversion(
    sku_id: uuid.UUID,
    payload: ConversionPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    sku = await CatalogService.get_sku(db, tenant_id, sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")
    
    return await CatalogService.create_sku_conversion(
        db, tenant_id, sku_id, payload.from_uom_id, payload.to_uom_id, payload.factor
    )
