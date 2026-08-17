import uuid
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Boolean, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from packages.tenant.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    role_title = Column(String(100), nullable=False) # Garçom, Cozinheiro, Bartender, Chef, Gerente, Cumim
    department = Column(String(50), nullable=False, default="FLOOR") # FLOOR, KITCHEN, BAR, ADMIN, DELIVERY
    monthly_salary = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    hourly_rate = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    tip_points = Column(Numeric(precision=24, scale=12), nullable=False, default=1.0) # Weight in tip distribution
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WorkShift(Base):
    __tablename__ = "work_shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    shift_date = Column(Date, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default="SCHEDULED") # SCHEDULED, COMPLETED, ABSENT, CANCELLED
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TimeClockEntry(Base):
    __tablename__ = "time_clock_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    clock_in = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    clock_out = Column(DateTime(timezone=True), nullable=True)
    break_minutes = Column(Integer, nullable=False, default=0)
    total_hours = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    status = Column(String(50), nullable=False, default="OPEN") # OPEN, APPROVED, ADJUSTED
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TipDistribution(Base):
    __tablename__ = "tip_distributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    reference_period = Column(String(50), nullable=False) # e.g. '2026-08'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    total_tips_collected = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    house_retention_percentage = Column(Numeric(precision=24, scale=12), nullable=False, default=0) # e.g. 10.00%
    net_tips_pool = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    status = Column(String(50), nullable=False, default="DRAFT") # DRAFT, DISTRIBUTED, PAID
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TipDistributionItem(Base):
    __tablename__ = "tip_distribution_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    distribution_id = Column(UUID(as_uuid=True), ForeignKey("tip_distributions.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    hours_worked = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
    points = Column(Numeric(precision=24, scale=12), nullable=False, default=1.0)
    calculated_share = Column(Numeric(precision=24, scale=12), nullable=False, default=0) # hours * points
    allocated_tip_amount = Column(Numeric(precision=24, scale=12), nullable=False, default=0)
