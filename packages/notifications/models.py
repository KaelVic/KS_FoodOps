import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from packages.tenant.database import Base

class Notification(Base):
    """
    Operational alerts and notifications (e.g. stock below minimum).
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True) # If null, it's a tenant-wide alert (e.g. for all admins)
    
    type = Column(String(100), nullable=False, index=True) # e.g. 'STOCK_ALERT', 'INVENTORY_DIVERGENCE'
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    
    metadata_payload = Column(JSONB, nullable=True) # Context like {'sku_id': '...'}
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class NotificationPreference(Base):
    """
    User preferences for receiving notifications.
    """
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    type = Column(String(100), nullable=False) # e.g. 'STOCK_ALERT'
    email_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    
    __table_args__ = (
        Index("ix_notification_preferences_user_type", "tenant_id", "user_id", "type", unique=True),
    )
