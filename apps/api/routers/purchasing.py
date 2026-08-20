from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header, require_permission, get_current_user
from packages.security.auth import TokenPayload
from packages.audit.service import AuditService
from modules.purchasing.models import (
    PurchaseOrder, PurchaseOrderLine, GoodsReceipt, GoodsReceiptLine,
    SupplierInvoice, SupplierInvoiceLine, PurchaseReconciliation
)
from modules.catalog.models import SKU, UOM
from modules.purchasing.service import PurchasingService

router = APIRouter(tags=["Purchasing"], prefix="/purchasing/orders")

class POLinePayload(BaseModel):
    sku_id: UUID
    ordered_quantity: Decimal
    unit_price: Decimal

class CreatePOPayload(BaseModel):
    supplier_id: UUID
    location_id: UUID
    expected_delivery_date: Optional[datetime] = None
    lines: List[POLinePayload]

class ReceivePOLinePayload(BaseModel):
    po_line_id: UUID
    sku_id: UUID
    quantity: Decimal
    unit_price: Decimal

class ReceivePOPayload(BaseModel):
    lines: List[ReceivePOLinePayload]

class InvoiceLinePayload(BaseModel):
    po_line_id: UUID
    sku_id: UUID
    invoiced_quantity: Decimal
    unit_price: Decimal

class InvoicePOPayload(BaseModel):
    invoice_number: str
    issue_date: datetime
    lines: List[InvoiceLinePayload]

class POResponse(BaseModel):
    id: UUID
    supplier_id: UUID
    location_id: UUID
    status: str
    order_date: Optional[datetime]
    expected_delivery_date: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class POLineResponse(BaseModel):
    id: UUID
    sku_id: UUID
    ordered_quantity: Decimal
    unit_price: Decimal
    model_config = ConfigDict(from_attributes=True)

class PODetailResponse(POResponse):
    lines: List[POLineResponse]

class ReconResponse(BaseModel):
    id: UUID
    po_line_id: UUID
    receipt_line_id: Optional[UUID]
    invoice_line_id: Optional[UUID]
    quantity_variance: Optional[Decimal]
    price_variance: Optional[Decimal]
    status: str
    model_config = ConfigDict(from_attributes=True)

class EnrichedReconResponse(BaseModel):
    id: UUID
    po_line_id: UUID
    sku_id: UUID
    sku_name: str
    uom_symbol: str
    
    # PO
    ordered_qty: Decimal
    ordered_price: Decimal
    
    # Receipt
    received_qty: Optional[Decimal]
    received_price: Optional[Decimal]
    
    # Invoice
    invoiced_qty: Optional[Decimal]
    invoiced_price: Optional[Decimal]
    
    status: str
    model_config = ConfigDict(from_attributes=True)

@router.post("", response_model=POResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    payload: CreatePOPayload,
    _perm: bool = Depends(require_permission("purchasing.create")),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    actor_user_id = None
    try:
        actor_user_id = UUID(user.sub)
    except Exception:
        pass

    try:
        po = PurchaseOrder(
            tenant_id=tenant_id,
            supplier_id=payload.supplier_id,
            location_id=payload.location_id,
            status="DRAFT",
            expected_delivery_date=payload.expected_delivery_date
        )
        db.add(po)
        await db.flush()

        for line in payload.lines:
            po_line = PurchaseOrderLine(
                tenant_id=tenant_id,
                purchase_order_id=po.id,
                sku_id=line.sku_id,
                ordered_quantity=line.ordered_quantity,
                unit_price=line.unit_price
            )
            db.add(po_line)
        
        await AuditService.log_action(
            db=db,
            tenant_id=tenant_id,
            actor_id=actor_user_id or po.id,
            action="PURCHASE_ORDER_CREATED",
            resource_type="purchase_orders",
            resource_id=po.id,
            changes_payload={
                "supplier_id": str(payload.supplier_id),
                "location_id": str(payload.location_id),
                "lines_count": len(payload.lines)
            }
        )

        await db.commit()
        return po
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[POResponse])
async def list_purchase_orders(
    _perm: bool = Depends(require_permission("purchasing.read")),
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{po_id}", response_model=PODetailResponse)
async def get_purchase_order(
    po_id: UUID,
    _perm: bool = Depends(require_permission("purchasing.read")),
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id)
    po = (await db.execute(stmt)).scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
        
    stmt_lines = select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == po_id)
    lines = (await db.execute(stmt_lines)).scalars().all()
    
    return PODetailResponse(
        id=po.id,
        supplier_id=po.supplier_id,
        location_id=po.location_id,
        status=po.status,
        order_date=po.order_date,
        expected_delivery_date=po.expected_delivery_date,
        created_at=po.created_at,
        lines=lines
    )

