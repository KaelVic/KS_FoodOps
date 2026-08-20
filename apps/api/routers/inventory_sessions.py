from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from modules.inventory.models import InventorySession, InventorySessionLocation, InventoryCountLine, InventoryCloseResult
from modules.inventory.service import InventoryService
from packages.security.dependencies import get_secure_session, get_tenant_id_from_header, require_permission, get_current_user
from packages.security.auth import TokenPayload

router = APIRouter(tags=["Inventory Sessions"], prefix="/inventory/sessions")

class CreateSessionPayload(BaseModel):
    location_id: UUID

class CountLinePayload(BaseModel):
    sku_id: UUID
    counted_quantity: Decimal

class CountLineResponse(BaseModel):
    id: UUID
    sku_id: UUID
    counted_quantity: Decimal
    model_config = ConfigDict(from_attributes=True)

class SessionResponse(BaseModel):
    id: UUID
    status: str
    cutoff_at: Optional[datetime]
    created_at: datetime
    closed_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class SessionDetailResponse(SessionResponse):
    lines: List[CountLineResponse]

class CloseResultResponse(BaseModel):
    sku_id: UUID
    expected_quantity: Decimal
    counted_quantity: Decimal
    variance_quantity: Decimal
    variance_value: Decimal
    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_session(
    payload: CreateSessionPayload,
    _perm: bool = Depends(require_permission("inventory.count")),
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    session = InventorySession(
        tenant_id=tenant_id,
        status="OPEN"
    )
    db.add(session)
    await db.flush()

    session_loc = InventorySessionLocation(
        tenant_id=tenant_id,
        session_id=session.id,
        location_id=payload.location_id
    )
    db.add(session_loc)
    await db.commit()
    return session

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    _perm: bool = Depends(require_permission("inventory.read")),
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = select(InventorySession).order_by(InventorySession.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    _perm: bool = Depends(require_permission("inventory.read")),
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = select(InventorySession).where(InventorySession.id == session_id)
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    stmt_lines = select(InventoryCountLine).where(InventoryCountLine.session_id == session_id)
    lines = (await db.execute(stmt_lines)).scalars().all()

    return SessionDetailResponse(
        id=session.id,
        status=session.status,
        cutoff_at=session.cutoff_at,
        created_at=session.created_at,
        closed_at=session.closed_at,
        lines=lines
    )

@router.post("/{session_id}/lines", response_model=CountLineResponse)
async def add_count_line(
    session_id: UUID,
    payload: CountLinePayload,
    _perm: bool = Depends(require_permission("inventory.count")),
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    # Retrieve location_id from session
    stmt = select(InventorySessionLocation).where(
        InventorySessionLocation.session_id == session_id,
        InventorySessionLocation.tenant_id == tenant_id
    )
    loc = (await db.execute(stmt)).scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=404, detail="Session location not found")

    line = InventoryCountLine(
        tenant_id=tenant_id,
        session_id=session_id,
        location_id=loc.location_id,
        sku_id=payload.sku_id,
        counted_quantity=payload.counted_quantity
    )
    db.add(line)
    await db.commit()
    return line

@router.post("/{session_id}/close", response_model=SessionResponse)
async def close_session(
    session_id: UUID,
    _perm: bool = Depends(require_permission("inventory.close")),
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
        session = await service.close_inventory_session(
            session_id=session_id,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id
        )
        await db.commit()
        return session
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/results", response_model=List[CloseResultResponse])
async def get_close_results(
    session_id: UUID,
    _perm: bool = Depends(require_permission("inventory.read")),
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = select(InventoryCloseResult).where(InventoryCloseResult.session_id == session_id)
    result = await db.execute(stmt)
    return result.scalars().all()
