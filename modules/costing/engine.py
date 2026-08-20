import uuid
from decimal import Decimal
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from modules.inventory.models import StockBalanceProjection, StockLedgerEntry
from modules.costing.service import CostingService


class CostingEngine:
    """
    Single unified authority for SKU and Recipe costing across the entire ERP.
    Eliminates fragmented calculations, arbitrary fallback numbers, and divergence.
    """

    @staticmethod
    async def get_sku_cost(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        sku_id: uuid.UUID,
        location_id: Optional[uuid.UUID] = None,
        at_time: Optional[datetime] = None
    ) -> Decimal:
        """
        Determines the unit cost for a SKU.
        1. If at_time is specified, computes historical weighted average cost (CMP) at that instant.
        2. If current, checks StockBalanceProjection for total_value / quantity (> 0).
        3. If balance is 0 or uninitialized, falls back to the most recent positive receipt cost in StockLedgerEntry.
        4. If no purchase history exists, returns Decimal('0.00'). Never invents a fake non-zero cost.
        """
        if at_time:
            return await CostingService.calculate_historical_cmp(
                db=db,
                tenant_id=tenant_id,
                sku_id=sku_id,
                up_to_date=at_time
            )

        # 1. Try location-specific or aggregate StockBalanceProjection
        stmt = select(StockBalanceProjection).where(
            StockBalanceProjection.tenant_id == tenant_id,
            StockBalanceProjection.sku_id == sku_id
        )
        if location_id:
            stmt = stmt.where(StockBalanceProjection.location_id == location_id)

        result = await db.execute(stmt)
        balances = result.scalars().all()

        total_qty = sum((Decimal(str(b.quantity)) for b in balances), Decimal("0"))
        total_val = sum((Decimal(str(b.total_value)) for b in balances), Decimal("0"))

        if total_qty > Decimal("0") and total_val > Decimal("0"):
            return (total_val / total_qty).quantize(Decimal("0.0001"))

        # 2. Check the most recent positive entry unit cost in ledger
        entry_stmt = select(StockLedgerEntry.unit_cost).where(
            StockLedgerEntry.tenant_id == tenant_id,
            StockLedgerEntry.sku_id == sku_id,
            StockLedgerEntry.unit_cost.isnot(None),
            StockLedgerEntry.quantity > 0
        ).order_by(StockLedgerEntry.created_at.desc(), StockLedgerEntry.id.desc()).limit(1)

        entry_cost = (await db.execute(entry_stmt)).scalar_one_or_none()
        if entry_cost is not None and entry_cost > 0:
            return Decimal(str(entry_cost)).quantize(Decimal("0.0001"))

        # 3. Full historical CMP calculation as fallback
        cmp = await CostingService.calculate_historical_cmp(
            db=db,
            tenant_id=tenant_id,
            sku_id=sku_id
        )
        if cmp > Decimal("0"):
            return cmp.quantize(Decimal("0.0001"))

        return Decimal("0.00")
