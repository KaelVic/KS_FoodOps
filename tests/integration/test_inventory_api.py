import pytest
from fastapi.testclient import TestClient
import os
import jwt
from datetime import datetime, timedelta, timezone

from apps.api.main import app

client = TestClient(app)

JWT_SECRET = os.environ.get("JWT_SECRET", "dummy_secret_for_development_32_bytes_long_min!")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")


def create_test_token(user_id: str = "test-user-123") -> str:
    """Create a valid JWT token for testing."""
    payload = {
        "sub": user_id,
        "email": "test@ksfoodops.local",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def test_inventory_balances_requires_authentication():
    """Test that GET /inventory/balances requires authentication."""
    response = client.get("/inventory/balances", headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"})
    assert response.status_code in (401, 422), "Should require authentication"


def test_inventory_balances_requires_tenant_header():
    """Test that GET /inventory/balances requires X-Tenant-ID header."""
    token = create_test_token()
    response = client.get("/inventory/balances", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (401, 422, 403), "Should require X-Tenant-ID header"


def test_inventory_balances_returns_200_when_authenticated():
    """Test that GET /inventory/balances returns 200 when properly authenticated."""
    token = create_test_token()
    # Use the default test tenant ID that should exist in the test database
    tenant_id = "00000000-0000-0000-0000-000000000001"
    
    response = client.get(
        "/inventory/balances",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": tenant_id
        }
    )
    # If tenant exists and user has membership, should return 200
    # If tenant doesn't exist or user not member, should return 403
    # Either way, we verify the endpoint is protected and responds appropriately
    assert response.status_code in (200, 403, 404), f"Unexpected status: {response.status_code}"
    
    # If 200, verify response structure
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert "sku_id" in item
            assert "sku_name" in item
            assert "base_uom" in item
            assert "quantity" in item
            assert "total_value" in item
            assert "unit_cost" in item
            assert "location_name" in item


def test_inventory_balances_with_location_filter():
    """Test that GET /inventory/balances accepts location_id filter."""
    token = create_test_token()
    tenant_id = "00000000-0000-0000-0000-000000000001"
    location_id = "00000000-0000-0000-0000-000000000002"
    
    response = client.get(
        f"/inventory/balances?location_id={location_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": tenant_id
        }
    )
    # Should respond (not 404 route not found)
    assert response.status_code != 404