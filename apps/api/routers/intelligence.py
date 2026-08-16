from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, desc

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from modules.intelligence.models import InventoryPolicy, PurchaseSuggestion, OperationalAlert
from modules.intelligence.service import IntelligenceService
from modules.catalog.models import SKU, UOM
from packages.tenant.models import Location
from modules.purchasing.models import PurchaseOrder, PurchaseOrderLine

router = APIRouter(tags=["Intelligence"])


# ==========================================
# Schemas
# ==========================================

class InventoryPolicyResponse(BaseModel):
    id: UUID
    location_id: UUID
    location_name: str
    sku_id: UUID
    sku_name: str
    base_uom: str
    min_stock: Decimal
    target_stock: Decimal
    lead_time_days: int
    abc_class: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class UpdatePolicyPayload(BaseModel):
    location_id: UUID
    sku_id: UUID
    min_stock: Decimal
    target_stock: Decimal
    lead_time_days: int


class PurchaseSuggestionResponse(BaseModel):
    id: UUID
    location_id: UUID
    sku_id: UUID
    sku_name: str
    base_uom: str
    suggested_quantity: Decimal
    status: str
    reason: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OperationalAlertResponse(BaseModel):
    id: UUID
    location_id: Optional[UUID]
    sku_id: UUID
    sku_name: str
    metric: str
    observed_value: Decimal
    reference_value: Decimal
    threshold: Decimal
    reason: str
    is_resolved: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConvertToPOPayload(BaseModel):
    supplier_id: UUID


class ConvertToPOResponse(BaseModel):
    purchase_order_id: UUID
    status: str


class CalculatePayload(BaseModel):
    location_id: UUID


# ==========================================
# Endpoints: ABC & Policies
# ==========================================

