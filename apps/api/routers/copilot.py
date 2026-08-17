import uuid
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from packages.security.dependencies import get_secure_session, get_tenant_id_from_header, get_current_user, TokenPayload
from modules.intelligence.copilot_service import CopilotService

router = APIRouter(tags=["Copilot"], prefix="/copilot")


class ChatPromptPayload(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    prompt: str = Field(..., example="Qual é o nosso Prime Cost atual e como reduzir o CMV?")

class DispatchBriefingPayload(BaseModel):
    channel: str = "WHATSAPP" # WHATSAPP, WEBHOOK, EMAIL
    destination: Optional[str] = None # Phone or Webhook URL


@router.post("/chat")
async def chat_with_copilot(
    payload: ChatPromptPayload,
    user: TokenPayload = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = CopilotService(db)
    u_id = None
    if user and user.sub:
        try:
            u_id = uuid.UUID(user.sub)
        except ValueError:
            u_id = None

    return await service.process_user_message(
        tenant_id=tenant_id,
        user_id=u_id,
        conversation_id=payload.conversation_id,
        user_prompt=payload.prompt
    )



@router.get("/conversations")
async def list_conversations(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = CopilotService(db)
    return await service.list_conversations(tenant_id)


@router.get("/audit")
async def get_360_audit(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = CopilotService(db)
    return await service.audit_restaurant_360(tenant_id)


@router.get("/briefings/today")
async def get_today_briefing(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = CopilotService(db)
    return await service.generate_executive_briefing(tenant_id)


@router.post("/briefings/dispatch")
async def dispatch_briefing(
    payload: DispatchBriefingPayload,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session)
):
    service = CopilotService(db)
    briefing = await service.generate_executive_briefing(tenant_id)
    return {
        "status": "DISPATCHED",
        "channel": payload.channel,
        "destination": payload.destination or "+55 (11) 99999-8888",
        "message": briefing["summary_text"]
    }
