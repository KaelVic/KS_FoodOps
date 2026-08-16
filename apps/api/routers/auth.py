import os
import jwt
from datetime import datetime, timedelta, timezone
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from apps.api.main import limiter
from packages.tenant.database import get_db
from packages.security.models import AppUser
from packages.security.password import verify_password
from packages.security.dependencies import get_current_user
from packages.security.auth import TokenPayload
from packages.tenant.models import TenantMembership, Tenant

router = APIRouter()

# Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]

class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    tenants: List[TenantResponse]

class MeResponse(BaseModel):
    user: UserResponse
    tenants: List[TenantResponse]

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Fetch user
    result = await db.execute(select(AppUser).where(AppUser.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account disabled"
        )

    from sqlalchemy import text
    # Fetch memberships + tenants using SECURITY DEFINER function to bypass RLS restrictions on tenant_memberships
    result = await db.execute(
        text("SELECT tenant_id, role, name FROM get_user_tenants(:uid)"),
        {"uid": str(user.id)}
    )
    memberships = result.all()

    tenant_responses = [
        TenantResponse(id=row.tenant_id, name=row.name, role=row.role)
        for row in memberships
    ]

    # Generate JWT
    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    exp = datetime.now(timezone.utc) + timedelta(hours=8)
    
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": exp
    }
    
    access_token = jwt.encode(payload, secret, algorithm=algorithm)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user.id, email=user.email, full_name=user.full_name),
        tenants=tenant_responses
    )

@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_uuid = uuid.UUID(current_user.sub)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    result = await db.execute(select(AppUser).where(AppUser.id == user_uuid))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from sqlalchemy import text
    result = await db.execute(
        text("SELECT tenant_id, role, name FROM get_user_tenants(:uid)"),
        {"uid": str(user.id)}
    )
    memberships = result.all()

    tenant_responses = [
        TenantResponse(id=row.tenant_id, name=row.name, role=row.role)
        for row in memberships
    ]

    return MeResponse(
        user=UserResponse(id=user.id, email=user.email, full_name=user.full_name),
        tenants=tenant_responses
    )
