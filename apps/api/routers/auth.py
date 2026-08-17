import os
import jwt
from datetime import datetime, timedelta, timezone
import uuid
from typing import List, Optional
import pyotp
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from apps.api.main import limiter
from packages.tenant.database import get_db
from packages.security.models import AppUser
from packages.security.password import verify_password, hash_password
from packages.security.dependencies import get_current_user
from packages.security.auth import TokenPayload
from packages.tenant.models import TenantMembership, Tenant
from packages.tenant.service import TenantService

router = APIRouter()

# Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    restaurant_name: Optional[str] = "Meu Restaurante"

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    is_2fa_enabled: bool = False

class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str

class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user: Optional[UserResponse] = None
    tenants: Optional[List[TenantResponse]] = None
    requires_2fa: bool = False
    temp_token: Optional[str] = None

class MeResponse(BaseModel):
    user: UserResponse
    tenants: List[TenantResponse]

class TwoFactorSetupResponse(BaseModel):
    secret: str
    otpauth_url: str

class TwoFactorEnableRequest(BaseModel):
    code: str

class TwoFactorDisableRequest(BaseModel):
    password: str
    code: str

class TwoFactorChallengeRequest(BaseModel):
    temp_token: str
    code: str

@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Check if email exists
        result = await db.execute(select(AppUser).where(AppUser.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este email já está cadastrado."
            )

        # 2. Hash password & create user
        hashed = hash_password(data.password)
        user = AppUser(
            email=data.email,
            password_hash=hashed,
            full_name=data.full_name,
            is_active=True,
            is_2fa_enabled=False
        )
        db.add(user)
        await db.flush()

        # 3. Create Tenant and default admin membership
        onboard_res = await TenantService.create_tenant_onboarding(
            db, str(user.id), data.restaurant_name or "Meu Restaurante"
        )
        await db.commit()

        # 4. Generate JWT
        secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
        algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
        exp = datetime.now(timezone.utc) + timedelta(hours=8)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": exp
        }
        access_token = jwt.encode(payload, secret, algorithm=algorithm)

        tenant_responses = [
            TenantResponse(id=onboard_res["tenant_id"], name=onboard_res["tenant_name"], role="admin")
        ]

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(id=user.id, email=user.email, full_name=user.full_name, is_2fa_enabled=False),
            tenants=tenant_responses,
            requires_2fa=False
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao registrar: {str(e)}"
        )

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

    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")

    # If 2FA is enabled, issue a short-lived temp token (5 min) requiring 2FA verification
    if user.is_2fa_enabled:
        temp_exp = datetime.now(timezone.utc) + timedelta(minutes=5)
        temp_payload = {
            "sub": str(user.id),
            "email": user.email,
            "type": "2fa_temp",
            "exp": temp_exp
        }
        temp_token = jwt.encode(temp_payload, secret, algorithm=algorithm)
        return LoginResponse(
            requires_2fa=True,
            temp_token=temp_token
        )

    # Standard login without 2FA
    result = await db.execute(
        text("SELECT tenant_id, role, name FROM get_user_tenants(:uid)"),
        {"uid": str(user.id)}
    )
    memberships = result.all()

    tenant_responses = [
        TenantResponse(id=row.tenant_id, name=row.name, role=row.role)
        for row in memberships
    ]

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
        user=UserResponse(id=user.id, email=user.email, full_name=user.full_name, is_2fa_enabled=user.is_2fa_enabled),
        tenants=tenant_responses,
        requires_2fa=False
    )

@router.post("/2fa/challenge", response_model=LoginResponse)
@limiter.limit("5/minute")
async def verify_2fa_challenge(request: Request, data: TwoFactorChallengeRequest, db: AsyncSession = Depends(get_db)):
    """Verifies the TOTP code against the temporary login token and completes authentication."""
    secret = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")

    try:
        payload = jwt.decode(data.temp_token, secret, algorithms=[algorithm])
        if payload.get("type") != "2fa_temp":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_uuid = uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired 2FA token")

    result = await db.execute(select(AppUser).where(AppUser.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not user.is_2fa_enabled or not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="2FA validation failed")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(data.code.strip()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Código de verificação inválido")

    # Fetch tenants
    result = await db.execute(
        text("SELECT tenant_id, role, name FROM get_user_tenants(:uid)"),
        {"uid": str(user.id)}
    )
    memberships = result.all()

    tenant_responses = [
        TenantResponse(id=row.tenant_id, name=row.name, role=row.role)
        for row in memberships
    ]

    exp = datetime.now(timezone.utc) + timedelta(hours=8)
    auth_payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": exp
    }
    access_token = jwt.encode(auth_payload, secret, algorithm=algorithm)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user.id, email=user.email, full_name=user.full_name, is_2fa_enabled=True),
        tenants=tenant_responses,
        requires_2fa=False
    )

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates a new TOTP secret for the user to scan via QR code in Google Authenticator/Authy."""
    user_uuid = uuid.UUID(current_user.sub)
    result = await db.execute(select(AppUser).where(AppUser.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(name=user.email, issuer_name="KS FoodOps")

    user.totp_secret = secret
    await db.commit()

    return TwoFactorSetupResponse(
        secret=secret,
        otpauth_url=otpauth_url
    )

@router.post("/2fa/enable")
async def enable_2fa(
    data: TwoFactorEnableRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enables 2FA after verifying the first 6-digit code."""
    user_uuid = uuid.UUID(current_user.sub)
    result = await db.execute(select(AppUser).where(AppUser.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user or not user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA setup must be initiated first")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(data.code.strip()):
        raise HTTPException(status_code=400, detail="Código de verificação 2FA inválido")

    user.is_2fa_enabled = True
    await db.commit()

    return {"success": True, "message": "2FA ativado com sucesso"}

@router.post("/2fa/disable")
async def disable_2fa(
    data: TwoFactorDisableRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disables 2FA with password confirmation and current code verification."""
    user_uuid = uuid.UUID(current_user.sub)
    result = await db.execute(select(AppUser).where(AppUser.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user or not user.is_2fa_enabled or not user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA não está ativo nesta conta")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Senha incorreta")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(data.code.strip()):
        raise HTTPException(status_code=400, detail="Código 2FA inválido")

    user.is_2fa_enabled = False
    user.totp_secret = None
    await db.commit()

    return {"success": True, "message": "2FA desativado com sucesso"}

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
        user=UserResponse(id=user.id, email=user.email, full_name=user.full_name, is_2fa_enabled=user.is_2fa_enabled),
        tenants=tenant_responses
    )

