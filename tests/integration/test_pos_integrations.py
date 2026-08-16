import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from unittest.mock import patch

@pytest.mark.asyncio
async def test_pos_webhook_totvs(async_client: AsyncClient, tenant_id: str):
    payload = {
        "ReceiptId": "TOTVS-123",
        "Date": "2023-10-01T12:00:00Z",
        "Items": [
            {
                "ProductId": str(uuid.uuid4()),
                "Qty": 2.0,
                "Price": 10.0,
                "Total": 20.0
            }
        ]
    }
    
    with patch('apps.worker.tasks.process_pos_sales_batch_task.delay') as mock_delay:
        response = await async_client.post(
            "/integrations/webhook/totvs",
            json=payload,
            headers={"X-Tenant-ID": tenant_id}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["message"] == "Received payload from totvs. Processing asynchronously."
        assert "webhook_totvs_" in data["import_reference"]
        assert mock_delay.called

@pytest.mark.asyncio
async def test_pos_webhook_unsupported(async_client: AsyncClient):
    response = await async_client.post(
        "/integrations/webhook/unknown_pos",
        json={"data": "test"},
        headers={"X-Tenant-ID": str(uuid.uuid4())}
    )
    assert response.status_code == 400
    assert "Unsupported POS system: unknown_pos" in response.json()["detail"]

@pytest.mark.asyncio
async def test_pos_webhook_missing_tenant(async_client: AsyncClient):
    response = await async_client.post(
        "/integrations/webhook/totvs",
        json={"data": "test"}
    )
    assert response.status_code == 400
    assert "Missing X-Tenant-ID header" in response.json()["detail"]
