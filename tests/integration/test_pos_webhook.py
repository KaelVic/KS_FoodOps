import pytest
import uuid
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_pos_webhook_totvs(async_client: AsyncClient, tenant_id: uuid.UUID):
    payload = {
        "saleId": "12345",
        "timestamp": "2026-08-15T12:00:00Z",
        "value": 150.00,
        "items": [
            {
                "productCode": "P1",
                "quantity": 2,
                "price": 75.00
            }
        ]
    }

    response = await async_client.post(
        "/integrations/webhook/totvs",
        json=payload,
        headers={"X-Tenant-ID": str(tenant_id)}
    )

    assert response.status_code == 202
    data = response.json()
    assert "webhook_totvs" in data["import_reference"]
    assert "Processing asynchronously" in data["message"]

@pytest.mark.asyncio
async def test_pos_webhook_missing_tenant(async_client: AsyncClient):
    payload = {"dummy": "data"}

    response = await async_client.post(
        "/integrations/webhook/totvs",
        json=payload
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Missing X-Tenant-ID header"
