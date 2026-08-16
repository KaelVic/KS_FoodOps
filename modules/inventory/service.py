from typing import List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import update, insert, and_, func
from decimal import Decimal

from modules.inventory.models import StockMovement, StockLedgerEntry, StockBalanceProjection, InventorySession, InventorySessionLocation, InventoryCountLine, InventoryCloseResult, LossRecord, AccountingPeriod
from modules.purchasing.models import GoodsReceipt, GoodsReceiptLine
from modules.catalog.models import SKUConversionVersion, SKU
from modules.suppliers.models import SupplierSKU
from sqlalchemy.exc import IntegrityError
class InventoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _guard_accounting_period(self, tenant_id: UUID, target_date: datetime):
        stmt = select(AccountingPeriod).where(
            AccountingPeriod.tenant_id == tenant_id,
            AccountingPeriod.status == 'CLOSED',
            AccountingPeriod.start_date <= target_date,
            AccountingPeriod.end_date >= target_date
        )
        closed_period = (await self.session.execute(stmt)).scalars().first()
        if closed_period:
            raise ValueError(f"Cannot post stock movement. Date {target_date} is within a closed accounting period.")

    async def post_goods_receipt(self, receipt_id: UUID, tenant_id: UUID) -> StockMovement:
        """
        Idempotent service to post a Goods Receipt to the inventory ledger.
        """
        # 1. Fetch Receipt
        stmt = select(GoodsReceipt).where(
            GoodsReceipt.id == receipt_id,
            GoodsReceipt.tenant_id == tenant_id
        ).with_for_update() # Lock the receipt
        
        result = await self.session.execute(stmt)
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise ValueError(f"GoodsReceipt {receipt_id} not found.")
            
        if receipt.status == 'POSTED':
            # Idempotency: if already posted, just fetch the existing movement
            stmt = select(StockMovement).where(
                StockMovement.reference_id == receipt_id,
                StockMovement.reference_type == 'GoodsReceipt',
                StockMovement.tenant_id == tenant_id
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()

        # Fetch lines
        stmt = select(GoodsReceiptLine).where(
            GoodsReceiptLine.receipt_id == receipt_id,
            GoodsReceiptLine.tenant_id == tenant_id
        )
        lines = (await self.session.execute(stmt)).scalars().all()
        
        now = datetime.now(timezone.utc)
        await self._guard_accounting_period(tenant_id, now)
        
        # 2. Create Movement
        movement = StockMovement(
            tenant_id=tenant_id,
            location_id=receipt.location_id,
            type='RECEIPT',
            status='POSTED',
            reference_id=receipt_id,
            reference_type='GoodsReceipt',
            posted_at=now
        )
        self.session.add(movement)
        await self.session.flush() # flush to get movement.id
        
        for line in lines:
            # 3. Resolve Conversion (if applicable)
            conversion_version_id = None
            quantity = Decimal(line.quantity)
            
            if line.supplier_sku_id:
                # Need to convert from supplier UOM to base UOM
                stmt = select(SupplierSKU).where(SupplierSKU.id == line.supplier_sku_id)
                supplier_sku = (await self.session.execute(stmt)).scalar_one()
                
                if supplier_sku.default_conversion_version_id:
                    stmt = select(SKUConversionVersion).where(SKUConversionVersion.id == supplier_sku.default_conversion_version_id)
                    version = (await self.session.execute(stmt)).scalar_one()
                    conversion_version_id = version.id
                    quantity = quantity * Decimal(version.factor)
            
            # 4. Lock and Update Balance Projection
            stmt = select(StockBalanceProjection).where(
                StockBalanceProjection.sku_id == line.sku_id,
                StockBalanceProjection.location_id == receipt.location_id,
                StockBalanceProjection.tenant_id == tenant_id
            ).with_for_update()
            
            result = await self.session.execute(stmt)
            balance = result.scalar_one_or_none()
            
            if balance is None:
                balance = StockBalanceProjection(
                    tenant_id=tenant_id,
                    location_id=receipt.location_id,
                    sku_id=line.sku_id,
                    quantity=Decimal('0'),
                    total_value=Decimal('0')
                )
                self.session.add(balance)
                try:
                    async with self.session.begin_nested():
                        await self.session.flush()
                except IntegrityError:
                    # Concurrently created, re-fetch
                    pass
                
                # Re-fetch with lock just to be absolutely sure in concurrent edge cases
                stmt = select(StockBalanceProjection).where(
                    StockBalanceProjection.id == balance.id
                ).with_for_update()
                balance = (await self.session.execute(stmt)).scalar_one()
                
            line_value = quantity * Decimal(line.unit_price)
            
            # Weighted average cost update or simple sum
            balance.quantity += quantity
            balance.total_value += line_value
            
            # 5. Create Ledger Entry
            ledger_entry = StockLedgerEntry(
                tenant_id=tenant_id,
                movement_id=movement.id,
                sku_id=line.sku_id,
                quantity=quantity,
                unit_cost=Decimal(line.unit_price),
                conversion_version_id=conversion_version_id,
                balance_after=balance.quantity
            )
            self.session.add(ledger_entry)
            
        # 6. Mark receipt as POSTED
        receipt.status = 'POSTED'
        receipt.posted_at = now
        
        return movement

    async def close_inventory_session(self, session_id: UUID, tenant_id: UUID) -> InventorySession:
        """
        Idempotent service to close an inventory session and post variances.
        """
        stmt = select(InventorySession).where(
            InventorySession.id == session_id,
            InventorySession.tenant_id == tenant_id
        ).with_for_update()
        
        result = await self.session.execute(stmt)
        inv_session = result.scalar_one_or_none()
        
        if not inv_session:
            raise ValueError(f"InventorySession {session_id} not found.")
            
        if inv_session.status == 'CLOSED':
            return inv_session
            
        cutoff = inv_session.cutoff_at or datetime.now(timezone.utc)
        
        # Aggregate counted quantities by location and SKU
        stmt = select(
            InventoryCountLine.location_id,
            InventoryCountLine.sku_id,
            func.sum(InventoryCountLine.counted_quantity).label('counted')
        ).where(
            InventoryCountLine.session_id == session_id,
            InventoryCountLine.tenant_id == tenant_id
        ).group_by(
            InventoryCountLine.location_id,
            InventoryCountLine.sku_id
        )
        counts = (await self.session.execute(stmt)).all()
        
        now = datetime.now(timezone.utc)
        await self._guard_accounting_period(tenant_id, now)
        
        for loc_id, sku_id, counted_qty in counts:
            counted_qty = Decimal(counted_qty)
            
            # Lock the balance projection early to prevent concurrent movements from sneaking in
            stmt = select(StockBalanceProjection).where(
                StockBalanceProjection.sku_id == sku_id,
                StockBalanceProjection.location_id == loc_id,
                StockBalanceProjection.tenant_id == tenant_id
            ).with_for_update()
            balance = (await self.session.execute(stmt)).scalar_one_or_none()
            
            # Calculate expected quantity at cutoff time
            # Expected = Sum of all ledger entries for this location up to cutoff
            stmt = select(func.coalesce(func.sum(StockLedgerEntry.quantity), 0)).select_from(StockLedgerEntry).join(
                StockMovement, StockLedgerEntry.movement_id == StockMovement.id
            ).where(
                StockMovement.location_id == loc_id,
                StockLedgerEntry.sku_id == sku_id,
                StockLedgerEntry.tenant_id == tenant_id,
                StockMovement.posted_at <= cutoff
            )
            expected_qty = Decimal((await self.session.execute(stmt)).scalar_one())
            
            variance_qty = counted_qty - expected_qty
            variance_value = Decimal('0')
            unit_cost = Decimal('0')
            
            if variance_qty != 0:
                if balance and balance.quantity > 0:
                    unit_cost = balance.total_value / balance.quantity
                
                variance_value = variance_qty * unit_cost
                
                # Generate adjustment movement
                movement = StockMovement(
                    tenant_id=tenant_id,
                    location_id=loc_id,
                    type='INVENTORY_ADJUSTMENT',
                    status='POSTED',
                    reference_id=session_id,
                    reference_type='InventorySession',
                    posted_at=now
                )
                self.session.add(movement)
                await self.session.flush()
                
                if not balance:
                    balance = StockBalanceProjection(
                        tenant_id=tenant_id,
                        location_id=loc_id,
                        sku_id=sku_id,
                        quantity=Decimal('0'),
                        total_value=Decimal('0')
                    )
                    self.session.add(balance)
                    await self.session.flush()
                    
                    stmt = select(StockBalanceProjection).where(StockBalanceProjection.id == balance.id).with_for_update()
                    balance = (await self.session.execute(stmt)).scalar_one()
                
                balance.quantity += variance_qty
                balance.total_value += variance_value
                
                ledger_entry = StockLedgerEntry(
                    tenant_id=tenant_id,
                    movement_id=movement.id,
                    sku_id=sku_id,
                    quantity=variance_qty,
                    unit_cost=unit_cost,
                    balance_after=balance.quantity
                )
                self.session.add(ledger_entry)
            
            # Record Close Result
            close_result = InventoryCloseResult(
                tenant_id=tenant_id,
                session_id=session_id,
                sku_id=sku_id,
                expected_quantity=expected_qty,
                counted_quantity=counted_qty,
                variance_quantity=variance_qty,
                variance_value=variance_value
            )
            self.session.add(close_result)
            
        inv_session.status = 'CLOSED'
        inv_session.closed_at = now
        
        return inv_session

    async def calculate_operational_cmv(self, location_id: UUID, start_date: datetime, end_date: datetime, tenant_id: UUID) -> Decimal:
        """
        Calculate Actual Operational CMV = Opening Value + Net Receipts - Closing Value
        Wait, a simpler way is: CMV = sum of value of all outgoing stock (sales, waste) - sum of positive adjustments + negative adjustments.
        Actually, Operational CMV is exactly the sum of negative value from specific outflow movements.
        Let's use the formula: Opening + Purchases - Closing.
        """
        # Opening value
        stmt = select(func.coalesce(func.sum(StockLedgerEntry.quantity * StockLedgerEntry.unit_cost), 0)).select_from(StockLedgerEntry).join(
            StockMovement, StockLedgerEntry.movement_id == StockMovement.id
        ).where(
            StockMovement.location_id == location_id,
            StockLedgerEntry.tenant_id == tenant_id,
            StockMovement.posted_at < start_date
        )
        opening_value = Decimal((await self.session.execute(stmt)).scalar_one())
        
        # Net Receipts during period
        stmt = select(func.coalesce(func.sum(StockLedgerEntry.quantity * StockLedgerEntry.unit_cost), 0)).select_from(StockLedgerEntry).join(
            StockMovement, StockLedgerEntry.movement_id == StockMovement.id
        ).where(
            StockMovement.location_id == location_id,
            StockLedgerEntry.tenant_id == tenant_id,
            StockMovement.type == 'RECEIPT',
            StockMovement.posted_at >= start_date,
            StockMovement.posted_at <= end_date
        )
        receipts_value = Decimal((await self.session.execute(stmt)).scalar_one())
        
        # Closing value
        stmt = select(func.coalesce(func.sum(StockLedgerEntry.quantity * StockLedgerEntry.unit_cost), 0)).select_from(StockLedgerEntry).join(
            StockMovement, StockLedgerEntry.movement_id == StockMovement.id
        ).where(
            StockMovement.location_id == location_id,
            StockLedgerEntry.tenant_id == tenant_id,
            StockMovement.posted_at <= end_date
        )
        closing_value = Decimal((await self.session.execute(stmt)).scalar_one())
        cmv = opening_value + receipts_value - closing_value
        return cmv

    async def register_loss(self, location_id: UUID, sku_id: UUID, quantity: Decimal, reason: str, actor: str, tenant_id: UUID) -> LossRecord:
        """
        Record a physical loss / waste, decreasing stock balance and creating ledger entries.
        """
        if quantity <= Decimal('0'):
            raise ValueError("Loss quantity must be greater than zero.")

        now = datetime.now(timezone.utc)
        await self._guard_accounting_period(tenant_id, now)

        # 1. Lock and update StockBalanceProjection
        stmt = select(StockBalanceProjection).where(
            StockBalanceProjection.sku_id == sku_id,
            StockBalanceProjection.location_id == location_id,
            StockBalanceProjection.tenant_id == tenant_id
        ).with_for_update()

        balance = (await self.session.execute(stmt)).scalar_one_or_none()
        unit_cost = Decimal('0')
        if balance and balance.quantity > 0:
            unit_cost = balance.total_value / balance.quantity

        if not balance:
            balance = StockBalanceProjection(
                tenant_id=tenant_id,
                location_id=location_id,
                sku_id=sku_id,
                quantity=Decimal('0'),
                total_value=Decimal('0')
            )
            self.session.add(balance)
            await self.session.flush()

            stmt = select(StockBalanceProjection).where(StockBalanceProjection.id == balance.id).with_for_update()
            balance = (await self.session.execute(stmt)).scalar_one()

        loss_value = quantity * unit_cost
        balance.quantity -= quantity
        balance.total_value -= loss_value

        # 2. Pre-generate LossRecord id so we can link it to the movement
        #    BEFORE flushing, avoiding an UPDATE on the POSTED movement
        #    which would trigger the immutability trigger.
        import uuid as _uuid
        loss_record_id = _uuid.uuid4()

        # 3. Create StockMovement with reference_id already set
        movement = StockMovement(
            tenant_id=tenant_id,
            location_id=location_id,
            type='LOSS',
            status='POSTED',
            reference_type='LossRecord',
            reference_id=loss_record_id,
            posted_at=now
        )
        self.session.add(movement)
        await self.session.flush()

        # 4. Create StockLedgerEntry
        ledger_entry = StockLedgerEntry(
            tenant_id=tenant_id,
            movement_id=movement.id,
            sku_id=sku_id,
            quantity=-quantity,
            unit_cost=unit_cost,
            balance_after=balance.quantity
        )
        self.session.add(ledger_entry)

        # 5. Create LossRecord using the pre-generated id
        loss_record = LossRecord(
            id=loss_record_id,
            tenant_id=tenant_id,
            movement_id=movement.id,
            reason=reason,
            actor=actor
        )
        self.session.add(loss_record)
        await self.session.flush()

        return loss_record

    async def close_period(self, period_id: UUID, tenant_id: UUID) -> AccountingPeriod:
        stmt = select(AccountingPeriod).where(
            AccountingPeriod.id == period_id,
            AccountingPeriod.tenant_id == tenant_id
        ).with_for_update()
        period = (await self.session.execute(stmt)).scalar_one_or_none()
        if not period:
            raise ValueError("AccountingPeriod not found.")
        if period.status == 'CLOSED':
            return period
            
        period.status = 'CLOSED'
        period.closed_at = datetime.now(timezone.utc)
        return period
