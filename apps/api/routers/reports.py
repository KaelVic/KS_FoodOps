from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from modules.reporting.service import ReportingService
from modules.reporting.consolidated import ConsolidatedReportService
from modules.reporting.exporter import ReportExporter

router = APIRouter(tags=["Reports"])


# ==========================================
# Schemas
# ==========================================

class ConsolidatedReportResponse(BaseModel):
    total_revenue: Decimal
    actual_cmv: Decimal
    theoretical_consumption: Decimal
    registered_losses: Decimal
    unexplained_variance: Decimal
    cmv_percentage: Decimal # (actual_cmv / total_revenue) * 100 if revenue > 0 else 0

    model_config = ConfigDict(from_attributes=True)


class LossReasonItem(BaseModel):
    reason: str
    quantity: Decimal
    total_value: Decimal


class LossDetailItem(BaseModel):
    sku_name: str
    uom_symbol: str
    reason: str
    quantity: Decimal
    unit_cost: Decimal
    total_value: Decimal
    posted_at: Optional[str] = None


class LossesAnalysisResponse(BaseModel):
    total_losses_value: Decimal
    by_reason: List[LossReasonItem]
    items: List[LossDetailItem]

    model_config = ConfigDict(from_attributes=True)


class StockPositionItem(BaseModel):
    sku_id: str
    sku_name: str
    category_name: str
    uom_symbol: str
    total_quantity: Decimal
    unit_cost: Decimal
    total_value: Decimal

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Endpoints
# ==========================================

@router.get("/consolidated", response_model=ConsolidatedReportResponse)
async def get_consolidated_report(
    location_id: UUID = Query(..., description="Target Location for CMV Analysis"),
    start_date: datetime = Query(..., description="Start Date (ISO format)"),
    end_date: datetime = Query(..., description="End Date (ISO format)"),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    """
    Returns the consolidated financial and inventory closing report (DRE Operacional).
    """
    service = ConsolidatedReportService(db)
    data = await service.generate(
        tenant_id=tenant_id,
        location_id=location_id,
        start_date=start_date,
        end_date=end_date
    )
    
    rev = data["total_revenue"]
    actual = data["actual_cmv"]
    cmv_pct = (actual / rev * Decimal('100')) if rev > Decimal('0') else Decimal('0')
    
    return ConsolidatedReportResponse(
        total_revenue=rev,
        actual_cmv=actual,
        theoretical_consumption=data["theoretical_consumption"],
        registered_losses=data["registered_losses"],
        unexplained_variance=data["unexplained_variance"],
        cmv_percentage=cmv_pct.quantize(Decimal('0.01'))
    )


@router.get("/losses", response_model=LossesAnalysisResponse)
async def get_losses_report(
    start_date: Optional[datetime] = Query(None, description="Filter Start Date"),
    end_date: Optional[datetime] = Query(None, description="Filter End Date"),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    """
    Returns an analytical breakdown of registered stock losses grouped by reason and detailed by SKU.
    """
    return await ReportingService.get_losses_analysis_report(
        db=db,
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/inventory/position", response_model=List[StockPositionItem])
async def get_stock_position(
    location_id: Optional[UUID] = Query(None, description="Optional Location filter"),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    """
    Returns real-time stock valuation report with average cost and total values.
    """
    return await ReportingService.get_stock_position_report(
        db=db,
        tenant_id=tenant_id,
        location_id=location_id
    )


@router.get("/inventory/export/csv")
async def export_inventory_csv(
    location_id: Optional[UUID] = Query(None, description="Optional Location filter"),
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    """
    Exports inventory position to Excel/Google Sheets compatible CSV with BOM and Portuguese headers.
    """
    items = await ReportingService.get_stock_position_report(
        db=db,
        tenant_id=tenant_id,
        location_id=location_id
    )
    
    csv_content = ReportExporter.export_inventory_valuation_csv(items)
    # UTF-8 with BOM for flawless opening in Excel on Windows
    csv_bytes = ("\ufeff" + csv_content).encode("utf-8")
    
    filename = f"inventario_posicao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/inventory/export/sped")
async def export_inventory_sped(
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    """
    Exports inventory position into SPED Fiscal Bloco H (H005 / H010) standard format.
    """
    items = await ReportingService.get_sped_bloco_h_data(
        db=db,
        tenant_id=tenant_id
    )
    
    sped_content = ReportExporter.export_to_sped_bloco_h(items)
    filename = f"sped_bloco_h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    return Response(
        content=sped_content.encode("latin-1", errors="replace"),
        media_type="text/plain; charset=iso-8859-1",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