@router.post("/abc/calculate", status_code=status.HTTP_200_OK)
async def calculate_abc(
    payload: CalculatePayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = IntelligenceService(db)
    await service.calculate_abc_classification(tenant_id, payload.location_id)
    await db.commit()
    return {"message": "ABC classification calculated successfully"}


@router.get("/policies", response_model=List[InventoryPolicyResponse])
async def list_policies(
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    stmt = (
        select(
            InventoryPolicy.id,
            InventoryPolicy.location_id,
            Location.name.label("location_name"),
            InventoryPolicy.sku_id,
            SKU.name.label("sku_name"),
            UOM.symbol.label("base_uom"),
            InventoryPolicy.min_stock,
            InventoryPolicy.target_stock,
            InventoryPolicy.lead_time_days,
            InventoryPolicy.abc_class
        )
        .join(Location, InventoryPolicy.location_id == Location.id)
        .join(SKU, InventoryPolicy.sku_id == SKU.id)
        .join(UOM, SKU.base_uom_id == UOM.id)
        .where(InventoryPolicy.tenant_id == tenant_id)
        .order_by(InventoryPolicy.abc_class.asc(), SKU.name.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        InventoryPolicyResponse(
            id=r.id,
            location_id=r.location_id,
            location_name=r.location_name,
            sku_id=r.sku_id,
            sku_name=r.sku_name,
            base_uom=r.base_uom,
            min_stock=r.min_stock,
            target_stock=r.target_stock,
            lead_time_days=r.lead_time_days,
            abc_class=r.abc_class
        )
        for r in rows
    ]


@router.put("/policies", response_model=InventoryPolicyResponse)
async def update_policy(
    payload: UpdatePolicyPayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    stmt = select(InventoryPolicy).where(
        InventoryPolicy.tenant_id == tenant_id,
        InventoryPolicy.location_id == payload.location_id,
        InventoryPolicy.sku_id == payload.sku_id
    )
    policy = (await db.execute(stmt)).scalar_one_or_none()
    
    if policy:
        policy.min_stock = payload.min_stock
        policy.target_stock = payload.target_stock
        policy.lead_time_days = payload.lead_time_days
    else:
        policy = InventoryPolicy(
            tenant_id=tenant_id,
            location_id=payload.location_id,
            sku_id=payload.sku_id,
            min_stock=payload.min_stock,
            target_stock=payload.target_stock,
            lead_time_days=payload.lead_time_days
        )
        db.add(policy)
        
    await db.commit()
    await db.refresh(policy)
    
    # Refetch to get names
    refetch_stmt = (
        select(
            Location.name.label("location_name"),
            SKU.name.label("sku_name"),
            UOM.symbol.label("base_uom")
        )
        .select_from(SKU)
        .join(UOM, SKU.base_uom_id == UOM.id)
        .join(Location, Location.id == payload.location_id)
        .where(SKU.id == payload.sku_id)
    )
    names = (await db.execute(refetch_stmt)).first()
    
    return InventoryPolicyResponse(
        id=policy.id,
        location_id=policy.location_id,
        location_name=names.location_name if names else "",
        sku_id=policy.sku_id,
        sku_name=names.sku_name if names else "",
        base_uom=names.base_uom if names else "",
        min_stock=policy.min_stock,
        target_stock=policy.target_stock,
        lead_time_days=policy.lead_time_days,
        abc_class=policy.abc_class
    )


# ==========================================
# Endpoints: Purchase Suggestions
# ==========================================

@router.post("/suggestions/generate", status_code=status.HTTP_200_OK)
async def generate_suggestions(
    payload: CalculatePayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = IntelligenceService(db)
    await service.generate_purchase_suggestions(tenant_id, payload.location_id)
    await db.commit()
    return {"message": "Purchase suggestions generated successfully"}


@router.get("/suggestions", response_model=List[PurchaseSuggestionResponse])
async def list_suggestions(
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    stmt = (
        select(
            PurchaseSuggestion.id,
            PurchaseSuggestion.location_id,
            PurchaseSuggestion.sku_id,
            SKU.name.label("sku_name"),
            UOM.symbol.label("base_uom"),
            PurchaseSuggestion.suggested_quantity,
            PurchaseSuggestion.status,
            PurchaseSuggestion.reason,
            PurchaseSuggestion.created_at
        )
        .join(SKU, PurchaseSuggestion.sku_id == SKU.id)
        .join(UOM, SKU.base_uom_id == UOM.id)
        .where(PurchaseSuggestion.tenant_id == tenant_id)
        .where(PurchaseSuggestion.status == 'PENDING')
        .order_by(PurchaseSuggestion.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        PurchaseSuggestionResponse(
            id=r.id,
            location_id=r.location_id,
            sku_id=r.sku_id,
            sku_name=r.sku_name,
            base_uom=r.base_uom,
            suggested_quantity=r.suggested_quantity,
            status=r.status,
            reason=r.reason,
            created_at=r.created_at
        )
        for r in rows
    ]


@router.post("/suggestions/{suggestion_id}/convert-to-po", response_model=ConvertToPOResponse)
async def convert_suggestion_to_po(
    suggestion_id: UUID,
    payload: ConvertToPOPayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    """
    Takes a pending purchase suggestion and creates a DRAFT Purchase Order for it.
    """
    stmt = select(PurchaseSuggestion).where(
        PurchaseSuggestion.id == suggestion_id,
        PurchaseSuggestion.tenant_id == tenant_id,
        PurchaseSuggestion.status == 'PENDING'
    )
    suggestion = (await db.execute(stmt)).scalar_one_or_none()
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found or already processed")
        
    # Create Purchase Order
    po = PurchaseOrder(
        tenant_id=tenant_id,
        supplier_id=payload.supplier_id,
        location_id=suggestion.location_id,
        status="DRAFT"
    )
    db.add(po)
    await db.flush()
    
    # Note: A real implementation would lookup supplier SKU pricing and mapping.
    # We will insert a generic PO line with zero price for now, to be filled by user.
    po_line = PurchaseOrderLine(
        tenant_id=tenant_id,
        purchase_order_id=po.id,
        sku_id=suggestion.sku_id,
        ordered_quantity=suggestion.suggested_quantity,
        unit_price=Decimal("0.00")
    )
    db.add(po_line)
    
    suggestion.status = 'ACCEPTED'
    await db.commit()
    
    return ConvertToPOResponse(purchase_order_id=po.id, status=po.status)


# ==========================================
# Endpoints: Operational Alerts
# ==========================================

@router.post("/alerts/generate", status_code=status.HTTP_200_OK)
async def generate_alerts(
    payload: CalculatePayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = IntelligenceService(db)
    await service.generate_operational_alerts(tenant_id, payload.location_id)
    await db.commit()
    return {"message": "Operational alerts generated successfully"}


@router.get("/alerts", response_model=List[OperationalAlertResponse])
async def list_alerts(
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    stmt = (
        select(
            OperationalAlert.id,
            OperationalAlert.location_id,
            OperationalAlert.sku_id,
            SKU.name.label("sku_name"),
            OperationalAlert.metric,
            OperationalAlert.observed_value,
            OperationalAlert.reference_value,
            OperationalAlert.threshold,
            OperationalAlert.reason,
            OperationalAlert.is_resolved,
            OperationalAlert.created_at
        )
        .join(SKU, OperationalAlert.sku_id == SKU.id)
        .where(OperationalAlert.tenant_id == tenant_id)
        .where(OperationalAlert.is_resolved == False)
        .order_by(OperationalAlert.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        OperationalAlertResponse(
            id=r.id,
            location_id=r.location_id,
            sku_id=r.sku_id,
            sku_name=r.sku_name,
            metric=r.metric,
            observed_value=r.observed_value,
            reference_value=r.reference_value,
            threshold=r.threshold,
            reason=r.reason,
            is_resolved=r.is_resolved,
            created_at=r.created_at
        )
        for r in rows
    ]


@router.post("/alerts/{alert_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    stmt = update(OperationalAlert).where(
        OperationalAlert.id == alert_id,
        OperationalAlert.tenant_id == tenant_id
    ).values(is_resolved=True)
    
    await db.execute(stmt)
    await db.commit()
    return {"message": "Alert resolved"}
