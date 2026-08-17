import pytest
import uuid
from decimal import Decimal
from datetime import datetime, date, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.team.models import Employee, WorkShift, TimeClockEntry, TipDistribution
from packages.tenant.models import BusinessUnit, Location, Tenant


@pytest.mark.asyncio
async def test_employee_crud_and_shifts(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    t_id = uuid.UUID(tenant_id)

    # 1. Setup Location
    bu = BusinessUnit(tenant_id=t_id, name="Matriz Restaurante")
    owner_session.add(bu)
    await owner_session.flush()

    loc = Location(tenant_id=t_id, business_unit_id=bu.id, name="Salão Principal")
    owner_session.add(loc)
    await owner_session.flush()
    loc_id_str = str(loc.id)

    await owner_session.commit()

    # 2. Create Employees via API
    r_emp1 = await async_client.post("/team/employees", json={
        "name": "Marcelo Garçom",
        "email": "marcelo@restaurante.com",
        "role_title": "Garçom Líder",
        "department": "FLOOR",
        "monthly_salary": "2500.00",
        "hourly_rate": "15.00",
        "tip_points": "1.00"
    }, headers=auth_headers)
    assert r_emp1.status_code == 201, r_emp1.text
    emp1 = r_emp1.json()
    emp1_id = emp1["id"]

    r_emp2 = await async_client.post("/team/employees", json={
        "name": "Rodrigo Cozinheiro",
        "email": "rodrigo@restaurante.com",
        "role_title": "Cozinheiro de Praça",
        "department": "KITCHEN",
        "monthly_salary": "3200.00",
        "hourly_rate": "20.00",
        "tip_points": "0.80"
    }, headers=auth_headers)
    assert r_emp2.status_code == 201, r_emp2.text
    emp2 = r_emp2.json()

    # 3. List Employees
    r_list = await async_client.get("/team/employees", headers=auth_headers)
    assert r_list.status_code == 200
    emps = r_list.json()
    assert len(emps) >= 2
    assert any(e["id"] == emp1_id for e in emps)

    # 4. Create Work Shift
    r_shift = await async_client.post("/team/shifts", json={
        "employee_id": emp1_id,
        "location_id": loc_id_str,
        "shift_date": "2026-08-20",
        "start_time": "2026-08-20T17:00:00Z",
        "end_time": "2026-08-21T01:00:00Z",
        "notes": "Turno noturno salão"
    }, headers=auth_headers)
    assert r_shift.status_code == 201
    assert r_shift.json()["status"] == "SCHEDULED"

    # 5. List Shifts
    r_shifts = await async_client.get("/team/shifts?start_date=2026-08-20", headers=auth_headers)
    assert r_shifts.status_code == 200
    assert len(r_shifts.json()) >= 1


@pytest.mark.asyncio
async def test_time_clock_and_tip_distribution_lei_da_gorjeta(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    t_id = uuid.UUID(tenant_id)

    # 1. Setup Location & Employees
    bu = BusinessUnit(tenant_id=t_id, name="Unidade Gorjeta")
    owner_session.add(bu)
    await owner_session.flush()
    loc = Location(tenant_id=t_id, business_unit_id=bu.id, name="Bar e Restaurante")
    owner_session.add(loc)
    await owner_session.flush()

    emp_a = Employee(
        tenant_id=t_id,
        name="Ana Garçonete",
        role_title="Garçom",
        department="FLOOR",
        monthly_salary=Decimal("2000.00"),
        tip_points=Decimal("1.00"),
        is_active=True
    )
    emp_b = Employee(
        tenant_id=t_id,
        name="Bruno Bartender",
        role_title="Bartender",
        department="BAR",
        monthly_salary=Decimal("2800.00"),
        tip_points=Decimal("1.00"),
        is_active=True
    )
    owner_session.add_all([emp_a, emp_b])
    await owner_session.flush()

    emp_a_id = str(emp_a.id)
    emp_b_id = str(emp_b.id)
    loc_id = str(loc.id)

    await owner_session.commit()

    # 2. Clock In & Out for Employee A
    r_in = await async_client.post("/team/time-clock/in", json={
        "employee_id": emp_a_id,
        "location_id": loc_id
    }, headers=auth_headers)
    assert r_in.status_code == 200
    assert r_in.json()["status"] == "OPEN"

    r_out = await async_client.post("/team/time-clock/out", json={
        "employee_id": emp_a_id,
        "break_minutes": 30
    }, headers=auth_headers)
    assert r_out.status_code == 200
    assert r_out.json()["status"] == "APPROVED"

    # 3. Calculate Tip Distribution: R$ 1.000,00 collected, 10% house retention = R$ 900,00 net
    r_tips = await async_client.post("/team/tips/calculate", json={
        "reference_period": "2026-08",
        "period_start": "2026-08-01T00:00:00Z",
        "period_end": "2026-08-31T23:59:59Z",
        "total_tips_collected": "1000.00",
        "house_retention_percentage": "10.00",
        "save": True
    }, headers=auth_headers)
    assert r_tips.status_code == 200, r_tips.text
    tip_res = r_tips.json()
    assert float(tip_res["net_tips_pool"]) == 900.0
    assert float(tip_res["house_retained_amount"]) == 100.0
    assert len(tip_res["items"]) >= 2

    # Check that sum of allocated amounts equals net pool
    total_allocated = sum(float(i["allocated_tip_amount"]) for i in tip_res["items"])
    assert abs(total_allocated - 900.0) < 1.0



@pytest.mark.asyncio
async def test_prime_cost_cmv_and_cmo_calculation(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    # Query Prime Cost endpoint
    r_pc = await async_client.get("/team/prime-cost", headers=auth_headers)
    assert r_pc.status_code == 200
    pc = r_pc.json()
    assert "prime_cost_amount" in pc
    assert "prime_cost_percentage" in pc
    assert "health_status" in pc
    assert "status_label" in pc
    assert "total_labor_cost_cmo" in pc
    assert "food_cost_cmv" in pc


@pytest.mark.asyncio
async def test_cross_tenant_isolation_employees_and_shifts(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession
):
    # Tenant 2
    t2 = Tenant(name="Restaurante T2 RH")
    owner_session.add(t2)
    await owner_session.flush()
    t2_id = t2.id

    emp2 = Employee(
        tenant_id=t2_id,
        name="Funcionario Secreto T2",
        role_title="Gerente",
        department="ADMIN",
        monthly_salary=Decimal("5000.00")
    )
    owner_session.add(emp2)
    await owner_session.flush()
    emp2_id_str = str(emp2.id)

    await owner_session.commit()

    # Query with Tenant 1
    r_list = await async_client.get("/team/employees", headers=auth_headers)
    assert r_list.status_code == 200
    assert all(e["id"] != emp2_id_str for e in r_list.json())
