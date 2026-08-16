from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from modules.sales.models import SalesImport, Sale, SaleLine, POSProductMapping
from modules.sales.service import SalesService
from modules.recipes.models import Recipe
from modules.inventory.models import TheoreticalConsumption, StockLedgerEntry, StockMovement, LossRecord
from modules.catalog.models import SKU, UOM

router = APIRouter(tags=["Sales"])


# Schemas
class SaleLineInput(BaseModel):
    pos_product_id: str
    quantity: Decimal
    unit_price: Decimal


class SaleInput(BaseModel):
    pos_sale_id: str
    sale_date: datetime
    total_amount: Decimal
    lines: List[SaleLineInput]


class SalesImportPayload(BaseModel):
    pos_system: str = "POS_GENERIC"
    import_reference: str
    sales: List[SaleInput]


class SalesImportResponse(BaseModel):
    id: UUID
    pos_system: str
    import_reference: str
    status: str
    created_at: datetime
    sales_count: int
    model_config = ConfigDict(from_attributes=True)


class POSMappingPayload(BaseModel):
    pos_product_id: str
    pos_product_name: str
    recipe_id: Optional[UUID] = None


class POSMappingResponse(BaseModel):
    id: UUID
    pos_product_id: str
    pos_product_name: str
    recipe_id: Optional[UUID]
    recipe_name: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TheoreticalConsumptionItem(BaseModel):
    sku_id: UUID
    sku_name: str
    uom_symbol: str
    theoretical_quantity: Decimal
    theoretical_cost: Decimal
    registered_losses_quantity: Decimal
    total_expected_depletion: Decimal


@router.post("/import", response_model=SalesImportResponse, status_code=status.HTTP_201_CREATED)
async def import_sales_endpoint(
    payload: SalesImportPayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = SalesService(db)
    
    sales_data = [
        {
            "pos_sale_id": s.pos_sale_id,
            "sale_date": s.sale_date,
            "total_amount": str(s.total_amount),
            "lines": [
                {
                    "pos_product_id": l.pos_product_id,
                    "quantity": str(l.quantity),
                    "unit_price": str(l.unit_price)
                }
                for l in s.lines
            ]
        }
        for s in payload.sales
    ]

    try:
        sales_import = await service.import_sales(
            tenant_id=tenant_id,
            pos_system=payload.pos_system,
            import_reference=payload.import_reference,
            sales_data=sales_data
        )
        await db.flush()

        # Process theoretical consumption
        await service.process_theoretical_consumption(sales_import.id, tenant_id)
        await db.commit()

        return SalesImportResponse(
            id=sales_import.id,
            pos_system=sales_import.pos_system,
            import_reference=sales_import.import_reference,
            status=sales_import.status,
            created_at=sales_import.created_at,
            sales_count=len(payload.sales)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/imports", response_model=List[SalesImportResponse])
async def list_sales_imports(
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = select(SalesImport).order_by(SalesImport.created_at.desc())
    result = await db.execute(stmt)
    imports = result.scalars().all()

    response = []
    for imp in imports:
        count_stmt = select(func.count(Sale.id)).where(Sale.sales_import_id == imp.id)
        count = (await db.execute(count_stmt)).scalar() or 0
        response.append(SalesImportResponse(
            id=imp.id,
            pos_system=imp.pos_system,
            import_reference=imp.import_reference,
            status=imp.status,
            created_at=imp.created_at,
            sales_count=count
        ))
    return response


@router.get("/mappings", response_model=List[POSMappingResponse])
async def list_pos_mappings(
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = (
        select(
            POSProductMapping.id,
            POSProductMapping.pos_product_id,
            POSProductMapping.pos_product_name,
            POSProductMapping.recipe_id,
            POSProductMapping.created_at,
            Recipe.name.label("recipe_name")
        )
        .outerjoin(Recipe, POSProductMapping.recipe_id == Recipe.id)
        .order_by(POSProductMapping.pos_product_name.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        POSMappingResponse(
            id=r.id,
            pos_product_id=r.pos_product_id,
            pos_product_name=r.pos_product_name,
            recipe_id=r.recipe_id,
            recipe_name=r.recipe_name,
            created_at=r.created_at
        )
        for r in rows
    ]


@router.post("/mappings", response_model=POSMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_pos_mapping(
    payload: POSMappingPayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    stmt = select(POSProductMapping).where(
        POSProductMapping.pos_product_id == payload.pos_product_id,
        POSProductMapping.tenant_id == tenant_id
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing:
        existing.pos_product_name = payload.pos_product_name
        existing.recipe_id = payload.recipe_id
        mapping = existing
    else:
        mapping = POSProductMapping(
            tenant_id=tenant_id,
            pos_product_id=payload.pos_product_id,
            pos_product_name=payload.pos_product_name,
            recipe_id=payload.recipe_id
        )
        db.add(mapping)

    await db.commit()

    recipe_name = None
    if mapping.recipe_id:
        r_stmt = select(Recipe.name).where(Recipe.id == mapping.recipe_id)
        recipe_name = (await db.execute(r_stmt)).scalar_one_or_none()

    return POSMappingResponse(
        id=mapping.id,
        pos_product_id=mapping.pos_product_id,
        pos_product_name=mapping.pos_product_name,
        recipe_id=mapping.recipe_id,
        recipe_name=recipe_name,
        created_at=mapping.created_at
    )


@router.get("/theoretical-vs-actual", response_model=List[TheoreticalConsumptionItem])
async def get_theoretical_vs_actual(
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    """
    Computes theoretical consumption vs losses per SKU.
    """
    # 1. Theoretical consumption aggregated by SKU
    tc_stmt = (
        select(
            TheoreticalConsumption.sku_id,
            SKU.name.label("sku_name"),
            UOM.symbol.label("uom_symbol"),
            func.coalesce(func.sum(TheoreticalConsumption.quantity), 0).label("theoretical_qty"),
            func.coalesce(func.sum(TheoreticalConsumption.quantity * TheoreticalConsumption.unit_cost_at_time), 0).label("theoretical_cost")
        )
        .join(SKU, TheoreticalConsumption.sku_id == SKU.id)
        .join(UOM, SKU.base_uom_id == UOM.id)
        .group_by(TheoreticalConsumption.sku_id, SKU.name, UOM.symbol)
    )
    tc_rows = (await db.execute(tc_stmt)).all()

    # 2. Losses aggregated by SKU
    losses_stmt = (
        select(
            StockLedgerEntry.sku_id,
            func.coalesce(func.sum(func.abs(StockLedgerEntry.quantity)), 0).label("losses_qty")
        )
        .join(StockMovement, StockLedgerEntry.movement_id == StockMovement.id)
        .where(StockMovement.type == 'LOSS')
        .group_by(StockLedgerEntry.sku_id)
    )
    losses_dict = {
        row.sku_id: Decimal(str(row.losses_qty))
        for row in (await db.execute(losses_stmt)).all()
    }

    result = []
    for r in tc_rows:
        theo_qty = Decimal(str(r.theoretical_qty))
        theo_cost = Decimal(str(r.theoretical_cost))
        loss_qty = losses_dict.get(r.sku_id, Decimal("0"))
        
        result.append(TheoreticalConsumptionItem(
            sku_id=r.sku_id,
            sku_name=r.sku_name,
            uom_symbol=r.uom_symbol,
            theoretical_quantity=theo_qty,
            theoretical_cost=theo_cost,
            registered_losses_quantity=loss_qty,
            total_expected_depletion=theo_qty + loss_qty
        ))

    return result
