import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Numeric,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from packages.tenant.database import Base


class DiningTable(Base):
    __tablename__ = "dining_tables"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    table_number = Column(String(50), nullable=False) # Ex: "Mesa 01", "Mesa 12", "Bar 02", "Varanda 05"
    capacity = Column(Integer, default=4, nullable=False)
    section = Column(String(50), default="Salão Principal", nullable=False) # "Salão Principal", "Varanda", "Bar", "Área Externa"
    status = Column(String(30), default="AVAILABLE", nullable=False) # AVAILABLE, OCCUPIED, RESERVED, BILL_REQUESTED, CLEANING
    active_order_id = Column(UUID(as_uuid=True), nullable=True) # ID da comanda aberta no momento

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_number = Column(String(50), nullable=False) # Ex: "CMD-104", "DEL-809"
    channel = Column(String(30), default="DINE_IN", nullable=False) # DINE_IN, TAKEOUT, DELIVERY, QR_CODE, WHATSAPP
    status = Column(String(30), default="PENDING", nullable=False) # PENDING, PREPARING, READY, OUT_FOR_DELIVERY, COMPLETED, CANCELLED

    table_id = Column(UUID(as_uuid=True), ForeignKey("dining_tables.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(150), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    delivery_address = Column(Text, nullable=True)
    waiter_name = Column(String(100), nullable=True)

    subtotal = Column(Numeric(24, 12), default=Decimal("0"), nullable=False)
    delivery_fee = Column(Numeric(24, 12), default=Decimal("0"), nullable=False)
    discount_amount = Column(Numeric(24, 12), default=Decimal("0"), nullable=False)
    total_amount = Column(Numeric(24, 12), default=Decimal("0"), nullable=False)

    notes = Column(Text, nullable=True)
    payment_method = Column(String(50), nullable=True) # CREDIT_CARD, DEBIT_CARD, PIX, CASH, VOUCHER_VR, IFOOD_ONLINE
    is_paid = Column(Boolean, default=False, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(200), nullable=False)
    quantity = Column(Numeric(24, 12), default=Decimal("1"), nullable=False)
    unit_price = Column(Numeric(24, 12), default=Decimal("0"), nullable=False)
    total_price = Column(Numeric(24, 12), default=Decimal("0"), nullable=False)

    preparation_notes = Column(String(300), nullable=True) # Ex: "Sem cebola", "Ponto mal passada", "Com gelo e limão"
    production_station = Column(String(50), default="KITCHEN", nullable=False) # KITCHEN, BAR, PIZZERIA, DESSERT
    status = Column(String(30), default="QUEUED", nullable=False) # QUEUED, PREPARING, READY, SERVED, CANCELLED

    started_at = Column(DateTime(timezone=True), nullable=True)
    ready_at = Column(DateTime(timezone=True), nullable=True)
    served_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    order = relationship("Order", back_populates="items")
