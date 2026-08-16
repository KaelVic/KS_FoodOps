import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from packages.security.dependencies import get_secure_session, get_current_user, get_tenant_id_from_header
from packages.security.auth import TokenPayload
from packages.notifications.service import NotificationDispatcher

router = APIRouter()

class NotificationResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    type: str
    title: str
    message: str
    metadata_payload: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[NotificationResponse])
async def get_unread_notifications(
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_secure_session)
):
    try:
        user_uuid = uuid.UUID(current_user.sub)
    except Exception:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, str(current_user.sub))

    return await NotificationDispatcher.get_unread_notifications(db, tenant_id, user_uuid)

@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id_from_header),
    db: AsyncSession = Depends(get_secure_session),
    _ = Depends(get_current_user)
):
    notif = await NotificationDispatcher.mark_as_read(db, notification_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif
