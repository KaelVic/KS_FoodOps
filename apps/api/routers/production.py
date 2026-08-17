import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.security.dependencies import get_tenant_id_from_header, get_secure_session
from modules.production.service import ProductionService

router = APIRouter(prefix="/production", tags=["production"])

# --- SCHEMAS ---

class CreateProductionOrderPayload(BaseModel):
    recipe_id: uuid.UUID
    produced_sku_id: uuid.UUID
    location_id: uuid.UUID
    planned_quantity: Decimal = Field(..., gt=0)
    batch_number: Optional[str] = None
    expiration_date: Optional[datetime] = None
    notes: Optional[str] = None

class CompleteProductionPayload(BaseModel):
    actual_quantity: Optional[Decimal] = Field(None, gt=0)
    batch_number: Optional[str] = None
    expiration_date: Optional[datetime] = None
    actual_ingredient_quantities: Optional[Dict[str, Decimal]] = None


# --- ENDPOINTS ---

@router.get("/orders")
async def list_production_orders(
    status: Optional[str] = Query(None),
    location_id: Optional[uuid.UUID] = Query(None),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    return await ProductionService.list_orders(
        session=session,
        tenant_id=tenant_id,
        status=status,
        location_id=location_id,
    )


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_production_order(
    payload: CreateProductionOrderPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    try:
        order = await ProductionService.create_order(
            session=session,
            tenant_id=tenant_id,
            recipe_id=payload.recipe_id,
            produced_sku_id=payload.produced_sku_id,
            location_id=payload.location_id,
            planned_quantity=payload.planned_quantity,
            notes=payload.notes,
            batch_number=payload.batch_number,
            expiration_date=payload.expiration_date,
        )
        res = await ProductionService.get_order_dict(session, tenant_id, order.id)
        await session.commit()
        return res
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders/{order_id}")
async def get_production_order_detail(
    order_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    order = await ProductionService.get_order_dict(session, tenant_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de Produção não encontrada.")
    return order


@router.post("/orders/{order_id}/start")
async def start_production_order(
    order_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    try:
        await ProductionService.start_production(session, tenant_id, order_id)
        res = await ProductionService.get_order_dict(session, tenant_id, order_id)
        await session.commit()
        return res
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/complete")
async def complete_production_order(
    order_id: uuid.UUID,
    payload: CompleteProductionPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    try:
        await ProductionService.complete_production(
            session=session,
            tenant_id=tenant_id,
            order_id=order_id,
            actual_quantity=payload.actual_quantity,
            batch_number=payload.batch_number,
            expiration_date=payload.expiration_date,
            actual_ingredient_quantities=payload.actual_ingredient_quantities,
        )
        res = await ProductionService.get_order_dict(session, tenant_id, order_id)
        await session.commit()
        return res
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
