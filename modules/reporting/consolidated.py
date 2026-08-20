from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from modules.inventory.service import InventoryService
from modules.sales.models import Sale
from modules.inventory.models import TheoreticalConsumption, StockMovement, StockLedgerEntry

class ConsolidatedReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.inventory_service = InventoryService(session)

    async def generate(self, tenant_id: UUID, location_id: UUID, start_date: datetime, end_date: datetime) -> Dict[str, Decimal]:
        """
        Gera o relatório analítico consolidado (Fechamento) para um tenant e localidade.
        """
        
        # 1. Total Revenue (Sales)
        stmt_rev = select(func.coalesce(func.sum(Sale.total_amount), Decimal(0))).where(
            Sale.tenant_id == tenant_id,
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date
        )
        if location_id:
            stmt_rev = stmt_rev.where((Sale.location_id == location_id) | (Sale.location_id.is_(None)))
        total_revenue = Decimal((await self.session.execute(stmt_rev)).scalar_one())

        # 2. Theoretical Consumption
        stmt_theo = select(func.coalesce(func.sum(TheoreticalConsumption.quantity * TheoreticalConsumption.unit_cost_at_time), Decimal(0))).where(
            TheoreticalConsumption.tenant_id == tenant_id,
            TheoreticalConsumption.created_at >= start_date,
            TheoreticalConsumption.created_at <= end_date
        )
        theoretical_consumption = Decimal((await self.session.execute(stmt_theo)).scalar_one())

        # 3. Actual CMV
        actual_cmv = await self.inventory_service.calculate_operational_cmv(
            location_id=location_id,
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id
        )

        # 4. Registered Losses
        stmt_loss = select(func.coalesce(func.sum(StockLedgerEntry.quantity * StockLedgerEntry.unit_cost), Decimal(0))).select_from(StockLedgerEntry).join(
            StockMovement, StockLedgerEntry.movement_id == StockMovement.id
        ).where(
            StockMovement.location_id == location_id,
            StockLedgerEntry.tenant_id == tenant_id,
            StockMovement.type == 'LOSS',
            StockMovement.posted_at >= start_date,
            StockMovement.posted_at <= end_date
        )
        # Note: quantity is negative for LOSS, so we multiply by -1 to get a positive value
        registered_losses = Decimal((await self.session.execute(stmt_loss)).scalar_one()) * Decimal('-1')

        # 5. Unexplained Variance (Divergência)
        # What is physically gone (actual_cmv) minus what should be gone (theoretical) minus what we know is gone (losses)
        unexplained_variance = actual_cmv - theoretical_consumption - registered_losses

        return {
            "total_revenue": total_revenue,
            "actual_cmv": actual_cmv,
            "theoretical_consumption": theoretical_consumption,
            "registered_losses": registered_losses,
            "unexplained_variance": unexplained_variance
        }
