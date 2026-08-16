import pytest
import uuid
import os
import asyncio
from unittest.mock import patch, MagicMock

from sqlalchemy import select, text
from packages.tenant.database import async_session_maker
from packages.tenant.models import Tenant
from apps.worker.tasks import (
    schedule_intelligence_for_all_tenants,
    cleanup_temporary_files_task,
    process_outbox_messages_task
)

async def async_run(coro):
    return await coro

@pytest.mark.asyncio
async def test_schedule_intelligence_task(owner_session):
    """Test that the schedule task dispatches sub-tasks for active tenants."""
    tenant_id = uuid.uuid4()
    await owner_session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
    stmt = text("INSERT INTO tenants (id, name, is_active) VALUES (:id, :name, true) ON CONFLICT DO NOTHING")
    await owner_session.execute(stmt, {"id": tenant_id, "name": "Test Tenant Beat"})
    await owner_session.commit()
    
    with patch("apps.worker.tasks.recalculate_nightly_intelligence_task.delay") as mock_delay:
        with patch("apps.worker.tasks.run_async", side_effect=async_run):
            result = await schedule_intelligence_for_all_tenants()
            assert mock_delay.called
            assert "Dispatched intelligence" in result


@pytest.mark.asyncio
async def test_cleanup_temporary_files():
    """Test that the cleanup task removes old files."""
    os.makedirs("uploads", exist_ok=True)
    file_path = "uploads/old_file.xml"
    with open(file_path, "w") as f:
        f.write("<xml></xml>")
    
    import time
    old_time = time.time() - (48 * 60 * 60)
    os.utime(file_path, (old_time, old_time))
    
    result = cleanup_temporary_files_task()
    assert not os.path.exists(file_path)
    assert "Cleaned" in result


@pytest.mark.asyncio
async def test_process_outbox_messages():
    """Test outbox processing task executes successfully."""
    with patch("packages.jobs.worker.OutboxWorker.process_pending_messages") as mock_process:
        mock_process.return_value = asyncio.Future()
        mock_process.return_value.set_result(None)
        with patch("apps.worker.tasks.run_async", side_effect=async_run):
            result = await process_outbox_messages_task()
            assert result == "Outbox processed"
            assert mock_process.called
