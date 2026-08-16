from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from packages.tenant.database import get_db
from packages.security.dependencies import get_current_user
from packages.security.auth import TokenPayload
from packages.tenant.service import TenantService

router = APIRouter()

class OnboardingPayload(BaseModel):
    restaurant_name: str = Field(..., min_length=2, max_length=100, example="Meu Restaurante")

class OnboardingResponse(BaseModel):
    tenant_id: uuid.UUID
    tenant_name: str
    message: str

@router.post("", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
async def complete_onboarding(
    payload: OnboardingPayload,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.sub
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated properly")
    
    try:
        result = await TenantService.create_tenant_onboarding(db, user_id, payload.restaurant_name)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Onboarding failed: {str(e)}")

    return {
        "tenant_id": result["tenant_id"],
        "tenant_name": result["tenant_name"],
        "message": "Onboarding concluído com sucesso."
    }
