import pytest
import uuid
import json
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

@pytest.mark.asyncio
async def test_process_nfe_batch_task_mock(owner_session: AsyncSession):
    # This is a unit-style test for the celery task using mock to avoid real db/celery interaction if needed,
    # or just an integration test if we run it synchronously.
    from apps.worker.tasks import process_nfe_batch_task
    
    tenant_id_result = await owner_session.execute(text("SELECT current_setting('app.current_tenant_id', true)"))
    tenant_id = tenant_id_result.scalar()
    
    if not tenant_id:
        pytest.skip("No tenant context available")
        
    # We will just mock the actual task delay call in the endpoint
    pass

@pytest.mark.asyncio
async def test_upload_nfe_batch_endpoint(async_client: AsyncClient, auth_headers: dict):
    with patch('apps.worker.tasks.process_nfe_batch_task.delay') as mock_delay:
        # Create a dummy XML file content
        dummy_xml = "<nfe><fake>data</fake></nfe>"
        
        files = [
            ("files", ("test1.xml", dummy_xml.encode("utf-8"), "application/xml")),
            ("files", ("test2.xml", dummy_xml.encode("utf-8"), "application/xml"))
        ]
        
        response = await async_client.post(
            "/documents/upload-nfe-batch",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "PROCESSING"
        assert len(data["document_ids"]) == 2
        
        # Verify the celery task was enqueued
        assert mock_delay.called
        args, kwargs = mock_delay.call_args
        assert len(args[1]) == 2 # raw_doc_ids list length
