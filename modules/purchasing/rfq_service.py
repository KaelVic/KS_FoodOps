import uuid
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from modules.purchasing.models import (
    RFQ, RFQItem, RFQSupplier, RFQProposal, RFQProposalItem,
    PurchaseOrder, PurchaseOrderLine
)
from modules.catalog.models import SKU, UOM
from modules.suppliers.models import Supplier


class RFQService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rfq(
        self,
        tenant_id: UUID,
        title: str,
        location_id: Optional[UUID],
        deadline: Optional[datetime],
        notes: Optional[str],
        items: List[Dict[str, Any]],
        supplier_ids: Optional[List[UUID]] = None
    ) -> RFQ:
        # Generate RFQ number: RFQ-YYYYMMDD-XXXX
        now = datetime.now(timezone.utc)
        rfq_count_stmt = select(RFQ).where(RFQ.tenant_id == tenant_id)
        existing_rfqs = (await self.db.execute(rfq_count_stmt)).scalars().all()
        seq_num = len(existing_rfqs) + 1
        rfq_number = f"RFQ-{now.strftime('%Y%m')}-{seq_num:04d}"


        rfq = RFQ(
            tenant_id=tenant_id,
            rfq_number=rfq_number,
            title=title,
            location_id=location_id,
            status="OPEN" if supplier_ids else "DRAFT",
            deadline=deadline,
            notes=notes
        )
        self.db.add(rfq)
        await self.db.flush()

        # Add RFQ items
        for item_data in items:
            rfq_item = RFQItem(
                tenant_id=tenant_id,
                rfq_id=rfq.id,
                sku_id=item_data["sku_id"],
                quantity=Decimal(str(item_data["quantity"])),
                target_price=Decimal(str(item_data["target_price"])) if item_data.get("target_price") is not None else None
            )
            self.db.add(rfq_item)

        # Invite suppliers if provided
        if supplier_ids:
            for supp_id in supplier_ids:
                rfq_supp = RFQSupplier(
                    tenant_id=tenant_id,
                    rfq_id=rfq.id,
                    supplier_id=supp_id,
                    status="INVITED"
                )
                self.db.add(rfq_supp)

        await self.db.commit()
        return rfq

    async def add_suppliers(
        self,
        tenant_id: UUID,
        rfq_id: UUID,
        supplier_ids: List[UUID]
    ) -> List[RFQSupplier]:
        rfq_stmt = select(RFQ).where(RFQ.id == rfq_id, RFQ.tenant_id == tenant_id)
        rfq = (await self.db.execute(rfq_stmt)).scalar_one_or_none()
        if not rfq:
            raise ValueError("RFQ não encontrada")

        added = []
        for supp_id in supplier_ids:
            # check if already invited
            check_stmt = select(RFQSupplier).where(
                RFQSupplier.rfq_id == rfq_id,
                RFQSupplier.supplier_id == supp_id,
                RFQSupplier.tenant_id == tenant_id
            )
            existing = (await self.db.execute(check_stmt)).scalar_one_or_none()
            if not existing:
                supp = RFQSupplier(
                    tenant_id=tenant_id,
                    rfq_id=rfq_id,
                    supplier_id=supp_id,
                    status="INVITED"
                )
                self.db.add(supp)
                added.append(supp)

        if rfq.status == "DRAFT":
            rfq.status = "OPEN"

        await self.db.commit()
        return added

    async def submit_proposal(
        self,
        tenant_id: UUID,
        rfq_id: UUID,
        supplier_id: UUID,
        freight_cost: Decimal,
        delivery_days: str,
        payment_terms: Optional[str],
        min_order_value: Decimal,
        notes: Optional[str],
        item_prices: List[Dict[str, Any]]
    ) -> RFQProposal:
        rfq_stmt = select(RFQ).where(RFQ.id == rfq_id, RFQ.tenant_id == tenant_id)
        rfq = (await self.db.execute(rfq_stmt)).scalar_one_or_none()
        if not rfq:
            raise ValueError("RFQ não encontrada")

        # Check or create supplier invitation
        supp_stmt = select(RFQSupplier).where(
            RFQSupplier.rfq_id == rfq_id,
            RFQSupplier.supplier_id == supplier_id,
            RFQSupplier.tenant_id == tenant_id
        )
        rfq_supp = (await self.db.execute(supp_stmt)).scalar_one_or_none()
        if not rfq_supp:
            rfq_supp = RFQSupplier(
                tenant_id=tenant_id,
                rfq_id=rfq_id,
                supplier_id=supplier_id,
                status="SUBMITTED"
            )
            self.db.add(rfq_supp)
        else:
            rfq_supp.status = "SUBMITTED"

        # Check if proposal exists already for this supplier
        prop_stmt = select(RFQProposal).where(
            RFQProposal.rfq_id == rfq_id,
            RFQProposal.supplier_id == supplier_id,
            RFQProposal.tenant_id == tenant_id
        )
        proposal = (await self.db.execute(prop_stmt)).scalar_one_or_none()

        if proposal:
            proposal.freight_cost = freight_cost
            proposal.delivery_days = str(delivery_days)
            proposal.payment_terms = payment_terms
            proposal.min_order_value = min_order_value
            proposal.notes = notes
            proposal.submitted_at = datetime.utcnow()
            # Delete old proposal items
            del_stmt = select(RFQProposalItem).where(RFQProposalItem.proposal_id == proposal.id)
            old_items = (await self.db.execute(del_stmt)).scalars().all()
            for oi in old_items:
                await self.db.delete(oi)
            await self.db.flush()
        else:
            proposal = RFQProposal(
                tenant_id=tenant_id,
                rfq_id=rfq_id,
                supplier_id=supplier_id,
                freight_cost=freight_cost,
                delivery_days=str(delivery_days),
                payment_terms=payment_terms,
                min_order_value=min_order_value,
                notes=notes
            )
            self.db.add(proposal)
            await self.db.flush()

        # Add proposal items
        for p_item in item_prices:
            rfq_p_item = RFQProposalItem(
                tenant_id=tenant_id,
                proposal_id=proposal.id,
                rfq_item_id=p_item["rfq_item_id"],
                unit_price=Decimal(str(p_item["unit_price"])),
                available_quantity=Decimal(str(p_item["available_quantity"])) if p_item.get("available_quantity") is not None else None,
                brand_or_spec=p_item.get("brand_or_spec")
            )
            self.db.add(rfq_p_item)

        if rfq.status in ["OPEN", "DRAFT"]:
            rfq.status = "EVALUATING"

        await self.db.commit()
        return proposal

    async def get_comparison_matrix(
        self,
        tenant_id: UUID,
        rfq_id: UUID
    ) -> Dict[str, Any]:
        rfq_stmt = select(RFQ).where(RFQ.id == rfq_id, RFQ.tenant_id == tenant_id)
        rfq = (await self.db.execute(rfq_stmt)).scalar_one_or_none()
        if not rfq:
            raise ValueError("RFQ não encontrada")

        # Load RFQ Items with SKU and UOM
        items_stmt = (
            select(RFQItem, SKU, UOM)
            .join(SKU, RFQItem.sku_id == SKU.id)
            .join(UOM, SKU.base_uom_id == UOM.id)
            .where(RFQItem.rfq_id == rfq_id, RFQItem.tenant_id == tenant_id)
            .order_by(SKU.name.asc())
        )
        items_res = (await self.db.execute(items_stmt)).all()

        # Load Proposals with Supplier
        props_stmt = (
            select(RFQProposal, Supplier)
            .join(Supplier, RFQProposal.supplier_id == Supplier.id)
            .where(RFQProposal.rfq_id == rfq_id, RFQProposal.tenant_id == tenant_id)
        )
        props_res = (await self.db.execute(props_stmt)).all()

        # Load All Proposal Items
        prop_items_stmt = (
            select(RFQProposalItem)
            .where(RFQProposalItem.tenant_id == tenant_id)
            .join(RFQProposal, RFQProposalItem.proposal_id == RFQProposal.id)
            .where(RFQProposal.rfq_id == rfq_id)
        )
        prop_items = (await self.db.execute(prop_items_stmt)).scalars().all()
        # Map: (proposal_id, rfq_item_id) -> proposal_item
        prop_item_map = {(pi.proposal_id, pi.rfq_item_id): pi for pi in prop_items}

        suppliers_data = []
        for prop, supp in props_res:
            suppliers_data.append({
                "supplier_id": supp.id,
                "supplier_name": supp.name,
                "proposal_id": prop.id,
                "freight_cost": prop.freight_cost,
                "delivery_days": prop.delivery_days,
                "payment_terms": prop.payment_terms,
                "min_order_value": prop.min_order_value,
                "submitted_at": prop.submitted_at
            })

        matrix_items = []
        split_order_total = Decimal("0")
        target_grand_total = Decimal("0")

        supplier_totals: Dict[UUID, Decimal] = {s["supplier_id"]: Decimal(str(s["freight_cost"])) for s in suppliers_data}

        for rfq_item, sku, uom in items_res:
            item_qty = rfq_item.quantity
            target_p = rfq_item.target_price or Decimal("0")
            target_total = target_p * item_qty
            target_grand_total += target_total

            item_quotes = []
            lowest_price = None
            best_supplier_id = None
            best_supplier_name = None

            for s in suppliers_data:
                p_item = prop_item_map.get((s["proposal_id"], rfq_item.id))
                if p_item:
                    u_price = p_item.unit_price
                    total_price = u_price * item_qty
                    supplier_totals[s["supplier_id"]] += total_price

                    if lowest_price is None or u_price < lowest_price:
                        lowest_price = u_price
                        best_supplier_id = s["supplier_id"]
                        best_supplier_name = s["supplier_name"]

                    item_quotes.append({
                        "supplier_id": s["supplier_id"],
                        "supplier_name": s["supplier_name"],
                        "unit_price": u_price,
                        "total_price": total_price,
                        "available_quantity": p_item.available_quantity,
                        "brand_or_spec": p_item.brand_or_spec
                    })
                else:
                    item_quotes.append({
                        "supplier_id": s["supplier_id"],
                        "supplier_name": s["supplier_name"],
                        "unit_price": None,
                        "total_price": None,
                        "available_quantity": None,
                        "brand_or_spec": None
                    })

            if lowest_price is not None:
                split_order_total += (lowest_price * item_qty)

            matrix_items.append({
                "rfq_item_id": rfq_item.id,
                "sku_id": sku.id,
                "sku_name": sku.name,
                "uom_symbol": uom.symbol,
                "quantity": item_qty,
                "target_price": rfq_item.target_price,
                "target_total": target_total,
                "quotes": item_quotes,
                "best_price": lowest_price,
                "best_supplier_id": best_supplier_id,
                "best_supplier_name": best_supplier_name
            })

        # Find best global single supplier
        best_global_supplier_id = None
        best_global_total = None
        global_rankings = []
        for s in suppliers_data:
            s_id = s["supplier_id"]
            tot = supplier_totals[s_id]
            global_rankings.append({
                "supplier_id": s_id,
                "supplier_name": s["supplier_name"],
                "total_with_freight": tot,
                "freight_cost": s["freight_cost"],
                "delivery_days": s["delivery_days"],
                "payment_terms": s["payment_terms"],
                "min_order_value": s["min_order_value"],
                "meets_min_order": tot >= s["min_order_value"]
            })
            if best_global_total is None or tot < best_global_total:
                best_global_total = tot
                best_global_supplier_id = s_id

        # Calculate estimated savings
        potential_savings = None
        if target_grand_total > Decimal("0") and split_order_total > Decimal("0"):
            potential_savings = target_grand_total - split_order_total

        return {
            "rfq_id": rfq.id,
            "rfq_number": rfq.rfq_number,
            "title": rfq.title,
            "status": rfq.status,
            "location_id": rfq.location_id,
            "suppliers": suppliers_data,
            "items": matrix_items,
            "split_order_total": split_order_total,
            "target_grand_total": target_grand_total,
            "potential_savings": potential_savings,
            "best_global_supplier_id": best_global_supplier_id,
            "best_global_total": best_global_total,
            "global_rankings": global_rankings
        }

    async def award_rfq(
        self,
        tenant_id: UUID,
        rfq_id: UUID,
        award_type: str = "SPLIT", # "SPLIT" or "SINGLE_SUPPLIER"
        selected_supplier_id: Optional[UUID] = None
    ) -> List[UUID]:
        rfq_stmt = select(RFQ).where(RFQ.id == rfq_id, RFQ.tenant_id == tenant_id)
        rfq = (await self.db.execute(rfq_stmt)).scalar_one_or_none()
        if not rfq:
            raise ValueError("RFQ não encontrada")

        if rfq.status == "AWARDED":
            raise ValueError("Esta cotação já foi homologada e convertida em Pedidos de Compra.")

        comp = await self.get_comparison_matrix(tenant_id, rfq_id)
        created_po_ids = []

        if award_type == "SINGLE_SUPPLIER":
            supp_id = selected_supplier_id or comp["best_global_supplier_id"]
            if not supp_id:
                raise ValueError("Nenhum fornecedor selecionado ou válido para pedido único.")

            # Group items for this supplier
            po = PurchaseOrder(
                tenant_id=tenant_id,
                supplier_id=supp_id,
                location_id=rfq.location_id or (await self._get_fallback_location(tenant_id)),
                status="APPROVED"
            )
            self.db.add(po)
            await self.db.flush()
            created_po_ids.append(po.id)

            for item in comp["items"]:
                for q in item["quotes"]:
                    if q["supplier_id"] == supp_id and q["unit_price"] is not None:
                        po_line = PurchaseOrderLine(
                            tenant_id=tenant_id,
                            purchase_order_id=po.id,
                            sku_id=item["sku_id"],
                            ordered_quantity=item["quantity"],
                            unit_price=q["unit_price"]
                        )
                        self.db.add(po_line)

        else: # SPLIT order (lowest price per item)
            # Group items by best_supplier_id
            supplier_items_map: Dict[UUID, List[Dict[str, Any]]] = {}
            for item in comp["items"]:
                if item["best_supplier_id"] and item["best_price"] is not None:
                    supp_id = item["best_supplier_id"]
                    if supp_id not in supplier_items_map:
                        supplier_items_map[supp_id] = []
                    supplier_items_map[supp_id].append(item)

            if not supplier_items_map:
                raise ValueError("Nenhum item cotado com fornecedor vencedor.")

            fallback_loc = rfq.location_id or (await self._get_fallback_location(tenant_id))

            for supp_id, itms in supplier_items_map.items():
                po = PurchaseOrder(
                    tenant_id=tenant_id,
                    supplier_id=supp_id,
                    location_id=fallback_loc,
                    status="APPROVED"
                )
                self.db.add(po)
                await self.db.flush()
                created_po_ids.append(po.id)

                for item in itms:
                    po_line = PurchaseOrderLine(
                        tenant_id=tenant_id,
                        purchase_order_id=po.id,
                        sku_id=item["sku_id"],
                        ordered_quantity=item["quantity"],
                        unit_price=item["best_price"]
                    )
                    self.db.add(po_line)

        rfq.status = "AWARDED"
        await self.db.commit()
        return created_po_ids

    async def _get_fallback_location(self, tenant_id: UUID) -> UUID:
        from modules.inventory.models import Location
        loc_stmt = select(Location).where(Location.tenant_id == tenant_id).limit(1)
        loc = (await self.db.execute(loc_stmt)).scalar_one_or_none()
        if not loc:
            raise ValueError("Nenhum local cadastrado para o tenant.")
        return loc.id
