import os
from celery import Celery

REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ks_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["apps.worker.tasks"]
)

from celery.schedules import crontab

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "nightly_intelligence": {
            "task": "apps.worker.tasks.schedule_intelligence_for_all_tenants",
            "schedule": crontab(hour=2, minute=0),
        },
        "cleanup_temporary_files": {
            "task": "apps.worker.tasks.cleanup_temporary_files_task",
            "schedule": crontab(hour=4, minute=0),
        },
        "process_outbox_messages": {
            "task": "apps.worker.tasks.process_outbox_messages_task",
            "schedule": 60.0, # Every 60 seconds
        },
    }
)

import asyncio
from contextlib import asynccontextmanager
from sqlalchemy import text
from packages.tenant.database import async_session_maker
from packages.tenant.rls import set_current_tenant_id, reset_current_tenant_id
import uuid

@asynccontextmanager
async def tenant_session(tenant_id: str | uuid.UUID):
    """
    Context manager to yield a database session with RLS configured for the given tenant.
    Celery tasks must use this to interact with the database securely.
    """
    if isinstance(tenant_id, str):
        tenant_id = uuid.UUID(tenant_id)
        
    token = set_current_tenant_id(tenant_id)
    async with async_session_maker() as session:
        # Use 'false' for session-level so it survives commit()
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
            {"tenant_id": str(tenant_id)}
        )
        try:
            yield session
        finally:
            # Cleanup for connection pool
            await session.execute(text("SELECT set_config('app.current_tenant_id', '', false)"))
            reset_current_tenant_id(token)

def run_async(coro):
    """Helper to run async code inside a synchronous Celery task."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
