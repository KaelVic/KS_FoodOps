from typing import AsyncGenerator, Callable, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from packages.tenant.database import get_db
from packages.tenant.models import TenantMembership
from packages.tenant.rls import set_current_tenant_id, reset_current_tenant_id
from .auth import decode_jwt, TokenPayload
from .rbac import has_permission

def get_token(request: Request, authorization: Optional[str] = Header(None, description="Bearer token")) -> str:
    """Extract token from Authorization header or fallback to session_token cookie."""
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth format")
        return authorization.replace("Bearer ", "")
    
    cookie_token = request.cookies.get("session_token")
    if cookie_token:
        return cookie_token
        
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

def get_current_user(token: str = Depends(get_token)) -> TokenPayload:
    try:
        return decode_jwt(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_tenant_id_from_header(request: Request, x_tenant_id: Optional[UUID] = Header(None, description="Target Tenant ID")) -> UUID:
    """Extract tenant_id from X-Tenant-ID header or fallback to active_tenant_id cookie."""
    if x_tenant_id:
        return x_tenant_id
    cookie_tenant = request.cookies.get("active_tenant_id")
    if cookie_tenant:
        try:
            return UUID(cookie_tenant)
        except ValueError:
            pass
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing X-Tenant-ID header or active_tenant_id cookie")

async def get_secure_session(
    tenant_id: UUID = Depends(get_tenant_id_from_header),
    user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Validates membership, sets the RLS context, and yields the session.
    This guarantees that the session cannot query outside the tenant.
    """
    # 1. Inject RLS context at session level
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
        {"tenant_id": str(tenant_id)}
    )

    # 2. Verify membership
    stmt = select(TenantMembership).where(
        TenantMembership.user_id == user.sub,
        TenantMembership.tenant_id == tenant_id
    )
    result = await session.execute(stmt)
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to tenant denied")
    
    # 3. Set python context for application code
    token = set_current_tenant_id(tenant_id)
    try:
        session.info["membership"] = membership
        yield session
    finally:
        reset_current_tenant_id(token)

def require_permission(required_permission: str) -> Callable:
    """Dependency factory for RBAC checks."""
    
    async def permission_checker(
        session: AsyncSession = Depends(get_secure_session)
    ):
        membership = session.info.get("membership")
        if not membership or not has_permission(membership.role, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Missing required permission: {required_permission}"
            )
        return True
        
    return permission_checker
