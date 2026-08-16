import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from packages.audit.models import AuditLog

class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[uuid.UUID] = None,
        changes_payload: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
    ) -> AuditLog:
        """
        Records an immutable audit log entry.
        """
        audit_entry = AuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes_payload=changes_payload or {},
            client_ip=client_ip
        )
        
        db.add(audit_entry)
        await db.flush()
        return audit_entry
