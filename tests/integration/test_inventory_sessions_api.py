import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio


async def test_create_inventory_session(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    """POST /inventory/sessions creates a session linked to a location."""
    from sqlalchemy import text

    # BusinessUnit is required by Location.business_unit_id (nullable=False)
    bu_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO business_units (id, tenant_id, name) "
            "VALUES (:id, :tid, 'Test BU')"
        ),
        {"id": str(bu_id), "tid": tenant_id},
    )
    await owner_session.flush()

    loc_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO locations (id, tenant_id, business_unit_id, name) "
            "VALUES (:id, :tid, :bu_id, 'Test Loc')"
        ),
        {"id": str(loc_id), "tid": tenant_id, "bu_id": str(bu_id)},
    )
    await owner_session.commit()

    response = await async_client.post(
        "/inventory/sessions",
        json={"location_id": str(loc_id)},
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["status"] == "OPEN"


async def test_list_inventory_sessions(
    async_client: AsyncClient, auth_headers: dict, owner_session
):
    """GET /inventory/sessions returns a list."""
    response = await async_client.get("/inventory/sessions", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)
