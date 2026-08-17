import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.orders.models import DiningTable, Order, OrderItem
from modules.menu.models import MenuItem, MenuCategory
from modules.financial.models import ReceivableInvoice, ReceivableInstallment, ReceivableSettlement, PaymentAcquirer, BankAccount


class OrderService:

    # -------------------------------------------------------------
    # DINING TABLES (Salão / Mesas)
    # -------------------------------------------------------------
    @staticmethod
    async def list_tables(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        section: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        stmt = select(DiningTable).where(DiningTable.tenant_id == tenant_id)
        if section and section != "ALL":
            stmt = stmt.where(DiningTable.section == section)
        if status and status != "ALL":
            stmt = stmt.where(DiningTable.status == status)
        stmt = stmt.order_by(DiningTable.table_number.asc())

        tables = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(t.id),
                "table_number": t.table_number,
                "capacity": t.capacity,
                "section": t.section,
                "status": t.status,
                "active_order_id": str(t.active_order_id) if t.active_order_id else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tables
        ]

    @staticmethod
    async def get_table(session: AsyncSession, tenant_id: uuid.UUID, table_id: uuid.UUID) -> Optional[DiningTable]:
        stmt = select(DiningTable).where(
            DiningTable.tenant_id == tenant_id,
            DiningTable.id == table_id
        )
        return (await session.execute(stmt)).scalars().first()

    @staticmethod
    async def create_table(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        table = DiningTable(
            tenant_id=tenant_id,
            table_number=data["table_number"],
            capacity=data.get("capacity", 4),
            section=data.get("section", "Salão Principal"),
            status=data.get("status", "AVAILABLE")
        )
        session.add(table)
        await session.flush()
        return {
            "id": str(table.id),
            "table_number": table.table_number,
            "capacity": table.capacity,
            "section": table.section,
            "status": table.status,
            "active_order_id": None,
            "created_at": table.created_at.isoformat() if table.created_at else None,
            "updated_at": table.updated_at.isoformat() if table.updated_at else None,
        }

    @staticmethod
    async def update_table(session: AsyncSession, tenant_id: uuid.UUID, table_id: uuid.UUID, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        table = await OrderService.get_table(session, tenant_id, table_id)
        if not table:
            return None
        if "table_number" in data:
            table.table_number = data["table_number"]
        if "capacity" in data:
            table.capacity = data["capacity"]
        if "section" in data:
            table.section = data["section"]
        if "status" in data:
            table.status = data["status"]
        await session.flush()
        return {
            "id": str(table.id),
            "table_number": table.table_number,
            "capacity": table.capacity,
            "section": table.section,
            "status": table.status,
            "active_order_id": str(table.active_order_id) if table.active_order_id else None,
            "created_at": table.created_at.isoformat() if table.created_at else None,
            "updated_at": table.updated_at.isoformat() if table.updated_at else None,
        }

    @staticmethod
    async def update_table_status(session: AsyncSession, tenant_id: uuid.UUID, table_id: uuid.UUID, status: str) -> Optional[Dict[str, Any]]:
        table = await OrderService.get_table(session, tenant_id, table_id)
        if not table:
            return None
        table.status = status
        if status == "AVAILABLE":
            table.active_order_id = None
        await session.flush()
        return {
            "id": str(table.id),
            "table_number": table.table_number,
            "capacity": table.capacity,
            "section": table.section,
            "status": table.status,
            "active_order_id": str(table.active_order_id) if table.active_order_id else None,
            "created_at": table.created_at.isoformat() if table.created_at else None,
            "updated_at": table.updated_at.isoformat() if table.updated_at else None,
        }

    # -------------------------------------------------------------
    # ORDERS & COMANDAS
    # -------------------------------------------------------------
    @staticmethod
    async def list_orders(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        is_paid: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        stmt = select(Order).where(Order.tenant_id == tenant_id)
        if channel and channel != "ALL":
            stmt = stmt.where(Order.channel == channel)
        if status and status != "ALL":
            stmt = stmt.where(Order.status == status)
        if is_paid is not None:
            stmt = stmt.where(Order.is_paid == is_paid)
        stmt = stmt.order_by(desc(Order.created_at)).limit(limit)

        orders = (await session.execute(stmt)).scalars().all()
        res = []
        for o in orders:
            # fetch items
            items_stmt = select(OrderItem).where(OrderItem.order_id == o.id)
            items = (await session.execute(items_stmt)).scalars().all()
            res.append({
                "id": str(o.id),
                "order_number": o.order_number,
                "channel": o.channel,
                "status": o.status,
                "table_id": str(o.table_id) if o.table_id else None,
                "customer_name": o.customer_name,
                "customer_phone": o.customer_phone,
                "delivery_address": o.delivery_address,
                "waiter_name": o.waiter_name,
                "subtotal": float(o.subtotal),
                "delivery_fee": float(o.delivery_fee),
                "discount_amount": float(o.discount_amount),
                "total_amount": float(o.total_amount),
                "notes": o.notes,
                "payment_method": o.payment_method,
                "is_paid": o.is_paid,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "items": [
                    {
                        "id": str(i.id),
                        "menu_item_id": str(i.menu_item_id) if i.menu_item_id else None,
                        "name": i.name,
                        "quantity": float(i.quantity),
                        "unit_price": float(i.unit_price),
                        "total_price": float(i.total_price),
                        "preparation_notes": i.preparation_notes,
                        "production_station": i.production_station,
                        "status": i.status,
                        "started_at": i.started_at.isoformat() if i.started_at else None,
                        "ready_at": i.ready_at.isoformat() if i.ready_at else None,
                        "served_at": i.served_at.isoformat() if i.served_at else None,
                    }
                    for i in items
                ]
            })
        return res

    @staticmethod
    async def get_order_dict(session: AsyncSession, tenant_id: uuid.UUID, order_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        stmt = select(Order).where(Order.tenant_id == tenant_id, Order.id == order_id)
        order = (await session.execute(stmt)).scalars().first()
        if not order:
            return None

        items_stmt = select(OrderItem).where(OrderItem.order_id == order.id)
        items = (await session.execute(items_stmt)).scalars().all()
        return {
            "id": str(order.id),
            "order_number": order.order_number,
            "channel": order.channel,
            "status": order.status,
            "table_id": str(order.table_id) if order.table_id else None,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "waiter_name": order.waiter_name,
            "subtotal": float(order.subtotal),
            "delivery_fee": float(order.delivery_fee),
            "discount_amount": float(order.discount_amount),
            "total_amount": float(order.total_amount),
            "notes": order.notes,
            "payment_method": order.payment_method,
            "is_paid": order.is_paid,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "items": [
                {
                    "id": str(i.id),
                    "menu_item_id": str(i.menu_item_id) if i.menu_item_id else None,
                    "name": i.name,
                    "quantity": float(i.quantity),
                    "unit_price": float(i.unit_price),
                    "total_price": float(i.total_price),
                    "preparation_notes": i.preparation_notes,
                    "production_station": i.production_station,
                    "status": i.status,
                    "started_at": i.started_at.isoformat() if i.started_at else None,
                    "ready_at": i.ready_at.isoformat() if i.ready_at else None,
                    "served_at": i.served_at.isoformat() if i.served_at else None,
                }
                for i in items
            ]
        }

    @staticmethod
    async def create_order(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        count_stmt = select(func.count(Order.id)).where(Order.tenant_id == tenant_id)
        count = (await session.execute(count_stmt)).scalar() or 0
        channel = data.get("channel", "DINE_IN")
        prefix = "CMD" if channel == "DINE_IN" else ("DEL" if channel == "DELIVERY" else "BAL")
        order_number = f"{prefix}-{count + 1:04d}"

        table_id = uuid.UUID(data["table_id"]) if data.get("table_id") else None

        order = Order(
            tenant_id=tenant_id,
            order_number=order_number,
            channel=channel,
            status=data.get("status", "PREPARING" if data.get("items") else "PENDING"),
            table_id=table_id,
            customer_name=data.get("customer_name"),
            customer_phone=data.get("customer_phone"),
            delivery_address=data.get("delivery_address"),
            waiter_name=data.get("waiter_name"),
            delivery_fee=Decimal(str(data.get("delivery_fee", 0))),
            discount_amount=Decimal(str(data.get("discount_amount", 0))),
            notes=data.get("notes"),
            payment_method=data.get("payment_method"),
            is_paid=data.get("is_paid", False)
        )
        session.add(order)
        await session.flush()

        if table_id:
            table = await OrderService.get_table(session, tenant_id, table_id)
            if table:
                table.status = "OCCUPIED"
                table.active_order_id = order.id
                await session.flush()

        subtotal = Decimal("0")
        items_objs = []
        if data.get("items"):
            for it in data["items"]:
                menu_item_id = uuid.UUID(it["menu_item_id"]) if it.get("menu_item_id") else None
                name = it["name"]
                unit_price = Decimal(str(it.get("unit_price", 0)))
                qty = Decimal(str(it.get("quantity", 1)))
                tot = unit_price * qty
                subtotal += tot

                station = it.get("production_station", "KITCHEN")
                if not it.get("production_station") and menu_item_id:
                    m_stmt = select(MenuItem).where(MenuItem.id == menu_item_id)
                    menu_item = (await session.execute(m_stmt)).scalars().first()
                    if menu_item and menu_item.category:
                        cat_name = menu_item.category.name.upper()
                        if "BEBIDA" in cat_name or "DRINK" in cat_name or "BAR" in cat_name or "VINHO" in cat_name or "CHOPP" in cat_name:
                            station = "BAR"
                        elif "SOBREMESA" in cat_name or "DOCE" in cat_name:
                            station = "DESSERT"
                        elif "PIZZA" in cat_name:
                            station = "PIZZERIA"

                item = OrderItem(
                    tenant_id=tenant_id,
                    order_id=order.id,
                    menu_item_id=menu_item_id,
                    name=name,
                    quantity=qty,
                    unit_price=unit_price,
                    total_price=tot,
                    preparation_notes=it.get("preparation_notes"),
                    production_station=station,
                    status=it.get("status", "QUEUED")
                )
                session.add(item)
                items_objs.append(item)

        order.subtotal = subtotal
        order.total_amount = max(Decimal("0"), subtotal + order.delivery_fee - order.discount_amount)
        await session.flush()

        return await OrderService.get_order_dict(session, tenant_id, order.id)

    @staticmethod
    async def add_items_to_order(session: AsyncSession, tenant_id: uuid.UUID, order_id: uuid.UUID, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        stmt = select(Order).where(Order.tenant_id == tenant_id, Order.id == order_id)
        order = (await session.execute(stmt)).scalars().first()
        if not order:
            raise ValueError("Comanda / Pedido não encontrado.")

        subtotal_addition = Decimal("0")
        for it in items_data:
            menu_item_id = uuid.UUID(it["menu_item_id"]) if it.get("menu_item_id") else None
            name = it["name"]
            unit_price = Decimal(str(it.get("unit_price", 0)))
            qty = Decimal(str(it.get("quantity", 1)))
            tot = unit_price * qty
            subtotal_addition += tot

            station = it.get("production_station", "KITCHEN")
            if not it.get("production_station") and menu_item_id:
                m_stmt = select(MenuItem).where(MenuItem.id == menu_item_id)
                menu_item = (await session.execute(m_stmt)).scalars().first()
                if menu_item and menu_item.category:
                    cat_name = menu_item.category.name.upper()
                    if "BEBIDA" in cat_name or "DRINK" in cat_name or "BAR" in cat_name or "VINHO" in cat_name or "CHOPP" in cat_name:
                        station = "BAR"
                    elif "SOBREMESA" in cat_name or "DOCE" in cat_name:
                        station = "DESSERT"
                    elif "PIZZA" in cat_name:
                        station = "PIZZERIA"

            item = OrderItem(
                tenant_id=tenant_id,
                order_id=order.id,
                menu_item_id=menu_item_id,
                name=name,
                quantity=qty,
                unit_price=unit_price,
                total_price=tot,
                preparation_notes=it.get("preparation_notes"),
                production_station=station,
                status="QUEUED"
            )
            session.add(item)

        order.subtotal += subtotal_addition
        order.total_amount = max(Decimal("0"), order.subtotal + order.delivery_fee - order.discount_amount)
        if order.status == "PENDING":
            order.status = "PREPARING"
        await session.flush()

        return await OrderService.get_order_dict(session, tenant_id, order.id)

    # -------------------------------------------------------------
    # KDS (Kitchen Display System)
    # -------------------------------------------------------------
    @staticmethod
    async def get_kds_queue(session: AsyncSession, tenant_id: uuid.UUID, station: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt = (
            select(OrderItem, Order, DiningTable)
            .join(Order, OrderItem.order_id == Order.id)
            .outerjoin(DiningTable, Order.table_id == DiningTable.id)
            .where(
                OrderItem.tenant_id == tenant_id,
                OrderItem.status.in_(["QUEUED", "PREPARING", "READY"]),
                Order.status.in_(["PENDING", "PREPARING", "READY", "OUT_FOR_DELIVERY"])
            )
        )
        if station and station != "ALL":
            stmt = stmt.where(OrderItem.production_station == station)
        stmt = stmt.order_by(OrderItem.created_at.asc())

        results = (await session.execute(stmt)).all()

        now = datetime.now(timezone.utc)
        kds_items = []
        for item, order, table in results:
            wait_seconds = (now - item.created_at).total_seconds()
            wait_minutes = int(wait_seconds // 60)

            sla_status = "GREEN"
            if wait_minutes > 25:
                sla_status = "RED"
            elif wait_minutes >= 15:
                sla_status = "YELLOW"

            kds_items.append({
                "item_id": str(item.id),
                "order_id": str(order.id),
                "order_number": order.order_number,
                "channel": order.channel,
                "table_number": table.table_number if table else None,
                "customer_name": order.customer_name or (table.table_number if table else "Balcão"),
                "waiter_name": order.waiter_name,
                "item_name": item.name,
                "quantity": float(item.quantity),
                "preparation_notes": item.preparation_notes,
                "production_station": item.production_station,
                "status": item.status,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "started_at": item.started_at.isoformat() if item.started_at else None,
                "ready_at": item.ready_at.isoformat() if item.ready_at else None,
                "wait_minutes": wait_minutes,
                "sla_status": sla_status
            })
        return kds_items

    @staticmethod
    async def update_order_item_kds_status(session: AsyncSession, tenant_id: uuid.UUID, item_id: uuid.UUID, new_status: str) -> Dict[str, Any]:
        stmt = select(OrderItem).where(OrderItem.tenant_id == tenant_id, OrderItem.id == item_id)
        item = (await session.execute(stmt)).scalars().first()
        if not item:
            raise ValueError("Item de pedido não encontrado.")

        now = datetime.now(timezone.utc)
        item.status = new_status
        if new_status == "PREPARING" and not item.started_at:
            item.started_at = now
        elif new_status == "READY" and not item.ready_at:
            item.ready_at = now
        elif new_status == "SERVED" and not item.served_at:
            item.served_at = now

        await session.flush()

        order_stmt = select(Order).where(Order.id == item.order_id)
        order = (await session.execute(order_stmt)).scalars().first()
        if order:
            all_items_stmt = select(OrderItem).where(OrderItem.order_id == order.id)
            all_items = (await session.execute(all_items_stmt)).scalars().all()
            if all(i.status in ["READY", "SERVED"] for i in all_items):
                if order.channel == "DELIVERY":
                    order.status = "READY"
                else:
                    order.status = "READY" if any(i.status == "READY" for i in all_items) else "COMPLETED"
            elif any(i.status == "PREPARING" for i in all_items):
                order.status = "PREPARING"
            await session.flush()

        return {
            "item_id": str(item.id),
            "status": item.status,
            "started_at": item.started_at.isoformat() if item.started_at else None,
            "ready_at": item.ready_at.isoformat() if item.ready_at else None,
            "served_at": item.served_at.isoformat() if item.served_at else None
        }

    # -------------------------------------------------------------
    # FECHAMENTO & LIQUIDAÇÃO
    # -------------------------------------------------------------
    @staticmethod
    async def close_and_pay_order(session: AsyncSession, tenant_id: uuid.UUID, order_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        stmt = select(Order).where(Order.tenant_id == tenant_id, Order.id == order_id)
        order = (await session.execute(stmt)).scalars().first()
        if not order:
            raise ValueError("Comanda / Pedido não encontrado.")

        payment_method = payload.get("payment_method", "CREDIT_CARD")
        acquirer_id = uuid.UUID(payload["acquirer_id"]) if payload.get("acquirer_id") else None
        bank_account_id = uuid.UUID(payload["bank_account_id"]) if payload.get("bank_account_id") else None

        now = datetime.now(timezone.utc)
        order.payment_method = payment_method
        order.is_paid = True
        order.paid_at = now
        order.status = "COMPLETED"

        if order.table_id:
            table = await OrderService.get_table(session, tenant_id, order.table_id)
            if table:
                table.status = "AVAILABLE"
                table.active_order_id = None
                await session.flush()

        # Integração financeira
        try:
            receivable = ReceivableInvoice(
                tenant_id=tenant_id,
                acquirer_id=acquirer_id,
                invoice_number=f"REC-{order.order_number}",
                customer_name=order.customer_name or f"Venda {order.order_number}",
                gross_amount=order.total_amount,
                net_amount=order.total_amount,
                fee_amount=Decimal("0"),
                payment_method=payment_method,
                status="SETTLED",
                sale_date=now.date(),
                settlement_date=now.date()
            )

            if acquirer_id:
                acq_stmt = select(PaymentAcquirer).where(PaymentAcquirer.id == acquirer_id)
                acquirer = (await session.execute(acq_stmt)).scalars().first()
                if acquirer:
                    mdr_rate = acquirer.credit_mdr_rate if "CREDIT" in payment_method else acquirer.debit_mdr_rate
                    fee = (order.total_amount * (mdr_rate / Decimal("100"))).quantize(Decimal("0.01"))
                    receivable.fee_amount = fee
                    receivable.net_amount = order.total_amount - fee
                    receivable.mdr_rate_applied = mdr_rate

            session.add(receivable)
            await session.flush()

            installment = ReceivableInstallment(
                tenant_id=tenant_id,
                invoice_id=receivable.id,
                installment_number=1,
                gross_amount=receivable.gross_amount,
                net_amount=receivable.net_amount,
                fee_amount=receivable.fee_amount,
                due_date=now.date(),
                status="SETTLED"
            )
            session.add(installment)
            await session.flush()

            if bank_account_id:
                settlement = ReceivableSettlement(
                    tenant_id=tenant_id,
                    installment_id=installment.id,
                    bank_account_id=bank_account_id,
                    settled_amount=receivable.net_amount,
                    settled_at=now
                )
                session.add(settlement)

                bank_stmt = select(BankAccount).where(BankAccount.id == bank_account_id)
                bank_acc = (await session.execute(bank_stmt)).scalars().first()
                if bank_acc:
                    bank_acc.current_balance += receivable.net_amount
        except Exception:
            pass

        await session.flush()
        return await OrderService.get_order_dict(session, tenant_id, order.id)

    # -------------------------------------------------------------
    # DELIVERY HUB KANBAN
    # -------------------------------------------------------------
    @staticmethod
    async def list_delivery_orders(session: AsyncSession, tenant_id: uuid.UUID) -> Dict[str, List[Dict[str, Any]]]:
        stmt = (
            select(Order)
            .where(
                Order.tenant_id == tenant_id,
                Order.channel.in_(["DELIVERY", "TAKEOUT", "QR_CODE", "WHATSAPP"]),
                Order.status.in_(["PENDING", "PREPARING", "READY", "OUT_FOR_DELIVERY", "COMPLETED"])
            )
            .order_by(desc(Order.created_at))
        )
        orders = (await session.execute(stmt)).scalars().all()

        kanban: Dict[str, List[Dict[str, Any]]] = {
            "PENDING": [],
            "PREPARING": [],
            "READY": [],
            "OUT_FOR_DELIVERY": [],
            "COMPLETED": []
        }

        now = datetime.now(timezone.utc)
        for ord in orders:
            items_stmt = select(OrderItem).where(OrderItem.order_id == ord.id)
            items = (await session.execute(items_stmt)).scalars().all()

            wait_seconds = (now - ord.created_at).total_seconds()
            wait_minutes = int(wait_seconds // 60)

            items_summary = [
                f"{float(it.quantity):g}x {it.name}"
                for it in items
            ]

            data = {
                "id": str(ord.id),
                "order_number": ord.order_number,
                "channel": ord.channel,
                "status": ord.status,
                "customer_name": ord.customer_name or "Cliente",
                "customer_phone": ord.customer_phone,
                "delivery_address": ord.delivery_address,
                "subtotal": float(ord.subtotal),
                "delivery_fee": float(ord.delivery_fee),
                "total_amount": float(ord.total_amount),
                "notes": ord.notes,
                "payment_method": ord.payment_method or "Pendente",
                "is_paid": ord.is_paid,
                "created_at": ord.created_at.isoformat() if ord.created_at else None,
                "wait_minutes": wait_minutes,
                "items_count": len(items),
                "items_summary": items_summary
            }

            if ord.status in kanban:
                kanban[ord.status].append(data)

        return kanban

    @staticmethod
    async def update_delivery_status(session: AsyncSession, tenant_id: uuid.UUID, order_id: uuid.UUID, new_status: str) -> Optional[Dict[str, Any]]:
        stmt = select(Order).where(Order.tenant_id == tenant_id, Order.id == order_id)
        order = (await session.execute(stmt)).scalars().first()
        if not order:
            return None
        order.status = new_status
        if new_status == "COMPLETED" and not order.is_paid:
            order.is_paid = True
            order.paid_at = datetime.now(timezone.utc)
        await session.flush()
        return await OrderService.get_order_dict(session, tenant_id, order.id)
