import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.tenant.models import Location, BusinessUnit, TenantMembership

class TenantService:
    
    @staticmethod
    async def list_locations(db: AsyncSession, tenant_id: uuid.UUID) -> List[Location]:
        stmt = select(Location).where(Location.tenant_id == tenant_id).order_by(Location.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_location(db: AsyncSession, tenant_id: uuid.UUID, location_id: uuid.UUID) -> Optional[Location]:
        stmt = select(Location).where(Location.tenant_id == tenant_id, Location.id == location_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_location(db: AsyncSession, tenant_id: uuid.UUID, business_unit_id: uuid.UUID, name: str) -> Location:
        loc = Location(tenant_id=tenant_id, business_unit_id=business_unit_id, name=name)
        db.add(loc)
        await db.flush()
        return loc

    @staticmethod
    async def update_location(db: AsyncSession, tenant_id: uuid.UUID, location_id: uuid.UUID, name: str) -> Optional[Location]:
        loc = await TenantService.get_location(db, tenant_id, location_id)
        if not loc:
            return None
        loc.name = name
        await db.flush()
        return loc

    @staticmethod
    async def list_business_units(db: AsyncSession, tenant_id: uuid.UUID) -> List[BusinessUnit]:
        stmt = select(BusinessUnit).where(BusinessUnit.tenant_id == tenant_id).order_by(BusinessUnit.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_memberships(db: AsyncSession, tenant_id: uuid.UUID) -> List[TenantMembership]:
        stmt = select(TenantMembership).where(TenantMembership.tenant_id == tenant_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_membership(db: AsyncSession, tenant_id: uuid.UUID, membership_id: uuid.UUID) -> Optional[TenantMembership]:
        stmt = select(TenantMembership).where(TenantMembership.tenant_id == tenant_id, TenantMembership.id == membership_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_membership(db: AsyncSession, tenant_id: uuid.UUID, user_id: str, role: str) -> TenantMembership:
        membership = TenantMembership(tenant_id=tenant_id, user_id=user_id, role=role)
        db.add(membership)
        await db.flush()
        return membership

    @staticmethod
    async def update_membership_role(db: AsyncSession, tenant_id: uuid.UUID, membership_id: uuid.UUID, role: str) -> Optional[TenantMembership]:
        membership = await TenantService.get_membership(db, tenant_id, membership_id)
        if not membership:
            return None
        membership.role = role
        await db.flush()
        return membership

    @staticmethod
    async def create_tenant_onboarding(db: AsyncSession, user_id: str, restaurant_name: str) -> dict:
        from packages.tenant.models import Tenant, BusinessUnit, Location, TenantMembership
        from sqlalchemy import text
        import uuid
        
        # 1. Create Tenant
        tenant = Tenant(name=restaurant_name)
        db.add(tenant)
        await db.flush()
        
        # Set RLS session variable so tenant-scoped inserts are permitted by PostgreSQL RLS
        await db.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, false)"),
            {"tid": str(tenant.id)}
        )

        # 2. Create Default Business Unit
        bu = BusinessUnit(tenant_id=tenant.id, name="Unidade Principal")
        db.add(bu)
        await db.flush()
        
        # 3. Create Default Location
        loc = Location(tenant_id=tenant.id, business_unit_id=bu.id, name="Estoque Geral")
        db.add(loc)
        
        # 4. Create Admin Membership
        membership = TenantMembership(tenant_id=tenant.id, user_id=user_id, role="admin")
        db.add(membership)
        
        await db.flush()
        
        return {
            "tenant_id": tenant.id,
            "tenant_name": tenant.name,
            "business_unit_id": bu.id,
            "location_id": loc.id,
            "membership_id": membership.id
        }
