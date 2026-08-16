import uuid
from typing import Any, Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.notifications.models import Notification, NotificationPreference

class NotificationDispatcher:
    """
    Handles dispatching internal system notifications.
    """
    @staticmethod
    async def dispatch_notification(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        type_: str,
        title: str,
        message: str,
        user_id: Optional[uuid.UUID] = None,
        metadata_payload: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """
        Creates an in-app notification. If user_id is provided, it targets a specific user.
        Otherwise, it is a tenant-wide notification.
        """
        notification = Notification(
            tenant_id=tenant_id,
            user_id=user_id,
            type=type_,
            title=title,
            message=message,
            metadata_payload=metadata_payload or {}
        )
        
        db.add(notification)
        await db.flush()
        return notification

    @staticmethod
    async def get_unread_notifications(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50
    ) -> List[Notification]:
        """
        Fetches unread notifications for a specific user within a tenant.
        Includes both user-specific and tenant-wide notifications.
        """
        stmt = select(Notification).where(
            Notification.tenant_id == tenant_id,
            Notification.is_read == False,
            (Notification.user_id == user_id) | (Notification.user_id.is_(None))
        ).order_by(Notification.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def mark_as_read(
        db: AsyncSession,
        notification_id: uuid.UUID
    ) -> Optional[Notification]:
        """
        Marks a specific notification as read.
        """
        notification = await db.get(Notification, notification_id)
        if notification:
            notification.is_read = True
            await db.flush()
        return notification
