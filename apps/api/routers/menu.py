import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from modules.menu.service import MenuService

router = APIRouter(prefix="/menu", tags=["Menu & Engineering"])



# --- Schemas ---

class MenuCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(0)
    is_active: bool = Field(True)

class MenuCategoryResponse(BaseModel):
    id: str
    name: str
    display_order: int
    is_active: bool
    created_at: Optional[str] = None


class MenuItemCreate(BaseModel):
    category_id: Optional[str] = None
    recipe_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    pos_code: Optional[str] = None
    description: Optional[str] = None
    sale_price: Decimal = Field(Decimal("0"))
    cost_price: Decimal = Field(Decimal("0"))
    target_cmv_percentage: Decimal = Field(Decimal("30.00"))
    is_active: bool = Field(True)
    display_order: int = Field(0)

class MenuItemUpdate(BaseModel):
    category_id: Optional[str] = None
    recipe_id: Optional[str] = None
    name: Optional[str] = None
    pos_code: Optional[str] = None
    description: Optional[str] = None
    sale_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    target_cmv_percentage: Optional[Decimal] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

class MenuItemResponse(BaseModel):
    id: str
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    recipe_id: Optional[str] = None
    recipe_name: Optional[str] = None
    name: str
    pos_code: Optional[str] = None
    description: Optional[str] = None
    sale_price: float
    cost_price: float
    unit_margin: float
    margin_pct: float
    cmv_pct: float
    target_cmv_percentage: float
    suggested_price: float
    is_active: bool
    display_order: int
    created_at: Optional[str] = None


class SimulatePricingPayload(BaseModel):
    target_cmv_pct: Optional[Decimal] = None
    new_price: Optional[Decimal] = None

class SimulatePricingResponse(BaseModel):
    item_id: str
    item_name: str
    cost_price: float
    current_price: float
    current_margin: float
    current_cmv_pct: float
    proposed_price: float
    proposed_margin: float
    proposed_margin_pct: float
    resulting_cmv_pct: float
    margin_delta: float
    price_delta: float


# --- Category Endpoints ---

@router.get("/categories", response_model=List[MenuCategoryResponse])
async def list_menu_categories(
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    """List all menu categories for the current restaurant."""
    return await MenuService.list_categories(session, tenant_id)


@router.post("/categories", response_model=MenuCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_category(
    payload: MenuCategoryCreate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    """Create a new menu category."""
    res = await MenuService.create_category(session, tenant_id, payload.model_dump())
    await session.commit()
    return res


# --- Menu Item Endpoints ---

@router.get("/items", response_model=List[MenuItemResponse])
async def list_menu_items(
    category_id: Optional[uuid.UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    """List menu items with dynamic recipe cost and margins."""
    return await MenuService.list_menu_items(session, tenant_id, category_id, is_active)


@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    payload: MenuItemCreate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    """Create a new menu item linked to a recipe or manual cost."""
    res = await MenuService.create_menu_item(session, tenant_id, payload.model_dump())
    await session.commit()
    return res


@router.put("/items/{item_id}")
async def update_menu_item(
    item_id: uuid.UUID,
    payload: MenuItemUpdate,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    """Update menu item details or price."""
    try:
        res = await MenuService.update_menu_item(
            session, tenant_id, item_id, payload.model_dump(exclude_unset=True)
        )
        await session.commit()
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/items/{item_id}")
async def delete_menu_item(
    item_id: uuid.UUID,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    """Delete a menu item."""
    success = await MenuService.delete_menu_item(session, tenant_id, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item de cardápio não encontrado.")
    await session.commit()
    return {"message": "Item removido com sucesso."}


# --- Menu Engineering & Pricing Simulation ---

@router.get("/engineering")
async def get_menu_engineering(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    """
    Computes Menu Engineering Matrix (BCG / Kasavana & Smith):
    Classifies all dishes into Stars, Plowhorses, Puzzles, Dogs based on Popularity vs Contribution Margin.
    """
    return await MenuService.calculate_menu_engineering(
        session, tenant_id, start_date, end_date, category_id
    )


@router.post("/items/{item_id}/simulate-pricing", response_model=SimulatePricingResponse)
async def simulate_item_pricing(
    item_id: uuid.UUID,
    payload: SimulatePricingPayload,
    session: AsyncSession = Depends(get_secure_session),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header)
):
    """
    Simulates new selling price and recalculates CMV % and unit contribution margin.
    """
    try:
        return await MenuService.simulate_pricing(
            session, tenant_id, item_id, payload.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

