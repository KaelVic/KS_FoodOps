from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import update, insert, and_, func
from decimal import Decimal

from modules.inventory.models import (
    StockMovement,
    StockLedgerEntry,
    StockBalanceProjection,
    InventorySession,
    InventorySessionLocation,
    InventoryCountLine,
    InventoryCloseResult,
    LossRecord,
    AccountingPeriod,
    StockTransfer,
    StockTransferItem,
)
from modules.purchasing.models import GoodsReceipt, GoodsReceiptLine
from modules.catalog.models import SKUConversionVersion, SKU
from packages.tenant.models import Location
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

    async def post_goods_receipt(
        self,
        receipt_id: UUID,
        tenant_id: UUID,
        actor_user_id: Optional[UUID] = None
    ) -> StockMovement:
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
            actor_user_id=actor_user_id,
            reason_code='PURCHASE_RECEIPT',
            notes=f"Receipt of PO items for GoodsReceipt {receipt_id}",
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

    async def close_inventory_session(
        self,
        session_id: UUID,
        tenant_id: UUID,
        actor_user_id: Optional[UUID] = None
    ) -> InventorySession:
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
        
        total_variance_count = 0
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
                total_variance_count += 1
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
                    actor_user_id=actor_user_id,
                    reason_code='COUNT_VARIANCE',
                    notes=f"Variance adjustment for inventory session {session_id}",
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

        # Log Audit
        from packages.audit.service import AuditService
        await AuditService.log_action(
            db=self.session,
            tenant_id=tenant_id,
            actor_id=actor_user_id or session_id,
            action="INVENTORY_SESSION_CLOSED",
            resource_type="inventory_sessions",
            resource_id=session_id,
            changes_payload={
                "session_id": str(session_id),
                "variances_posted": total_variance_count,
                "closed_at": str(now)
            }
        )
        
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

    async def register_loss(
        self,
        location_id: UUID,
        sku_id: UUID,
        quantity: Decimal,
        reason: str,
        actor: str,
        tenant_id: UUID,
        actor_user_id: Optional[UUID] = None
    ) -> LossRecord:
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
            actor_user_id=actor_user_id,
            reason_code=reason,
            notes=f"Stock loss registered by {actor}. Reason: {reason}",
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

        # 6. Audit Log
        from packages.audit.service import AuditService
        await AuditService.log_action(
            db=self.session,
            tenant_id=tenant_id,
            actor_id=actor_user_id or loss_record_id,
            action="STOCK_LOSS_RECORDED",
            resource_type="loss_records",
            resource_id=loss_record.id,
            changes_payload={
                "location_id": str(location_id),
                "sku_id": str(sku_id),
                "quantity": float(quantity),
                "unit_cost": float(unit_cost),
                "loss_value": float(loss_value),
                "reason": reason,
                "actor": actor
            }
        )

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

    async def list_transfers(
        self,
        tenant_id: UUID,
        status: str = None,
    ) -> List[dict]:
        stmt = select(StockTransfer).where(StockTransfer.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(StockTransfer.status == status)
        stmt = stmt.order_by(StockTransfer.created_at.desc())
        transfers = (await self.session.execute(stmt)).scalars().all()

        result = []
        for t in transfers:
            orig = (await self.session.execute(select(Location).where(Location.id == t.origin_location_id))).scalar_one_or_none()
            dest = (await self.session.execute(select(Location).where(Location.id == t.destination_location_id))).scalar_one_or_none()
            
            # Count items
            item_count_stmt = select(func.count(StockTransferItem.id)).where(
                StockTransferItem.transfer_id == t.id,
                StockTransferItem.tenant_id == tenant_id,
            )
            item_count = (await self.session.execute(item_count_stmt)).scalar() or 0

            result.append({
                "id": str(t.id),
                "tenant_id": str(t.tenant_id),
                "transfer_number": t.transfer_number,
                "origin_location_id": str(t.origin_location_id),
                "origin_location_name": orig.name if orig else "Origem",
                "destination_location_id": str(t.destination_location_id),
                "destination_location_name": dest.name if dest else "Destino",
                "status": t.status,
                "items_count": item_count,
                "dispatched_at": t.dispatched_at.isoformat() if t.dispatched_at else None,
                "received_at": t.received_at.isoformat() if t.received_at else None,
                "notes": t.notes,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            })
        return result

    async def get_transfer_dict(
        self,
        tenant_id: UUID,
        transfer_id: UUID,
    ) -> Optional[dict]:
        stmt = select(StockTransfer).where(
            StockTransfer.id == transfer_id,
            StockTransfer.tenant_id == tenant_id,
        )
        t = (await self.session.execute(stmt)).scalar_one_or_none()
        if not t:
            return None

        orig = (await self.session.execute(select(Location).where(Location.id == t.origin_location_id))).scalar_one_or_none()
        dest = (await self.session.execute(select(Location).where(Location.id == t.destination_location_id))).scalar_one_or_none()

        items_stmt = select(StockTransferItem).where(
            StockTransferItem.transfer_id == t.id,
            StockTransferItem.tenant_id == tenant_id,
        )
        items = (await self.session.execute(items_stmt)).scalars().all()
        items_list = []
        for it in items:
            sku = (await self.session.execute(select(SKU).where(SKU.id == it.sku_id))).scalar_one_or_none()
            items_list.append({
                "id": str(it.id),
                "sku_id": str(it.sku_id),
                "sku_name": sku.name if sku else "SKU",
                "quantity_sent": float(it.quantity_sent),
                "quantity_received": float(it.quantity_received) if it.quantity_received is not None else None,
                "unit_cost": float(it.unit_cost),
            })

        return {
            "id": str(t.id),
            "tenant_id": str(t.tenant_id),
            "transfer_number": t.transfer_number,
            "origin_location_id": str(t.origin_location_id),
            "origin_location_name": orig.name if orig else "Origem",
            "destination_location_id": str(t.destination_location_id),
            "destination_location_name": dest.name if dest else "Destino",
            "status": t.status,
            "items": items_list,
            "dispatched_at": t.dispatched_at.isoformat() if t.dispatched_at else None,
            "received_at": t.received_at.isoformat() if t.received_at else None,
            "notes": t.notes,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }

    async def create_transfer(
        self,
        tenant_id: UUID,
        origin_location_id: UUID,
        destination_location_id: UUID,
        items: List[dict], # [{"sku_id": UUID, "quantity_sent": Decimal}]
        notes: Optional[str] = None,
    ) -> StockTransfer:
        if origin_location_id == destination_location_id:
            raise ValueError("O local de origem e destino não podem ser iguais.")

        count_stmt = select(func.count(StockTransfer.id)).where(StockTransfer.tenant_id == tenant_id)
        current_count = (await self.session.execute(count_stmt)).scalar() or 0
        transfer_number = f"TRF-{(current_count + 1):04d}"

        transfer = StockTransfer(
            tenant_id=tenant_id,
            transfer_number=transfer_number,
            origin_location_id=origin_location_id,
            destination_location_id=destination_location_id,
            status="DRAFT",
            notes=notes,
        )
        self.session.add(transfer)
        await self.session.flush()

        for it in items:
            sku_id = it["sku_id"]
            qty = Decimal(str(it["quantity_sent"]))

            # Get CMP in origin location
            bal_stmt = select(StockBalanceProjection).where(
                StockBalanceProjection.sku_id == sku_id,
                StockBalanceProjection.location_id == origin_location_id,
                StockBalanceProjection.tenant_id == tenant_id,
            )
            bal = (await self.session.execute(bal_stmt)).scalar_one_or_none()
            unit_cost = (bal.total_value / bal.quantity) if (bal and bal.quantity > 0) else Decimal("0")

            transfer_item = StockTransferItem(
                tenant_id=tenant_id,
                transfer_id=transfer.id,
                sku_id=sku_id,
                quantity_sent=qty,
                unit_cost=unit_cost,
            )
            self.session.add(transfer_item)

        await self.session.flush()
        return transfer

    async def dispatch_transfer(
        self,
        tenant_id: UUID,
        transfer_id: UUID,
    ) -> StockTransfer:
        stmt = (
            select(StockTransfer)
            .where(StockTransfer.id == transfer_id, StockTransfer.tenant_id == tenant_id)
            .with_for_update()
        )
        transfer = (await self.session.execute(stmt)).scalar_one_or_none()
        if not transfer:
            raise ValueError(f"Transferência {transfer_id} não encontrada.")
            
        if transfer.status != "DRAFT":
            raise ValueError(f"Transferência {transfer.transfer_number} já foi despachada ou concluída.")

        transfer.status = "IN_TRANSIT"
        transfer.dispatched_at = datetime.now(timezone.utc)
        await self.session.flush()
        return transfer

    async def receive_transfer(
        self,
        tenant_id: UUID,
        transfer_id: UUID,
        items_received: Optional[List[dict]] = None, # [{"item_id": UUID, "quantity_received": Decimal}]
    ) -> StockTransfer:
        """
        Receives the stock transfer, posting TRANSFER_OUT from origin location
        and TRANSFER_IN to destination location in immutable stock ledger.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(StockTransfer)
            .where(StockTransfer.id == transfer_id, StockTransfer.tenant_id == tenant_id)
            .with_for_update()
        )
        transfer = (await self.session.execute(stmt)).scalar_one_or_none()
        if not transfer:
            raise ValueError(f"Transferência {transfer_id} não encontrada.")
            
        if transfer.status == "RECEIVED":
            return transfer

        # 1. Fetch Items
        items_stmt = select(StockTransferItem).where(
            StockTransferItem.transfer_id == transfer.id,
            StockTransferItem.tenant_id == tenant_id,
        )
        transfer_items = (await self.session.execute(items_stmt)).scalars().all()

        # Map received quantities if provided
        rec_map = {}
        if items_received:
            for r in items_received:
                rec_map[str(r.get("item_id") or r.get("sku_id"))] = Decimal(str(r["quantity_received"]))

        # 2. Movement TRANSFER_OUT (at origin)
        out_movement = StockMovement(
            tenant_id=tenant_id,
            location_id=transfer.origin_location_id,
            type="TRANSFER_OUT",
            status="POSTED",
            reference_id=transfer.id,
            reference_type="StockTransfer",
            posted_at=now,
        )
        self.session.add(out_movement)

        # 3. Movement TRANSFER_IN (at destination)
        in_movement = StockMovement(
            tenant_id=tenant_id,
            location_id=transfer.destination_location_id,
            type="TRANSFER_IN",
            status="POSTED",
            reference_id=transfer.id,
            reference_type="StockTransfer",
            posted_at=now,
        )
        self.session.add(in_movement)
        await self.session.flush()

        for it in transfer_items:
            qty_rec = (
                rec_map.get(str(it.id))
                or rec_map.get(str(it.sku_id))
                or it.quantity_sent
            )
            it.quantity_received = qty_rec

            # === ORIGIN LOCATION: DEDUCT STOCK ===
            orig_bal_stmt = (
                select(StockBalanceProjection)
                .where(
                    StockBalanceProjection.sku_id == it.sku_id,
                    StockBalanceProjection.location_id == transfer.origin_location_id,
                    StockBalanceProjection.tenant_id == tenant_id,
                )
                .with_for_update()
            )
            orig_bal = (await self.session.execute(orig_bal_stmt)).scalar_one_or_none()
            if orig_bal is None:
                orig_bal = StockBalanceProjection(
                    tenant_id=tenant_id,
                    location_id=transfer.origin_location_id,
                    sku_id=it.sku_id,
                    quantity=Decimal("0"),
                    total_value=Decimal("0"),
                )
                self.session.add(orig_bal)
                await self.session.flush()
                orig_bal = (await self.session.execute(orig_bal_stmt)).scalar_one()

            unit_cost = (orig_bal.total_value / orig_bal.quantity) if orig_bal.quantity > 0 else Decimal("0")
            it.unit_cost = unit_cost
            transferred_value = it.quantity_sent * unit_cost

            orig_bal.quantity -= it.quantity_sent
            orig_bal.total_value -= transferred_value

            out_ledger = StockLedgerEntry(
                tenant_id=tenant_id,
                movement_id=out_movement.id,
                sku_id=it.sku_id,
                quantity=-it.quantity_sent,
                unit_cost=unit_cost,
                balance_after=orig_bal.quantity,
            )
            self.session.add(out_ledger)

            # === DESTINATION LOCATION: ADD STOCK ===
            dest_bal_stmt = (
                select(StockBalanceProjection)
                .where(
                    StockBalanceProjection.sku_id == it.sku_id,
                    StockBalanceProjection.location_id == transfer.destination_location_id,
                    StockBalanceProjection.tenant_id == tenant_id,
                )
                .with_for_update()
            )
            dest_bal = (await self.session.execute(dest_bal_stmt)).scalar_one_or_none()
            if dest_bal is None:
                dest_bal = StockBalanceProjection(
                    tenant_id=tenant_id,
                    location_id=transfer.destination_location_id,
                    sku_id=it.sku_id,
                    quantity=Decimal("0"),
                    total_value=Decimal("0"),
                )
                self.session.add(dest_bal)
                await self.session.flush()
                dest_bal = (await self.session.execute(dest_bal_stmt)).scalar_one()

            received_value = qty_rec * unit_cost
            dest_bal.quantity += qty_rec
            dest_bal.total_value += received_value

            in_ledger = StockLedgerEntry(
                tenant_id=tenant_id,
                movement_id=in_movement.id,
                sku_id=it.sku_id,
                quantity=qty_rec,
                unit_cost=unit_cost,
                balance_after=dest_bal.quantity,
            )
            self.session.add(in_ledger)

        transfer.status = "RECEIVED"
        transfer.received_at = now
        await self.session.flush()
        return transfer

    async def reverse_movement(
        self,
        movement_id: UUID,
        tenant_id: UUID,
        actor_user_id: Optional[UUID] = None,
        reason: Optional[str] = None
    ) -> StockMovement:
        """
        Reverses a posted stock movement immutably.
        Domain Invariant: Posted stock movements and ledger entries are never UPDATE'd or DELETE'd.
        A reversal creates a NEW StockMovement of type 'REVERSAL' referencing the original movement,
        with exact opposite ledger entries (quantity = -1 * original_quantity, preserving unit_cost).
        """
        now = datetime.now(timezone.utc)
        await self._guard_accounting_period(tenant_id, now)

        # 1. Lock and validate original movement
        stmt = select(StockMovement).where(
            StockMovement.id == movement_id,
            StockMovement.tenant_id == tenant_id
        ).with_for_update()
        original_mov = (await self.session.execute(stmt)).scalar_one_or_none()

        if not original_mov:
            raise ValueError(f"StockMovement {movement_id} not found.")

        if original_mov.status != 'POSTED':
            raise ValueError(f"Cannot reverse movement with status '{original_mov.status}'. Only POSTED movements can be reversed.")

        if original_mov.type == 'REVERSAL':
            raise ValueError("Cannot reverse a movement that is already a reversal.")

        # 2. Fetch original ledger entries
        stmt_entries = select(StockLedgerEntry).where(
            StockLedgerEntry.movement_id == movement_id,
            StockLedgerEntry.tenant_id == tenant_id
        )
        original_entries = (await self.session.execute(stmt_entries)).scalars().all()

        if not original_entries:
            raise ValueError(f"No ledger entries found for StockMovement {movement_id}.")

        # 3. Create reversal StockMovement
        reversal_movement = StockMovement(
            tenant_id=tenant_id,
            location_id=original_mov.location_id,
            type='REVERSAL',
            status='POSTED',
            reference_id=original_mov.id,
            reference_type='StockMovement',
            actor_user_id=actor_user_id,
            reason_code=reason or "MOVEMENT_REVERSAL",
            notes=f"Reversal of {original_mov.type} movement {original_mov.id}. Reason: {reason or 'Not specified'}",
            posted_at=now
        )
        self.session.add(reversal_movement)
        await self.session.flush()

        # 4. Create opposite ledger entries and update balance projections
        for entry in original_entries:
            rev_qty = Decimal(str(entry.quantity)) * Decimal("-1")
            
            # Lock balance projection
            stmt_bal = select(StockBalanceProjection).where(
                StockBalanceProjection.sku_id == entry.sku_id,
                StockBalanceProjection.location_id == original_mov.location_id,
                StockBalanceProjection.tenant_id == tenant_id
            ).with_for_update()
            balance = (await self.session.execute(stmt_bal)).scalar_one_or_none()

            if not balance:
                balance = StockBalanceProjection(
                    tenant_id=tenant_id,
                    location_id=original_mov.location_id,
                    sku_id=entry.sku_id,
                    quantity=Decimal('0'),
                    total_value=Decimal('0')
                )
                self.session.add(balance)
                await self.session.flush()
                balance = (await self.session.execute(stmt_bal)).scalar_one()

            entry_unit_cost = Decimal(str(entry.unit_cost)) if entry.unit_cost is not None else Decimal('0')
            rev_value = rev_qty * entry_unit_cost

            balance.quantity += rev_qty
            balance.total_value += rev_value

            # Create reversed ledger entry
            rev_ledger_entry = StockLedgerEntry(
                tenant_id=tenant_id,
                movement_id=reversal_movement.id,
                sku_id=entry.sku_id,
                quantity=rev_qty,
                unit_cost=entry.unit_cost,
                conversion_version_id=entry.conversion_version_id,
                balance_after=balance.quantity
            )
            self.session.add(rev_ledger_entry)

        # 5. Update original movement status to REVERSED
        original_mov.status = 'REVERSED'

        # 6. Audit log
        from packages.audit.service import AuditService
        await AuditService.log_action(
            db=self.session,
            tenant_id=tenant_id,
            actor_id=actor_user_id or reversal_movement.id,
            action="STOCK_MOVEMENT_REVERSED",
            resource_type="stock_movements",
            resource_id=reversal_movement.id,
            changes_payload={
                "original_movement_id": str(original_mov.id),
                "original_type": original_mov.type,
                "reversal_movement_id": str(reversal_movement.id),
                "reason": reason
            }
        )

        return reversal_movement

    async def calculate_theoretical_stock_by_sku(
        self,
        tenant_id: UUID,
        location_id: Optional[UUID] = None,
        as_of_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculates theoretical perpetual inventory vs actual physical stock by SKU.
        Formula:
          Theoretical Stock = Physical Ledger Net Movements - Theoretical Consumption from Recipe Sales.
          Variance Quantity = Actual Physical Stock - Theoretical Stock.
          Variance Value = Variance Quantity * Current Unit Cost.
        """
        from modules.inventory.models import TheoreticalConsumption
        from modules.catalog.models import SKU, UOM, Category
        from modules.costing.engine import CostingEngine

        # 1. Fetch SKUs
        stmt_skus = select(SKU, UOM, Category).join(UOM, SKU.base_uom_id == UOM.id).outerjoin(Category, SKU.category_id == Category.id).where(
            SKU.tenant_id == tenant_id,
            SKU.is_active == True
        ).order_by(SKU.name.asc())
        sku_rows = (await self.session.execute(stmt_skus)).all()

        results = []
        for sku, uom, cat in sku_rows:
            # Physical ledger net movements
            stmt_ledger = select(func.coalesce(func.sum(StockLedgerEntry.quantity), 0)).select_from(StockLedgerEntry).join(
                StockMovement, StockLedgerEntry.movement_id == StockMovement.id
            ).where(
                StockLedgerEntry.tenant_id == tenant_id,
                StockLedgerEntry.sku_id == sku.id
            )
            if location_id:
                stmt_ledger = stmt_ledger.where(StockMovement.location_id == location_id)
            if as_of_date:
                stmt_ledger = stmt_ledger.where(StockMovement.posted_at <= as_of_date)

            ledger_qty = Decimal(str((await self.session.execute(stmt_ledger)).scalar_one()))

            # Theoretical consumption from sales
            stmt_theo = select(func.coalesce(func.sum(TheoreticalConsumption.quantity), 0)).where(
                TheoreticalConsumption.tenant_id == tenant_id,
                TheoreticalConsumption.sku_id == sku.id
            )
            if as_of_date:
                stmt_theo = stmt_theo.where(TheoreticalConsumption.created_at <= as_of_date)

            theo_consumed_qty = Decimal(str((await self.session.execute(stmt_theo)).scalar_one()))

            theoretical_qty = ledger_qty - theo_consumed_qty

            # Actual live balance projection
            stmt_bal = select(
                func.coalesce(func.sum(StockBalanceProjection.quantity), 0),
                func.coalesce(func.sum(StockBalanceProjection.total_value), 0)
            ).where(
                StockBalanceProjection.tenant_id == tenant_id,
                StockBalanceProjection.sku_id == sku.id
            )
            if location_id:
                stmt_bal = stmt_bal.where(StockBalanceProjection.location_id == location_id)

            actual_bal_row = (await self.session.execute(stmt_bal)).one()
            actual_qty = Decimal(str(actual_bal_row[0]))

            unit_cost = await CostingEngine.get_sku_cost(self.session, tenant_id, sku.id)

            variance_qty = actual_qty - theoretical_qty
            variance_value = variance_qty * unit_cost

            results.append({
                "sku_id": str(sku.id),
                "sku_name": sku.name,
                "category_name": cat.name if cat else "Uncategorized",
                "uom_symbol": uom.symbol,
                "actual_quantity": float(actual_qty),
                "theoretical_quantity": float(theoretical_qty),
                "theoretical_consumption": float(theo_consumed_qty),
                "variance_quantity": float(variance_qty),
                "unit_cost": float(unit_cost),
                "variance_value": float(variance_value),
                "status": "BALANCED" if variance_qty == Decimal("0") else ("EXCESS" if variance_qty > Decimal("0") else "SHORTAGE")
            })

        return results

