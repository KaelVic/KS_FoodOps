import pytest
import uuid
from modules.integrations.service import IntegrationService

@pytest.mark.asyncio
async def test_sync_ifood_sales():
    """
    Tests that iFood sales are fetched and synchronized correctly.
    """
    tenant_id = uuid.uuid4()
    credentials = {"client_id": "test", "client_secret": "test"}
    
    # Sync sales
    count = await IntegrationService.sync_sales(tenant_id, "ifood", credentials, "2026-08-15")
    
    # Based on the mocked iFood adapter, it returns 2 events, 1 is PLACED.
    assert count == 1

@pytest.mark.asyncio
async def test_sync_totvs_sales():
    """
    Tests that TOTVS sales are fetched and synchronized correctly.
    """
    tenant_id = uuid.uuid4()
    credentials = {"api_key": "test_key"}
    
    # Sync sales
    count = await IntegrationService.sync_sales(tenant_id, "totvs", credentials, "2026-08-15")
    
    # Based on the mocked TOTVS adapter, it returns 1 sale.
    assert count == 1
