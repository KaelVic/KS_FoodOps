import uuid
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from modules.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders & POS"])


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================
class TableBase(BaseModel):
    table_number: str = Field(..., example="Mesa 01")
    capacity: int = Field(4, example=4)
    section: str = Field("Salão Principal", example="Salão Principal")
    status: str = Field("AVAILABLE", example="AVAILABLE")


class TableCreate(TableBase):
    pass


class TableUpdate(BaseModel):
    table_number: Optional[str] = None
    capacity: Optional[int] = None
    section: Optional[str] = None
    status: Optional[str] = None


class TableStatusUpdate(BaseModel):
    status: str = Field(..., example="OCCUPIED")


class TableResponse(TableBase):
    id: str
    active_order_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class OrderItemInput(BaseModel):
    menu_item_id: Optional[uuid.UUID] = None
    name: str = Field(..., example="Picanha Premium Grelhada")
    quantity: Decimal = Field(Decimal("1"), example="1.00")
    unit_price: Decimal = Field(..., example="79.90")
    preparation_notes: Optional[str] = Field(None, example="Ponto da carne: mal passada")
    production_station: Optional[str] = Field(None, example="KITCHEN")


class OrderItemResponse(BaseModel):
    id: str
    menu_item_id: Optional[str] = None
    name: str
    quantity: float
    unit_price: float
    total_price: float
    preparation_notes: Optional[str] = None
    production_station: str
    status: str
    started_at: Optional[str] = None
    ready_at: Optional[str] = None
    served_at: Optional[str] = None


class OrderCreate(BaseModel):
    channel: str = Field("DINE_IN", example="DINE_IN")
    table_id: Optional[uuid.UUID] = None
    customer_name: Optional[str] = Field(None, example="Roberto Silva")
    customer_phone: Optional[str] = Field(None, example="11999998888")
    delivery_address: Optional[str] = Field(None, example="Av. Paulista, 1000, Apto 42")
    waiter_name: Optional[str] = Field(None, example="Carlos Garçom")
    delivery_fee: Decimal = Field(Decimal("0"), example="8.00")
    discount_amount: Decimal = Field(Decimal("0"), example="0.00")
    notes: Optional[str] = Field(None, example="Entregar na portaria")
    payment_method: Optional[str] = Field(None, example="CREDIT_CARD")
    items: Optional[List[OrderItemInput]] = None


class OrderAddItems(BaseModel):
    items: List[OrderItemInput]


class OrderCloseAndPay(BaseModel):
    payment_method: str = Field("CREDIT_CARD", example="CREDIT_CARD")
    acquirer_id: Optional[uuid.UUID] = None
    bank_account_id: Optional[uuid.UUID] = None


class OrderResponse(BaseModel):
    id: str
    order_number: str
    channel: str
    status: str
    table_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    waiter_name: Optional[str] = None
    subtotal: float
    delivery_fee: float
    discount_amount: float
    total_amount: float
    notes: Optional[str] = None
    payment_method: Optional[str] = None
    is_paid: bool
    created_at: Optional[str] = None
    items: List[OrderItemResponse] = []


class KDSStatusUpdate(BaseModel):
    status: str = Field(..., example="PREPARING")


class DeliveryStatusUpdate(BaseModel):
    status: str = Field(..., example="OUT_FOR_DELIVERY")


# ==========================================
# ENDPOINTS: DINING TABLES
# ==========================================
@router.get("/tables", response_model=List[TableResponse])
async def list_tables(
    section: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    return await OrderService.list_tables(session, tenant_id, section=section, status=status)


@router.post("/tables", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
async def create_table(
    payload: TableCreate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    res = await OrderService.create_table(session, tenant_id, payload.model_dump())
    await session.commit()
    return res


@router.put("/tables/{table_id}", response_model=TableResponse)
async def update_table(
    table_id: uuid.UUID,
    payload: TableUpdate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    res = await OrderService.update_table(session, tenant_id, table_id, payload.model_dump(exclude_unset=True))
    if not res:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    await session.commit()
    return res


@router.patch("/tables/{table_id}/status", response_model=TableResponse)
async def update_table_status(
    table_id: uuid.UUID,
    payload: TableStatusUpdate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    res = await OrderService.update_table_status(session, tenant_id, table_id, payload.status)
    if not res:
        raise HTTPException(status_code=404, detail="Mesa não encontrada")
    await session.commit()
    return res


# ==========================================
# ENDPOINTS: ORDERS & COMANDAS
# ==========================================
@router.get("", response_model=List[OrderResponse])
async def list_orders(
    channel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_paid: Optional[bool] = Query(None),
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    return await OrderService.list_orders(session, tenant_id, channel=channel, status=status, is_paid=is_paid)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    order = await OrderService.get_order_dict(session, tenant_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Comanda / Pedido não encontrado")
    return order


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    data = payload.model_dump()
    if data.get("table_id"):
        data["table_id"] = str(data["table_id"])
    if data.get("items"):
        for it in data["items"]:
            if it.get("menu_item_id"):
                it["menu_item_id"] = str(it["menu_item_id"])
    res = await OrderService.create_order(session, tenant_id, data)
    await session.commit()
    return res


@router.post("/{order_id}/items", response_model=OrderResponse)
async def add_items_to_order(
    order_id: uuid.UUID,
    payload: OrderAddItems,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    items_data = []
    for it in payload.items:
        d = it.model_dump()
        if d.get("menu_item_id"):
            d["menu_item_id"] = str(d["menu_item_id"])
        items_data.append(d)

    try:
        res = await OrderService.add_items_to_order(session, tenant_id, order_id, items_data)
        await session.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{order_id}/close-and-pay", response_model=OrderResponse)
async def close_and_pay_order(
    order_id: uuid.UUID,
    payload: OrderCloseAndPay,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    try:
        res = await OrderService.close_and_pay_order(session, tenant_id, order_id, payload.model_dump())
        await session.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# ENDPOINTS: KDS (KITCHEN DISPLAY SYSTEM)
# ==========================================
@router.get("/kds/queue")
async def get_kds_queue(
    station: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    return await OrderService.get_kds_queue(session, tenant_id, station=station)


@router.patch("/items/{item_id}/kds-status")
async def update_kds_item_status(
    item_id: uuid.UUID,
    payload: KDSStatusUpdate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    try:
        res = await OrderService.update_order_item_kds_status(session, tenant_id, item_id, payload.status)
        await session.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# ENDPOINTS: DELIVERY HUB
# ==========================================
@router.get("/delivery/kanban")
async def get_delivery_kanban(
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    return await OrderService.list_delivery_orders(session, tenant_id)


@router.patch("/{order_id}/delivery-status", response_model=OrderResponse)
async def update_delivery_status(
    order_id: uuid.UUID,
    payload: DeliveryStatusUpdate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    order = await OrderService.update_delivery_status(session, tenant_id, order_id, payload.status)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido delivery não encontrado")
    await session.commit()
    return order