@router.post("/{po_id}/approve", response_model=POResponse)
async def approve_purchase_order(
    po_id: UUID,
    _perm: bool = Depends(require_permission("purchasing.approve")),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    actor_user_id = None
    try:
        actor_user_id = UUID(user.sub)
    except Exception:
        pass

    stmt = select(PurchaseOrder).where(
        PurchaseOrder.id == po_id,
        PurchaseOrder.tenant_id == tenant_id
    ).with_for_update()
    po = (await db.execute(stmt)).scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    if po.status not in ["DRAFT", "PENDING"]:
        raise HTTPException(status_code=400, detail=f"Cannot approve PO with status '{po.status}'")
    
    po.status = "APPROVED"

    await AuditService.log_action(
        db=db,
        tenant_id=tenant_id,
        actor_id=actor_user_id or po.id,
        action="PURCHASE_ORDER_APPROVED",
        resource_type="purchase_orders",
        resource_id=po.id,
        changes_payload={"new_status": "APPROVED"}
    )

    await db.commit()
    return po

@router.post("/{po_id}/receive")
async def receive_purchase_order(
    po_id: UUID,
    payload: ReceivePOPayload,
    _perm: bool = Depends(require_permission("purchasing.receive")),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    actor_user_id = None
    try:
        actor_user_id = UUID(user.sub)
    except Exception:
        pass

    service = PurchasingService(db)
    lines_data = [
        {
            "po_line_id": l.po_line_id,
            "sku_id": l.sku_id,
            "quantity": l.quantity,
            "unit_price": l.unit_price
        } for l in payload.lines
    ]
    try:
        receipt = await service.receive_purchase_order(po_id, tenant_id, lines_data, actor_user_id=actor_user_id)
        await db.commit()
        return {"receipt_id": receipt.id}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{po_id}/invoice")
async def register_invoice(
    po_id: UUID,
    payload: InvoicePOPayload,
    _perm: bool = Depends(require_permission("purchasing.create")),
    db: AsyncSession = Depends(get_secure_session),
    tenant_id: UUID = Depends(get_tenant_id_from_header)
):
    service = PurchasingService(db)
    invoice_data = {
        "invoice_number": payload.invoice_number,
        "issue_date": payload.issue_date,
        "due_date": payload.due_date,
        "total_amount": payload.total_amount
    }
    lines_data = [
        {
            "po_line_id": l.po_line_id,
            "sku_id": l.sku_id,
            "invoiced_quantity": l.invoiced_quantity,
            "unit_price": l.unit_price
        } for l in payload.lines
    ]
    try:
        invoice = await service.register_supplier_invoice(po_id, tenant_id, invoice_data, lines_data)
        await db.commit()
        return {"invoice_id": invoice.id}
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{po_id}/reconciliation", response_model=List[EnrichedReconResponse])
async def get_po_reconciliations(
    po_id: UUID,
    _perm: bool = Depends(require_permission("purchasing.read")),
    db: AsyncSession = Depends(get_secure_session)
):
    stmt = (
        select(
            PurchaseReconciliation.id,
            PurchaseOrderLine.id.label("po_line_id"),
            SKU.id.label("sku_id"),
            SKU.name.label("sku_name"),
            UOM.symbol.label("uom_symbol"),
            PurchaseOrderLine.ordered_quantity.label("ordered_qty"),
            PurchaseOrderLine.unit_price.label("ordered_price"),
            GoodsReceiptLine.quantity.label("received_qty"),
            GoodsReceiptLine.unit_price.label("received_price"),
            SupplierInvoiceLine.invoiced_quantity.label("invoiced_qty"),
            SupplierInvoiceLine.unit_price.label("invoiced_price"),
            PurchaseReconciliation.status
        )
        .join(PurchaseOrderLine, PurchaseReconciliation.purchase_order_line_id == PurchaseOrderLine.id)
        .join(SKU, PurchaseOrderLine.sku_id == SKU.id)
        .join(UOM, SKU.base_uom_id == UOM.id)
        .outerjoin(GoodsReceiptLine, PurchaseReconciliation.receipt_line_id == GoodsReceiptLine.id)
        .outerjoin(SupplierInvoiceLine, PurchaseReconciliation.invoice_line_id == SupplierInvoiceLine.id)
        .where(PurchaseOrderLine.purchase_order_id == po_id)
    )
    
    result = await db.execute(stmt)
    return [EnrichedReconResponse.model_validate(row) for row in result.all()]
