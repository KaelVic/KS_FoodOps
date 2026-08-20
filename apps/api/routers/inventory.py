from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.inventory.models import StockBalanceProjection
from modules.catalog.models import SKU, Category, UOM
from packages.tenant.models import Location
from packages.security.dependencies import get_secure_session, require_permission

router = APIRouter(tags=["Inventory"])


class StockBalanceResponse(BaseModel):
    sku_id: UUID
    sku_name: str
    category_name: Optional[str]
    base_uom: str
    quantity: Decimal
    total_value: Decimal
    unit_cost: Decimal
    location_name: str

    model_config = ConfigDict(from_attributes=True)


@router.get("/balances", response_model=List[StockBalanceResponse])
async def list_stock_balances(
    location_id: Optional[UUID] = Query(None, description="Filter by specific location"),
    _perm: bool = Depends(require_permission("inventory.read")),
    db: AsyncSession = Depends(get_secure_session)
) -> List[StockBalanceResponse]:
    """
    List stock balances with optional location filter.
    Returns stock balances joined with SKU, Category, UOM, and Location.
    """
    stmt = (
        select(
            StockBalanceProjection.sku_id,
            SKU.name.label("sku_name"),
            Category.name.label("category_name"),
            UOM.symbol.label("base_uom"),
            StockBalanceProjection.quantity,
            StockBalanceProjection.total_value,
            Location.name.label("location_name"),
        )
        .join(SKU, StockBalanceProjection.sku_id == SKU.id)
        .join(UOM, SKU.base_uom_id == UOM.id)
        .join(Location, StockBalanceProjection.location_id == Location.id)
        .outerjoin(Category, SKU.category_id == Category.id)
    )

    if location_id:
        stmt = stmt.where(StockBalanceProjection.location_id == location_id)

    result = await db.execute(stmt)
    rows = result.all()

    response = []
    for row in rows:
        quantity = Decimal(str(row.quantity)) if row.quantity is not None else Decimal("0")
        total_value = Decimal(str(row.total_value)) if row.total_value is not None else Decimal("0")
        unit_cost = (total_value / quantity) if quantity > 0 else Decimal("0")

        response.append(StockBalanceResponse(
            sku_id=row.sku_id,
            sku_name=row.sku_name,
            category_name=row.category_name,
            base_uom=row.base_uom,
            quantity=quantity,
            total_value=total_value,
            unit_cost=unit_cost,
            location_name=row.location_name
        ))

    return response


from datetime import datetime
from fastapi import HTTPException, status
from modules.inventory.models import LossRecord, StockMovement
from modules.inventory.service import InventoryService
from packages.security.dependencies import get_tenant_id_from_header, get_current_user
from packages.security.auth import TokenPayload


class RegisterLossPayload(BaseModel):
    location_id: UUID
    sku_id: UUID
    quantity: Decimal
    reason: str
    actor: Optional[str] = "Kitchen Operator"


class LossResponse(BaseModel):
    id: UUID
    movement_id: UUID
    sku_id: Optional[UUID] = None
    sku_name: Optional[str] = None
    quantity: Optional[Decimal] = None
    reason: str
    actor: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReverseMovementPayload(BaseModel):
    reason: str = Field(..., example="Input error / Duplicate entry")


class MovementResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    location_id: UUID
    type: str
    status: str
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    actor_user_id: Optional[UUID] = None
    reason_code: Optional[str] = None
    notes: Optional[str] = None
    posted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


