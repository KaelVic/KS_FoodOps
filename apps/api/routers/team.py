import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession
from packages.security.dependencies import get_secure_session, get_tenant_id_from_header
from packages.tenant.service import TenantService

router = APIRouter()

class MembershipBase(BaseModel):
    user_id: str = Field(..., example="user-123")
    role: str = Field(..., example="manager")

class MembershipUpdate(BaseModel):
    role: str

class MembershipResponse(MembershipBase):
    id: uuid.UUID
    tenant_id: uuid.UUID

    class Config:
        from_attributes = True

@router.get("", response_model=List[MembershipResponse])
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
