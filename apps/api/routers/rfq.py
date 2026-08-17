from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from modules.purchasing.models import RFQ, RFQItem, RFQSupplier, RFQProposal
from modules.purchasing.rfq_service import RFQService
from modules.catalog.models import SKU, UOM
from modules.suppliers.models import Supplier

router = APIRouter(tags=["RFQs & Cotações B2B"], prefix="/purchasing/rfqs")


class CreateRFQItemPayload(BaseModel):
    sku_id: UUID
    quantity: Decimal
    target_price: Optional[Decimal] = None


class CreateRFQPayload(BaseModel):
    title: str
    location_id: Optional[UUID] = None
    deadline: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[CreateRFQItemPayload]
    supplier_ids: Optional[List[UUID]] = None


class AddSuppliersPayload(BaseModel):
    supplier_ids: List[UUID]


class ProposalItemPayload(BaseModel):
    rfq_item_id: UUID
    unit_price: Decimal
    available_quantity: Optional[Decimal] = None
    brand_or_spec: Optional[str] = None


class SubmitProposalPayload(BaseModel):
    supplier_id: UUID
    freight_cost: Decimal = Decimal("0")
    delivery_days: str = "0"
    payment_terms: Optional[str] = None
    min_order_value: Decimal = Decimal("0")
    notes: Optional[str] = None
    item_prices: List[ProposalItemPayload]


class AwardRFQPayload(BaseModel):
    award_type: str = "SPLIT"  # "SPLIT" or "SINGLE_SUPPLIER"
    selected_supplier_id: Optional[UUID] = None


# Responses
class RFQItemResponse(BaseModel):
    id: UUID
    sku_id: UUID
    sku_name: Optional[str] = None
    uom_symbol: Optional[str] = None
    quantity: Decimal
    target_price: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)


class RFQSupplierResponse(BaseModel):
    id: UUID
    supplier_id: UUID
    supplier_name: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class RFQResponse(BaseModel):
    id: UUID
    rfq_number: str
    title: str
    location_id: Optional[UUID]
    status: str
    deadline: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RFQDetailResponse(RFQResponse):
    items: List[RFQItemResponse]
    suppliers: List[RFQSupplierResponse]


@router.post("", response_model=RFQResponse, status_code=status.HTTP_201_CREATED)
async def create_rfq(
    payload: CreateRFQPayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = RFQService(db)
    items_data = [item.model_dump() for item in payload.items]
    try:
        rfq = await service.create_rfq(
            tenant_id=tenant_id,
            title=payload.title,
            location_id=payload.location_id,
            deadline=payload.deadline,
            notes=payload.notes,
            items=items_data,
            supplier_ids=payload.supplier_ids
        )
        return rfq
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[RFQResponse])
async def list_rfqs(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = select(RFQ).order_by(RFQ.created_at.desc())
    if status_filter:
        stmt = stmt.where(RFQ.status == status_filter)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{rfq_id}", response_model=RFQDetailResponse)
async def get_rfq_details(
    rfq_id: UUID,
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = select(RFQ).where(RFQ.id == rfq_id)
    rfq = (await db.execute(stmt)).scalar_one_or_none()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ não encontrada")

    # Load items with SKU & UOM
    items_stmt = (
        select(RFQItem, SKU.name.label("sku_name"), UOM.symbol.label("uom_symbol"))
        .join(SKU, RFQItem.sku_id == SKU.id)
        .join(UOM, SKU.base_uom_id == UOM.id)
        .where(RFQItem.rfq_id == rfq_id)
    )
    items_rows = (await db.execute(items_stmt)).all()
    items_data = [
        RFQItemResponse(
            id=row[0].id,
            sku_id=row[0].sku_id,
            sku_name=row.sku_name,
            uom_symbol=row.uom_symbol,
            quantity=row[0].quantity,
            target_price=row[0].target_price
        )
        for row in items_rows
    ]

    # Load suppliers
    supp_stmt = (
        select(RFQSupplier, Supplier.name.label("supplier_name"))
        .join(Supplier, RFQSupplier.supplier_id == Supplier.id)
        .where(RFQSupplier.rfq_id == rfq_id)
    )
    supp_rows = (await db.execute(supp_stmt)).all()
    supp_data = [
        RFQSupplierResponse(
            id=row[0].id,
            supplier_id=row[0].supplier_id,
            supplier_name=row.supplier_name,
            status=row[0].status
        )
        for row in supp_rows
    ]

    return RFQDetailResponse(
        id=rfq.id,
        rfq_number=rfq.rfq_number,
        title=rfq.title,
        location_id=rfq.location_id,
        status=rfq.status,
        deadline=rfq.deadline,
        notes=rfq.notes,
        created_at=rfq.created_at,
        updated_at=rfq.updated_at,
        items=items_data,
        suppliers=supp_data
    )


@router.post("/{rfq_id}/suppliers", response_model=List[RFQSupplierResponse])
async def add_rfq_suppliers(
    rfq_id: UUID,
    payload: AddSuppliersPayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = RFQService(db)
    try:
        added = await service.add_suppliers(tenant_id, rfq_id, payload.supplier_ids)
        return [RFQSupplierResponse.model_validate(s) for s in added]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rfq_id}/proposals")
async def submit_proposal(
    rfq_id: UUID,
    payload: SubmitProposalPayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = RFQService(db)
    item_prices = [item.model_dump() for item in payload.item_prices]
    try:
        proposal = await service.submit_proposal(
            tenant_id=tenant_id,
            rfq_id=rfq_id,
            supplier_id=payload.supplier_id,
            freight_cost=payload.freight_cost,
            delivery_days=payload.delivery_days,
            payment_terms=payload.payment_terms,
            min_order_value=payload.min_order_value,
            notes=payload.notes,
            item_prices=item_prices
        )
        return {"proposal_id": proposal.id, "status": "SUBMITTED"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rfq_id}/comparison")
async def get_rfq_comparison(
    rfq_id: UUID,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = RFQService(db)
    try:
        matrix = await service.get_comparison_matrix(tenant_id, rfq_id)
        return matrix
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rfq_id}/award")
async def award_rfq(
    rfq_id: UUID,
    payload: AwardRFQPayload,
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = RFQService(db)
    try:
        po_ids = await service.award_rfq(
            tenant_id=tenant_id,
            rfq_id=rfq_id,
            award_type=payload.award_type,
            selected_supplier_id=payload.selected_supplier_id
        )
        return {
            "status": "AWARDED",
            "purchase_order_ids": po_ids,
            "message": f"{len(po_ids)} Pedido(s) de Compra gerado(s) com sucesso."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
