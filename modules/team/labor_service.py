import uuid
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func


from modules.team.models import (
    Employee, WorkShift, TimeClockEntry, TipDistribution, TipDistributionItem
)
from modules.financial.models import ReceivableInvoice, PayableBill
from modules.sales.models import SaleLine
from modules.inventory.models import StockLedgerEntry
from packages.tenant.models import Location


class LaborService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Employees ---
    async def list_employees(
        self,
        tenant_id: UUID,
        department: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Employee]:
        stmt = select(Employee).where(Employee.tenant_id == tenant_id)
        if department:
            stmt = stmt.where(Employee.department == department)
        if is_active is not None:
            stmt = stmt.where(Employee.is_active == is_active)
        stmt = stmt.order_by(Employee.name.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_employee(
        self,
        tenant_id: UUID,
        data: Dict[str, Any]
    ) -> Employee:
        employee = Employee(
            tenant_id=tenant_id,
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            role_title=data["role_title"],
            department=data.get("department", "FLOOR"),
            monthly_salary=Decimal(str(data.get("monthly_salary", "0.00"))),
            hourly_rate=Decimal(str(data.get("hourly_rate", "0.00"))),
            tip_points=Decimal(str(data.get("tip_points", "1.00"))),
            is_active=data.get("is_active", True)
        )
        self.db.add(employee)
        await self.db.commit()
        return employee

    async def update_employee(
        self,
        tenant_id: UUID,
        employee_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[Employee]:
        stmt = select(Employee).where(Employee.id == employee_id, Employee.tenant_id == tenant_id)
        emp = (await self.db.execute(stmt)).scalar_one_or_none()
        if not emp:
            return None

        if "name" in data: emp.name = data["name"]
        if "email" in data: emp.email = data["email"]
        if "phone" in data: emp.phone = data["phone"]
        if "role_title" in data: emp.role_title = data["role_title"]
        if "department" in data: emp.department = data["department"]
        if "monthly_salary" in data: emp.monthly_salary = Decimal(str(data["monthly_salary"]))
        if "hourly_rate" in data: emp.hourly_rate = Decimal(str(data["hourly_rate"]))
        if "tip_points" in data: emp.tip_points = Decimal(str(data["tip_points"]))
        if "is_active" in data: emp.is_active = data["is_active"]

        await self.db.commit()
        return emp

    # --- Work Shifts ---
    async def list_shifts(
        self,
        tenant_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        location_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(WorkShift, Employee.name.label("employee_name"), Employee.role_title.label("role_title"), Employee.department.label("department"))
            .join(Employee, WorkShift.employee_id == Employee.id)
            .where(WorkShift.tenant_id == tenant_id)
        )
        if start_date:
            stmt = stmt.where(WorkShift.shift_date >= start_date)
        if end_date:
            stmt = stmt.where(WorkShift.shift_date <= end_date)
        if location_id:
            stmt = stmt.where(WorkShift.location_id == location_id)

        stmt = stmt.order_by(WorkShift.shift_date.asc(), WorkShift.start_time.asc())
        rows = (await self.db.execute(stmt)).all()

        results = []
        for shift, emp_name, role, dept in rows:
            results.append({
                "id": shift.id,
                "tenant_id": shift.tenant_id,
                "employee_id": shift.employee_id,
                "employee_name": emp_name,
                "role_title": role,
                "department": dept,
                "location_id": shift.location_id,
                "shift_date": shift.shift_date,
                "start_time": shift.start_time,
                "end_time": shift.end_time,
                "status": shift.status,
                "notes": shift.notes,
                "created_at": shift.created_at
            })
        return results

    async def create_shift(
        self,
        tenant_id: UUID,
        data: Dict[str, Any]
    ) -> WorkShift:
        shift = WorkShift(
            tenant_id=tenant_id,
            employee_id=data["employee_id"],
            location_id=data["location_id"],
            shift_date=data["shift_date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            status=data.get("status", "SCHEDULED"),
            notes=data.get("notes")
        )
        self.db.add(shift)
        await self.db.commit()
        return shift

    # --- Time Clock ---
    async def clock_in(
        self,
        tenant_id: UUID,
        employee_id: UUID,
        location_id: UUID
    ) -> TimeClockEntry:
        # Check if already has an open entry
        stmt = select(TimeClockEntry).where(
            TimeClockEntry.tenant_id == tenant_id,
            TimeClockEntry.employee_id == employee_id,
            TimeClockEntry.clock_out == None
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ValueError("Colaborador já possui um registro de ponto em aberto.")

        entry = TimeClockEntry(
            tenant_id=tenant_id,
            employee_id=employee_id,
            location_id=location_id,
            clock_in=datetime.now(timezone.utc),
            status="OPEN"
        )
        self.db.add(entry)
        await self.db.commit()
        return entry

    async def clock_out(
        self,
        tenant_id: UUID,
        employee_id: UUID,
        break_minutes: int = 0
    ) -> TimeClockEntry:
        stmt = select(TimeClockEntry).where(
            TimeClockEntry.tenant_id == tenant_id,
            TimeClockEntry.employee_id == employee_id,
            TimeClockEntry.clock_out == None
        ).order_by(TimeClockEntry.clock_in.desc())
        entry = (await self.db.execute(stmt)).scalar_one_or_none()
        if not entry:
            raise ValueError("Nenhum registro de ponto aberto encontrado para este colaborador.")

        out_time = datetime.now(timezone.utc)
        entry.clock_out = out_time
        entry.break_minutes = break_minutes

        diff_seconds = (out_time - entry.clock_in).total_seconds()
        work_seconds = max(0, diff_seconds - (break_minutes * 60))
        entry.total_hours = Decimal(str(round(work_seconds / 3600.0, 4)))
        entry.status = "APPROVED"

        await self.db.commit()
        return entry

    async def list_time_clock_entries(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(TimeClockEntry, Employee.name.label("employee_name"), Employee.role_title.label("role_title"), Employee.department.label("department"))
            .join(Employee, TimeClockEntry.employee_id == Employee.id)
            .where(TimeClockEntry.tenant_id == tenant_id)
        )
        if start_date:
            stmt = stmt.where(TimeClockEntry.clock_in >= start_date)
        if end_date:
            stmt = stmt.where(TimeClockEntry.clock_in <= end_date)

        stmt = stmt.order_by(TimeClockEntry.clock_in.desc())
        rows = (await self.db.execute(stmt)).all()

        results = []
        for entry, name, role, dept in rows:
            results.append({
                "id": entry.id,
                "tenant_id": entry.tenant_id,
                "employee_id": entry.employee_id,
                "employee_name": name,
                "role_title": role,
                "department": dept,
                "location_id": entry.location_id,
                "clock_in": entry.clock_in,
                "clock_out": entry.clock_out,
                "break_minutes": entry.break_minutes,
                "total_hours": entry.total_hours,
                "status": entry.status,
                "created_at": entry.created_at
            })
        return results

    # --- Tip Distribution (Lei da Gorjeta 13.419/2017) ---
    async def calculate_and_distribute_tips(
        self,
        tenant_id: UUID,
        reference_period: str,
        period_start: datetime,
        period_end: datetime,
        total_tips_collected: Decimal,
        house_retention_percentage: Decimal = Decimal("0.00"), # e.g. 10.00%
        save: bool = True
    ) -> Dict[str, Any]:
        # 1. Calculate net tips pool after house retention
        retention_rate = house_retention_percentage / Decimal("100.00")
        house_retained_amount = total_tips_collected * retention_rate
        net_tips_pool = total_tips_collected - house_retained_amount

        # 2. Get hours worked per active employee in the period
        clock_stmt = (
            select(TimeClockEntry.employee_id, func.sum(TimeClockEntry.total_hours).label("hours"))
            .where(
                TimeClockEntry.tenant_id == tenant_id,
                TimeClockEntry.clock_in >= period_start,
                TimeClockEntry.clock_in <= period_end
            )
            .group_by(TimeClockEntry.employee_id)
        )
        clock_res = (await self.db.execute(clock_stmt)).all()
        hours_map = {row[0]: Decimal(str(row[1] or "0")) for row in clock_res}

        # 3. Load all active employees
        emp_stmt = select(Employee).where(Employee.tenant_id == tenant_id, Employee.is_active == True)
        employees = (await self.db.execute(emp_stmt)).scalars().all()

        items_breakdown = []
        total_points_pool = Decimal("0.00")

        for emp in employees:
            hours = hours_map.get(emp.id, Decimal("0.00"))
            # If no time clock entries found, fallback to standard 160h for full-time active staff
            if hours == Decimal("0.00"):
                hours = Decimal("160.00")

            points = emp.tip_points
            share = hours * points
            total_points_pool += share

            items_breakdown.append({
                "employee_id": emp.id,
                "employee_name": emp.name,
                "role_title": emp.role_title,
                "department": emp.department,
                "hours_worked": hours,
                "points": points,
                "calculated_share": share,
                "allocated_tip_amount": Decimal("0.00")
            })

        # 4. Allocate tip amounts proportional to calculated_share
        if total_points_pool > Decimal("0.00") and net_tips_pool > Decimal("0.00"):
            for item in items_breakdown:
                item_prop = item["calculated_share"] / total_points_pool
                item["allocated_tip_amount"] = round(net_tips_pool * item_prop, 2)

        distribution_record = None
        if save:
            distribution_record = TipDistribution(
                tenant_id=tenant_id,
                reference_period=reference_period,
                period_start=period_start,
                period_end=period_end,
                total_tips_collected=total_tips_collected,
                house_retention_percentage=house_retention_percentage,
                net_tips_pool=net_tips_pool,
                status="DISTRIBUTED"
            )
            self.db.add(distribution_record)
            await self.db.flush()

            for item in items_breakdown:
                db_item = TipDistributionItem(
                    tenant_id=tenant_id,
                    distribution_id=distribution_record.id,
                    employee_id=item["employee_id"],
                    hours_worked=item["hours_worked"],
                    points=item["points"],
                    calculated_share=item["calculated_share"],
                    allocated_tip_amount=item["allocated_tip_amount"]
                )
                self.db.add(db_item)

            await self.db.commit()

        return {
            "distribution_id": distribution_record.id if distribution_record else None,
            "reference_period": reference_period,
            "total_tips_collected": total_tips_collected,
            "house_retention_percentage": house_retention_percentage,
            "house_retained_amount": house_retained_amount,
            "net_tips_pool": net_tips_pool,
            "total_points_pool": total_points_pool,
            "total_beneficiaries": len(items_breakdown),
            "items": items_breakdown
        }

    # --- Prime Cost (CMV + CMO) Calculation ---
    async def get_prime_cost_analysis(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        # 1. Total Net Revenue from Receivables / Invoices
        ar_stmt = select(ReceivableInvoice).where(ReceivableInvoice.tenant_id == tenant_id)
        if start_date:
            ar_stmt = ar_stmt.where(ReceivableInvoice.issue_date >= start_date)
        if end_date:
            ar_stmt = ar_stmt.where(ReceivableInvoice.issue_date <= end_date)
        invoices = (await self.db.execute(ar_stmt)).scalars().all()
        net_revenue = sum((inv.net_amount for inv in invoices), Decimal("0.00"))

        if net_revenue == Decimal("0.00"):
            # Fallback to sum of total_amount
            net_revenue = sum((inv.total_amount for inv in invoices), Decimal("0.00"))

        # If still 0, check sales lines
        if net_revenue == Decimal("0.00"):
            sale_stmt = select(SaleLine).where(SaleLine.tenant_id == tenant_id)
            if start_date:
                sale_stmt = sale_stmt.where(SaleLine.sale_timestamp >= start_date)
            if end_date:
                sale_stmt = sale_stmt.where(SaleLine.sale_timestamp <= end_date)
            sales = (await self.db.execute(sale_stmt)).scalars().all()
            net_revenue = sum((Decimal(str(s.quantity)) * Decimal(str(s.unit_price)) for s in sales), Decimal("0.00"))

        # 2. Actual Food Cost (CMV Real) from Payable Bills with category EXPENSE_CMV or Stock Ledger
        cmv_stmt = select(PayableBill).where(PayableBill.tenant_id == tenant_id)
        if start_date:
            cmv_stmt = cmv_stmt.where(PayableBill.first_due_date >= start_date)
        if end_date:
            cmv_stmt = cmv_stmt.where(PayableBill.first_due_date <= end_date)
        bills = (await self.db.execute(cmv_stmt)).scalars().all()
        food_cost_cmv = sum((b.total_amount for b in bills), Decimal("0.00"))

        # 3. Labor Cost (CMO): Base salaries + Hourly pay + Social Charges (35%)
        emp_stmt = select(Employee).where(Employee.tenant_id == tenant_id, Employee.is_active == True)
        employees = (await self.db.execute(emp_stmt)).scalars().all()

        base_salaries = sum((emp.monthly_salary for emp in employees), Decimal("0.00"))
        
        # Hours from timeclock
        tc_stmt = select(func.sum(TimeClockEntry.total_hours)).where(TimeClockEntry.tenant_id == tenant_id)
        if start_date:
            tc_stmt = tc_stmt.where(TimeClockEntry.clock_in >= start_date)
        if end_date:
            tc_stmt = tc_stmt.where(TimeClockEntry.clock_in <= end_date)
        total_clock_hours = Decimal(str((await self.db.execute(tc_stmt)).scalar() or "0"))

        hourly_payroll = sum(
            (emp.hourly_rate * (total_clock_hours / max(Decimal("1"), Decimal(str(len(employees))))))
            for emp in employees if emp.hourly_rate > Decimal("0")
        )
        
        direct_payroll = base_salaries + hourly_payroll
        social_charges = direct_payroll * Decimal("0.35") # 35% encargos e provisões
        total_labor_cost_cmo = direct_payroll + social_charges

        # 4. Prime Cost = CMV + CMO
        prime_cost_amount = food_cost_cmv + total_labor_cost_cmo

        cmv_percentage = Decimal("0.00")
        cmo_percentage = Decimal("0.00")
        prime_cost_percentage = Decimal("0.00")

        if net_revenue > Decimal("0.00"):
            cmv_percentage = round((food_cost_cmv / net_revenue) * Decimal("100.00"), 2)
            cmo_percentage = round((total_labor_cost_cmo / net_revenue) * Decimal("100.00"), 2)
            prime_cost_percentage = round((prime_cost_amount / net_revenue) * Decimal("100.00"), 2)

        # Health status evaluation
        health_status = "HEALTHY"
        status_label = "Meta Saudável (55% a 65%)"
        if prime_cost_percentage < Decimal("55.00") and prime_cost_percentage > Decimal("0.00"):
            health_status = "EXCELLENT"
            status_label = "Excelente (Altíssima Margem Operacional)"
        elif prime_cost_percentage > Decimal("68.00"):
            health_status = "CRITICAL"
            status_label = "Crítico (Risco Operacional: Prime Cost acima de 68%)"
        elif prime_cost_percentage > Decimal("65.00"):
            health_status = "WARNING"
            status_label = "Atenção (Margem Comprimida: 65% a 68%)"

        return {
            "net_revenue": net_revenue,
            "food_cost_cmv": food_cost_cmv,
            "cmv_percentage": cmv_percentage,
            "total_labor_cost_cmo": total_labor_cost_cmo,
            "direct_payroll": direct_payroll,
            "social_charges": social_charges,
            "cmo_percentage": cmo_percentage,
            "prime_cost_amount": prime_cost_amount,
            "prime_cost_percentage": prime_cost_percentage,
            "active_headcount": len(employees),
            "total_hours_logged": total_clock_hours,
            "health_status": health_status,
            "status_label": status_label
        }