@router.post("/losses", response_model=LossResponse, status_code=status.HTTP_201_CREATED)
async def register_loss_endpoint(
    payload: RegisterLossPayload,
    _perm: bool = Depends(require_permission("inventory.adjust")),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = InventoryService(db)
    actor_user_id = None
    try:
        actor_user_id = UUID(user.sub)
    except Exception:
        pass

    try:
        loss = await service.register_loss(
            location_id=payload.location_id,
            sku_id=payload.sku_id,
            quantity=payload.quantity,
            reason=payload.reason,
            actor=payload.actor or "Operator",
            tenant_id=tenant_id,
            actor_user_id=actor_user_id
        )
        await db.commit()

        # Get sku name
        sku_stmt = select(SKU.name).where(SKU.id == payload.sku_id)
        sku_name = (await db.execute(sku_stmt)).scalar_one_or_none()

        return LossResponse(
            id=loss.id,
            movement_id=loss.movement_id,
            sku_id=payload.sku_id,
            sku_name=sku_name,
            quantity=payload.quantity,
            reason=loss.reason,
            actor=loss.actor,
            created_at=loss.created_at
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/movements/{movement_id}/reverse", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
async def reverse_movement_endpoint(
    movement_id: UUID,
    payload: ReverseMovementPayload,
    _perm: bool = Depends(require_permission("inventory.adjust")),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    """
    Reverses an existing POSTED stock movement immutably.
    Creates a counter-movement of type REVERSAL with inverse ledger entries.
    """
    service = InventoryService(db)
    actor_user_id = None
    try:
        actor_user_id = UUID(user.sub)
    except Exception:
        pass

    try:
        reversal = await service.reverse_movement(
            movement_id=movement_id,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            reason=payload.reason
        )
        await db.commit()
        return reversal
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/losses", response_model=List[LossResponse])
async def list_losses_endpoint(
    _perm: bool = Depends(require_permission("inventory.read")),
    db: AsyncSession = Depends(get_secure_session)
):
    from modules.inventory.models import StockLedgerEntry
    stmt = (
        select(
            LossRecord.id,
            LossRecord.movement_id,
            LossRecord.reason,
            LossRecord.actor,
            LossRecord.created_at,
            StockLedgerEntry.sku_id,
            StockLedgerEntry.quantity,
            SKU.name.label("sku_name")
        )
        .join(StockMovement, LossRecord.movement_id == StockMovement.id)
        .join(StockLedgerEntry, StockMovement.id == StockLedgerEntry.movement_id)
        .join(SKU, StockLedgerEntry.sku_id == SKU.id)
        .order_by(LossRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        LossResponse(
            id=r.id,
            movement_id=r.movement_id,
            sku_id=r.sku_id,
            sku_name=r.sku_name,
            quantity=abs(Decimal(str(r.quantity))),
            reason=r.reason,
            actor=r.actor,
            created_at=r.created_at
        )
        for r in rows
    ]


# --- STOCK TRANSFERS ---

class TransferItemPayload(BaseModel):
    sku_id: UUID
    quantity_sent: Decimal = Field(..., gt=0)

class CreateStockTransferPayload(BaseModel):
    origin_location_id: UUID
    destination_location_id: UUID
    items: List[TransferItemPayload]
    notes: Optional[str] = None

class ReceiveTransferItemPayload(BaseModel):
    item_id: Optional[UUID] = None
    sku_id: Optional[UUID] = None
    quantity_received: Decimal = Field(..., gt=0)

class ReceiveStockTransferPayload(BaseModel):
    items: Optional[List[ReceiveTransferItemPayload]] = None


@router.get("/transfers")
async def list_stock_transfers(
    status: Optional[str] = Query(None),
    _perm: bool = Depends(require_permission("inventory.read")),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    service = InventoryService(session)
    return await service.list_transfers(tenant_id=tenant_id, status=status)


@router.post("/transfers", status_code=status.HTTP_201_CREATED)
async def create_stock_transfer(
    payload: CreateStockTransferPayload,
    _perm: bool = Depends(require_permission("inventory.adjust")),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    service = InventoryService(session)
    try:
        transfer = await service.create_transfer(
            tenant_id=tenant_id,
            origin_location_id=payload.origin_location_id,
            destination_location_id=payload.destination_location_id,
            items=[{"sku_id": i.sku_id, "quantity_sent": i.quantity_sent} for i in payload.items],
            notes=payload.notes,
        )
        res = await service.get_transfer_dict(tenant_id=tenant_id, transfer_id=transfer.id)
        await session.commit()
        return res
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transfers/{transfer_id}")
async def get_stock_transfer_detail(
    transfer_id: UUID,
    _perm: bool = Depends(require_permission("inventory.read")),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    service = InventoryService(session)
    transfer = await service.get_transfer_dict(tenant_id=tenant_id, transfer_id=transfer_id)
    if not transfer:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")
    return transfer


@router.post("/transfers/{transfer_id}/dispatch")
async def dispatch_stock_transfer(
    transfer_id: UUID,
    _perm: bool = Depends(require_permission("inventory.adjust")),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    service = InventoryService(session)
    try:
        await service.dispatch_transfer(tenant_id=tenant_id, transfer_id=transfer_id)
        res = await service.get_transfer_dict(tenant_id=tenant_id, transfer_id=transfer_id)
        await session.commit()
        return res
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))


class TheoreticalBalanceResponse(BaseModel):
    sku_id: str
    sku_name: str
    category_name: str
    uom_symbol: str
    actual_quantity: float
    theoretical_quantity: float
    theoretical_consumption: float
    variance_quantity: float
    unit_cost: float
    variance_value: float
    status: str


@router.get("/theoretical-balances", response_model=List[TheoreticalBalanceResponse])
async def list_theoretical_balances(
    location_id: Optional[UUID] = Query(None, description="Filter by specific location"),
    _perm: bool = Depends(require_permission("inventory.read")),
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    """
    Computes perpetual theoretical stock vs real ledger stock and operational variances for all SKUs.
    """
    service = InventoryService(session)
    return await service.calculate_theoretical_stock_by_sku(tenant_id=tenant_id, location_id=location_id)


@router.post("/transfers/{transfer_id}/receive")
async def receive_stock_transfer(
    transfer_id: UUID,
    payload: Optional[ReceiveStockTransferPayload] = None,
    _perm: bool = Depends(require_permission("inventory.adjust")),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    session: AsyncSession = Depends(get_secure_session),
):
    service = InventoryService(session)
    try:
        items_rec = None
        if payload and payload.items:
            items_rec = [
                {
                    "item_id": i.item_id,
                    "sku_id": i.sku_id,
                    "quantity_received": i.quantity_received,
                }
                for i in payload.items
            ]
        await service.receive_transfer(
            tenant_id=tenant_id,
            transfer_id=transfer_id,
            items_received=items_rec,
        )
        res = await service.get_transfer_dict(tenant_id=tenant_id, transfer_id=transfer_id)
        await session.commit()
        return res
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))