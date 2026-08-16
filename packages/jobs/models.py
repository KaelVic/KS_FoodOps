import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from packages.tenant.database import Base

class OutboxMessage(Base):
    """
    Implements the Transactional Outbox Pattern for reliable async messaging.
    """
    __tablename__ = "outbox_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True) # Optional for global jobs
    
    aggregate_type = Column(String(100), nullable=False) # e.g. 'Order', 'StockMovement'
    aggregate_id = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False) # e.g. 'OrderCreated'
    payload = Column(JSONB, nullable=False)
    
    status = Column(String(50), default='PENDING', nullable=False, index=True) # PENDING, PROCESSED, FAILED
    error_message = Column(Text, nullable=True)
    retry_count = Column(sa.Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
