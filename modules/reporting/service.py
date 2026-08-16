import uuid
from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from modules.inventory.models import StockBalanceProjection, StockLedgerEntry, StockMovement, LossRecord
from modules.catalog.models import SKU, Category, UOM

class ReportingService:
    @staticmethod
    async def get_stock_position_report(
        db: AsyncSession, 
        tenant_id: uuid.UUID, 
        location_id: Optional[uuid.UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates a consolidated and enriched stock valuation report for the tenant.
        """
        stmt = (
            select(
                SKU.id.label('sku_id'),
                SKU.name.label('sku_name'),
                Category.name.label('category_name'),
                UOM.symbol.label('uom_symbol'),
                func.sum(StockBalanceProjection.quantity).label('total_quantity'),
                func.sum(StockBalanceProjection.total_value).label('total_value')
            )
            .join(StockBalanceProjection, SKU.id == StockBalanceProjection.sku_id)
            .join(UOM, SKU.base_uom_id == UOM.id)
            .outerjoin(Category, SKU.category_id == Category.id)
            .where(StockBalanceProjection.tenant_id == tenant_id)
        )
        
        if location_id:
            stmt = stmt.where(StockBalanceProjection.location_id == location_id)
            
        stmt = stmt.group_by(SKU.id, SKU.name, Category.name, UOM.symbol).order_by(SKU.name)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        report = []
        for row in rows:
            qty = Decimal(str(row.total_quantity or 0))
            val = Decimal(str(row.total_value or 0))
            unit_cost = val / qty if qty > Decimal('0') else Decimal('0.0')
            
            report.append({
                "sku_id": str(row.sku_id),
                "sku_name": row.sku_name,
                "category_name": row.category_name or "Sem Categoria",
                "uom_symbol": row.uom_symbol,
                "total_quantity": qty,
                "unit_cost": unit_cost,
                "total_value": val,
            })
            
        return report

    @staticmethod
    async def get_losses_analysis_report(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generates an analytical loss report grouped by loss reason and SKU breakdown.
        """
        filters = [
            StockLedgerEntry.tenant_id == tenant_id,
            StockMovement.type == 'LOSS'
        ]
        if start_date:
            filters.append(StockMovement.posted_at >= start_date)
        if end_date:
            filters.append(StockMovement.posted_at <= end_date)

        # 1. Losses by reason
        stmt_by_reason = (
            select(
                func.coalesce(LossRecord.reason, 'OUTROS').label('reason'),
                func.sum(StockLedgerEntry.quantity).label('total_qty'),
                func.sum(StockLedgerEntry.quantity * StockLedgerEntry.unit_cost).label('total_val')
            )
            .select_from(StockLedgerEntry)
            .join(StockMovement, StockLedgerEntry.movement_id == StockMovement.id)
            .outerjoin(LossRecord, StockMovement.id == LossRecord.movement_id)
            .where(and_(*filters))
            .group_by(LossRecord.reason)
        )
        res_reason = await db.execute(stmt_by_reason)
        by_reason = []
        total_loss_val = Decimal('0')
        for r in res_reason.all():
            qty = abs(Decimal(str(r.total_qty or 0)))
            val = abs(Decimal(str(r.total_val or 0)))
            total_loss_val += val
            by_reason.append({
                "reason": r.reason,
                "quantity": qty,
                "total_value": val
            })

        # 2. Detailed loss lines by SKU
        stmt_items = (
            select(
                SKU.name.label('sku_name'),
                UOM.symbol.label('uom_symbol'),
                func.coalesce(LossRecord.reason, 'OUTROS').label('reason'),
                StockLedgerEntry.quantity.label('quantity'),
                StockLedgerEntry.unit_cost.label('unit_cost'),
                StockMovement.posted_at.label('posted_at')
            )
            .select_from(StockLedgerEntry)
            .join(StockMovement, StockLedgerEntry.movement_id == StockMovement.id)
            .join(SKU, StockLedgerEntry.sku_id == SKU.id)
            .join(UOM, SKU.base_uom_id == UOM.id)
            .outerjoin(LossRecord, StockMovement.id == LossRecord.movement_id)
            .where(and_(*filters))
            .order_by(StockMovement.posted_at.desc())
        )
        res_items = await db.execute(stmt_items)
        items = []
        for row in res_items.all():
            qty = abs(Decimal(str(row.quantity or 0)))
            cost = Decimal(str(row.unit_cost or 0))
            items.append({
                "sku_name": row.sku_name,
                "uom_symbol": row.uom_symbol,
                "reason": row.reason,
                "quantity": qty,
                "unit_cost": cost,
                "total_value": qty * cost,
                "posted_at": row.posted_at.isoformat() if row.posted_at else None
            })

        return {
            "total_losses_value": total_loss_val,
            "by_reason": by_reason,
            "items": items
        }

    @staticmethod
    async def get_sped_bloco_h_data(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        inventory_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepares structured inventory records for SPED Fiscal Bloco H (H005 e H010).
        """
        position = await ReportingService.get_stock_position_report(db, tenant_id)
        return position
