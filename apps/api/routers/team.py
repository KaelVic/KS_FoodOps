import uuid
from typing import List, Optional, Any, Dict
from datetime import datetime, date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, ConfigDict

from sqlalchemy.ext.asyncio import AsyncSession
from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from packages.tenant.service import TenantService
from modules.team.labor_service import LaborService

router = APIRouter()

# --- Legacy Membership Schemas ---
class MembershipBase(BaseModel):
    user_id: str = Field(..., example="user-123")
    role: str = Field(..., example="manager")

class MembershipUpdate(BaseModel):
    role: str

class MembershipResponse(MembershipBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# --- Phase 8 HR Schemas ---
class EmployeeCreatePayload(BaseModel):
    name: str = Field(..., example="Carlos Alberto")
    email: Optional[str] = None
    phone: Optional[str] = None
    role_title: str = Field(..., example="Garçom Líder")
    department: str = Field("FLOOR", example="FLOOR") # FLOOR, KITCHEN, BAR, ADMIN, DELIVERY
    monthly_salary: Decimal = Decimal("0.00")
    hourly_rate: Decimal = Decimal("0.00")
    tip_points: Decimal = Decimal("1.00")
    is_active: bool = True

class EmployeeResponse(EmployeeCreatePayload):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ShiftCreatePayload(BaseModel):
    employee_id: uuid.UUID
    location_id: uuid.UUID
    shift_date: date
    start_time: datetime
    end_time: datetime
    status: str = "SCHEDULED"
    notes: Optional[str] = None

class ClockInPayload(BaseModel):
    employee_id: uuid.UUID
    location_id: uuid.UUID

class ClockOutPayload(BaseModel):
    employee_id: uuid.UUID
    break_minutes: int = 0

class TipCalculatePayload(BaseModel):
    reference_period: str = Field(..., example="2026-08")
    period_start: datetime
    period_end: datetime
    total_tips_collected: Decimal
    house_retention_percentage: Decimal = Decimal("0.00")
    save: bool = True


# --- Membership Routes ---
@router.get("/memberships", response_model=List[MembershipResponse])
async def list_memberships(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await TenantService.list_memberships(db, tenant_id)

@router.post("/invite", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    payload: MembershipBase,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    return await TenantService.create_membership(db, tenant_id, payload.user_id, payload.role)

@router.put("/{membership_id}/role", response_model=MembershipResponse)
async def update_role(
    membership_id: uuid.UUID,
    payload: MembershipUpdate,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    membership = await TenantService.update_membership_role(db, tenant_id, membership_id, payload.role)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    return membership


# --- Phase 8 Employee Routes ---
@router.get("/employees", response_model=List[EmployeeResponse])
async def list_employees(
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    return await service.list_employees(tenant_id, department, is_active)

@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreatePayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    return await service.create_employee(tenant_id, payload.model_dump())

@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeCreatePayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    emp = await service.update_employee(tenant_id, employee_id, payload.model_dump())
    if not emp:
        raise HTTPException(status_code=404, detail="Colaborador não encontrado")
    return emp


# --- Shifts Routes ---
@router.get("/shifts")
async def list_shifts(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    location_id: Optional[uuid.UUID] = None,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    return await service.list_shifts(tenant_id, start_date, end_date, location_id)

@router.post("/shifts", status_code=status.HTTP_201_CREATED)
async def create_shift(
    payload: ShiftCreatePayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    shift = await service.create_shift(tenant_id, payload.model_dump())
    return {"id": shift.id, "status": "SCHEDULED"}


# --- Time Clock Routes ---
@router.post("/time-clock/in")
async def clock_in(
    payload: ClockInPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    try:
        entry = await service.clock_in(tenant_id, payload.employee_id, payload.location_id)
        return {"id": entry.id, "clock_in": entry.clock_in, "status": entry.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/time-clock/out")
async def clock_out(
    payload: ClockOutPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    try:
        entry = await service.clock_out(tenant_id, payload.employee_id, payload.break_minutes)
        return {
            "id": entry.id,
            "clock_out": entry.clock_out,
            "total_hours": entry.total_hours,
            "status": entry.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/time-clock")
async def list_time_clock(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    return await service.list_time_clock_entries(tenant_id, start_date, end_date)


# --- Tip Distribution Routes (Lei 13.419/2017) ---
@router.post("/tips/calculate")
async def calculate_tips(
    payload: TipCalculatePayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    return await service.calculate_and_distribute_tips(
        tenant_id=tenant_id,
        reference_period=payload.reference_period,
        period_start=payload.period_start,
        period_end=payload.period_end,
        total_tips_collected=payload.total_tips_collected,
        house_retention_percentage=payload.house_retention_percentage,
        save=payload.save
    )


# --- Prime Cost (CMV + CMO) Analysis ---
@router.get("/prime-cost")
async def get_prime_cost(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = LaborService(db)
    return await service.get_prime_cost_analysis(tenant_id, start_date, end_date)
