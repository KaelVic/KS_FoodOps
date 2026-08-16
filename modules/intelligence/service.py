from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case, text, desc
from decimal import Decimal

from modules.intelligence.models import InventoryPolicy, PurchaseSuggestion, OperationalAlert
from modules.inventory.models import StockBalanceProjection, StockLedgerEntry
from modules.catalog.models import SKU
from modules.purchasing.models import PurchaseOrderLine, PurchaseOrder, SupplierInvoiceLine, GoodsReceiptLine

class IntelligenceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_abc_classification(self, tenant_id: UUID, location_id: UUID, days_history: int = 30) -> None:
        """
        Calculates ABC classification based on consumption value over the last N days.
        Top 80% = A, Next 15% = B, Bottom 5% = C.
        Consumption is represented by negative quantity in stock ledger for LOSS or CONSUMPTION (or SALES).
        For simplicity, we'll look at negative stock ledger entries that are not transfers or reversals.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_history)
        
        # 1. Aggregate consumption value per SKU
        stmt = select(
            StockLedgerEntry.sku_id,
            func.sum(func.abs(StockLedgerEntry.quantity) * StockLedgerEntry.unit_cost).label('total_value')
        ).join(
            StockBalanceProjection, 
            (StockBalanceProjection.sku_id == StockLedgerEntry.sku_id) & 
            (StockBalanceProjection.tenant_id == StockLedgerEntry.tenant_id)
        ).where(
            StockLedgerEntry.tenant_id == tenant_id,
            StockBalanceProjection.location_id == location_id,
            StockLedgerEntry.quantity < 0,
            StockLedgerEntry.created_at >= cutoff_date
        ).group_by(StockLedgerEntry.sku_id)
        
        results = (await self.session.execute(stmt)).all()
        
        if not results:
            return
            
        # 2. Sort and calculate cumulative percentages
        # We need a list of dicts to sort in memory
        sku_values = [{'sku_id': r.sku_id, 'value': r.total_value or Decimal(0)} for r in results]
        sku_values.sort(key=lambda x: x['value'], reverse=True)
        
        total_consumption = sum(x['value'] for x in sku_values)
        if total_consumption == 0:
            return
            
        cumulative_value = Decimal(0)
        
        for item in sku_values:
            percentage_before = cumulative_value / total_consumption
            
            if percentage_before < Decimal('0.80'):
                abc = 'A'
            elif percentage_before < Decimal('0.95'):
                abc = 'B'
            else:
                abc = 'C'
                
            cumulative_value += item['value']
                
            # 3. Upsert InventoryPolicy
            stmt_policy = select(InventoryPolicy).where(
                InventoryPolicy.tenant_id == tenant_id,
                InventoryPolicy.location_id == location_id,
                InventoryPolicy.sku_id == item['sku_id']
            )
            policy = (await self.session.execute(stmt_policy)).scalar_one_or_none()
            
            if policy:
                policy.abc_class = abc
            else:
                policy = InventoryPolicy(
                    tenant_id=tenant_id,
                    location_id=location_id,
                    sku_id=item['sku_id'],
                    abc_class=abc
                )
                self.session.add(policy)
                
        await self.session.flush()

    async def generate_purchase_suggestions(self, tenant_id: UUID, location_id: UUID) -> List[PurchaseSuggestion]:
        """
        Generates deterministic purchase suggestions based on:
        Suggested Qty = Target Stock - On Hand - Expected Inbound (Approved PO lines not yet received)
        """
        # Get policies with targets > 0
        stmt = select(InventoryPolicy).where(
            InventoryPolicy.tenant_id == tenant_id,
            InventoryPolicy.location_id == location_id,
            InventoryPolicy.target_stock > 0
        )
        policies = (await self.session.execute(stmt)).scalars().all()
        
        generated = []
        for policy in policies:
            # 1. On Hand
            stmt_stock = select(StockBalanceProjection.quantity).where(
                StockBalanceProjection.tenant_id == tenant_id,
                StockBalanceProjection.location_id == location_id,
                StockBalanceProjection.sku_id == policy.sku_id
            )
            on_hand = (await self.session.execute(stmt_stock)).scalar_one_or_none() or Decimal(0)
            
            # 2. Expected Inbound (from Purchase Orders)
            stmt_po_lines = select(PurchaseOrderLine.id, PurchaseOrderLine.ordered_quantity).join(
                PurchaseOrder, PurchaseOrder.id == PurchaseOrderLine.purchase_order_id
            ).where(
                PurchaseOrderLine.tenant_id == tenant_id,
                PurchaseOrderLine.sku_id == policy.sku_id,
                PurchaseOrder.status.in_(['approved', 'sent', 'partial_receipt'])
            )
            po_lines_result = (await self.session.execute(stmt_po_lines)).all()
            
            inbound = Decimal(0)
            if po_lines_result:
                for row in po_lines_result:
                    stmt_rec = select(func.sum(GoodsReceiptLine.quantity)).where(
                        GoodsReceiptLine.tenant_id == tenant_id,
                        GoodsReceiptLine.purchase_order_line_id == row.id
                    )
                    received_qty = (await self.session.execute(stmt_rec)).scalar_one_or_none() or Decimal(0)
                    if row.ordered_quantity > received_qty:
                        inbound += (row.ordered_quantity - received_qty)
                        
            suggested = policy.target_stock - on_hand - inbound
            
            if suggested > 0:
                # Upsert suggestion
                stmt_sugg = select(PurchaseSuggestion).where(
                    PurchaseSuggestion.tenant_id == tenant_id,
                    PurchaseSuggestion.location_id == location_id,
                    PurchaseSuggestion.sku_id == policy.sku_id,
                    PurchaseSuggestion.status == 'PENDING'
                )
                existing = (await self.session.execute(stmt_sugg)).scalar_one_or_none()
                
                reason = f"Target({policy.target_stock}) - OnHand({on_hand}) - Inbound({inbound}) = {suggested}"
                if existing:
                    existing.suggested_quantity = suggested
                    existing.reason = reason
                    generated.append(existing)
                else:
                    new_sugg = PurchaseSuggestion(
                        tenant_id=tenant_id,
                        location_id=location_id,
                        sku_id=policy.sku_id,
                        suggested_quantity=suggested,
                        reason=reason
                    )
                    self.session.add(new_sugg)
                    generated.append(new_sugg)
                    
        await self.session.flush()
        return generated

    async def generate_operational_alerts(self, tenant_id: UUID, location_id: UUID) -> List[OperationalAlert]:
        """
        Generates alerts for stockouts (On Hand < Reorder Point).
        ROP = (Daily Baseline * Lead Time) + Min Stock.
        For Phase 7, we'll approximate Daily Baseline by dividing the last 30 days consumption by 30.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        stmt = select(InventoryPolicy).where(
            InventoryPolicy.tenant_id == tenant_id,
            InventoryPolicy.location_id == location_id
        )
        policies = (await self.session.execute(stmt)).scalars().all()
        
        alerts = []
        for policy in policies:
            # On Hand
            stmt_stock = select(StockBalanceProjection.quantity).where(
                StockBalanceProjection.tenant_id == tenant_id,
                StockBalanceProjection.location_id == location_id,
                StockBalanceProjection.sku_id == policy.sku_id
            )
            on_hand = (await self.session.execute(stmt_stock)).scalar_one_or_none() or Decimal(0)
            
            # Daily Baseline (Average over 30 days)
            stmt_cons = select(func.sum(func.abs(StockLedgerEntry.quantity))).join(
                StockBalanceProjection, 
                (StockBalanceProjection.sku_id == StockLedgerEntry.sku_id) & 
                (StockBalanceProjection.tenant_id == StockLedgerEntry.tenant_id)
            ).where(
                StockLedgerEntry.tenant_id == tenant_id,
                StockBalanceProjection.location_id == location_id,
                StockLedgerEntry.quantity < 0,
                StockLedgerEntry.created_at >= cutoff_date,
                StockLedgerEntry.sku_id == policy.sku_id
            )
            monthly_consumption = (await self.session.execute(stmt_cons)).scalar_one_or_none() or Decimal(0)
            daily_baseline = monthly_consumption / Decimal(30)
            
            # Reorder Point
            rop = (daily_baseline * Decimal(policy.lead_time_days)) + policy.min_stock
            
            if on_hand < rop:
                # Avoid duplicates
                stmt_alert = select(OperationalAlert).where(
                    OperationalAlert.tenant_id == tenant_id,
                    OperationalAlert.location_id == location_id,
                    OperationalAlert.sku_id == policy.sku_id,
                    OperationalAlert.metric == 'STOCKOUT_RISK',
                    OperationalAlert.is_resolved == False
                )
                existing = (await self.session.execute(stmt_alert)).scalar_one_or_none()
                if not existing:
                    alert = OperationalAlert(
                        tenant_id=tenant_id,
                        location_id=location_id,
                        sku_id=policy.sku_id,
                        metric='STOCKOUT_RISK',
                        observed_value=on_hand,
                        reference_value=rop,
                        threshold=rop,
                        reason=f"On Hand ({on_hand}) is below ROP ({rop})"
                    )
                    self.session.add(alert)
                    alerts.append(alert)
                    
        await self.session.flush()
        return alerts

    async def check_purchase_price_variation(self, tenant_id: UUID, invoice_id: UUID) -> List[OperationalAlert]:
        """
        Check if the unit price on a SupplierInvoiceLine exceeds the historical average cost 
        (e.g., from StockLedgerEntry) by more than 10%.
        """
        stmt = select(SupplierInvoiceLine).where(
            SupplierInvoiceLine.tenant_id == tenant_id,
            SupplierInvoiceLine.invoice_id == invoice_id
        )
        lines = (await self.session.execute(stmt)).scalars().all()
        
        alerts = []
        for line in lines:
            if not line.sku_id:
                continue
                
            # Get latest moving average cost from stock ledger before this invoice (simplification: just get the latest unit_cost)
            # A true MA cost would look at balance value / quantity. 
            # We'll just look at the last positive receipt cost.
            stmt_hist = select(StockLedgerEntry.unit_cost).where(
                StockLedgerEntry.tenant_id == tenant_id,
                StockLedgerEntry.sku_id == line.sku_id,
                StockLedgerEntry.quantity > 0,
                StockLedgerEntry.unit_cost != None
            ).order_by(desc(StockLedgerEntry.created_at)).limit(1)
            
            last_cost = (await self.session.execute(stmt_hist)).scalar_one_or_none()
            
            if last_cost and last_cost > 0:
                variance = (line.unit_price - last_cost) / last_cost
                if variance > Decimal('0.10'): # 10% threshold
                    alert = OperationalAlert(
                        tenant_id=tenant_id,
                        location_id=None, # Price variance might not be location-specific if purchasing is central
                        sku_id=line.sku_id,
                        metric='PRICE_VARIANCE',
                        observed_value=line.unit_price,
                        reference_value=last_cost,
                        threshold=Decimal('0.10'),
                        reason=f"Invoice price ({line.unit_price}) is >10% higher than last cost ({last_cost}). Variance: {variance*100:.1f}%"
                    )
                    self.session.add(alert)
                    alerts.append(alert)
                    
        await self.session.flush()
        return alerts
