import uuid
from sqlalchemy import Column, String, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from packages.tenant.database import Base

class AuditLog(Base):
    """
    Immutable audit log for tracking critical operations (stock changes, inventory, settings).
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=False, index=True) # ID of the AppUser who performed the action
    
    action = Column(String(100), nullable=False, index=True) # e.g., "STOCK_MANUAL_ADJUSTMENT", "INVENTORY_CLOSED", "NFE_APPROVED"
    resource_type = Column(String(100), nullable=False, index=True) # e.g., "stock_movements", "inventory_sessions"
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    changes_payload = Column(JSONB, nullable=False, default=dict)
    client_ip = Column(String(45), nullable=True) # IPv6 ready
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Indexes to speed up queries by tenant/resource and time
    __table_args__ = (
        Index("ix_audit_logs_tenant_resource", "tenant_id", "resource_type", "resource_id"),
    )
