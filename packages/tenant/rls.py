import contextvars
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event

# Context variable to store the current tenant_id per-request/task
current_tenant_id_var: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "current_tenant_id", default=None
)

def set_current_tenant_id(tenant_id: Optional[UUID]) -> contextvars.Token:
    """Sets the current tenant_id and returns a token to restore it."""
    return current_tenant_id_var.set(tenant_id)

def get_current_tenant_id() -> Optional[UUID]:
    """Gets the current tenant_id from the context."""
    return current_tenant_id_var.get()

def reset_current_tenant_id(token: contextvars.Token) -> None:
    """Restores the current tenant_id from a token."""
    current_tenant_id_var.reset(token)

