import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy import text

pytestmark = pytest.mark.asyncio


async def test_create_purchase_order(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    """POST /purchasing/orders creates a DRAFT purchase order."""

    # ------------------------------------------------------------------
    # Seed: all inserts through owner_session to bypass RLS
    # ------------------------------------------------------------------
    bu_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :tid, 'BU PO')"),
        {"id": str(bu_id), "tid": tenant_id},
    )

    loc_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO locations (id, tenant_id, business_unit_id, name) "
            "VALUES (:id, :tid, :bu_id, 'Loc PO')"
        ),
        {"id": str(loc_id), "tid": tenant_id, "bu_id": str(bu_id)},
    )

    sup_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO suppliers (id, tenant_id, name) VALUES (:id, :tid, 'Test Supplier')"),
        {"id": str(sup_id), "tid": tenant_id},
    )

    uom_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO uoms (id, tenant_id, symbol, name, base_type) "
            "VALUES (:id, :tid, 'KG', 'Kilogram', 'mass')"
        ),
        {"id": str(uom_id), "tid": tenant_id},
    )

    cat_id = uuid4()
    await owner_session.execute(
        text("INSERT INTO categories (id, tenant_id, name) VALUES (:id, :tid, 'Cat PO')"),
        {"id": str(cat_id), "tid": tenant_id},
    )

    sku_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO skus (id, tenant_id, name, base_uom_id, category_id) "
            "VALUES (:id, :tid, 'Test SKU PO', :uom_id, :cat_id)"
        ),
        {"id": str(sku_id), "tid": tenant_id, "uom_id": str(uom_id), "cat_id": str(cat_id)},
    )
    await owner_session.commit()

    # ------------------------------------------------------------------
    # API call
    # ------------------------------------------------------------------
    payload = {
        "supplier_id": str(sup_id),
        "location_id": str(loc_id),
        "lines": [
            {
                "sku_id": str(sku_id),
                "ordered_quantity": "100.00",
                "unit_price": "5.50",
            }
        ],
    }

    response = await async_client.post(
        "/purchasing/orders",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == "DRAFT"
