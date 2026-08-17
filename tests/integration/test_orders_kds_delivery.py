import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text


@pytest.mark.asyncio
async def test_dining_tables_crud_and_status(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create a dining table
    r_create = await async_client.post("/orders/tables", json={
        "table_number": "Mesa 01",
        "capacity": 4,
        "section": "Salão Principal",
        "status": "AVAILABLE"
    }, headers=auth_headers)
    assert r_create.status_code in [200, 201], r_create.text
    table_data = r_create.json()
    assert table_data["table_number"] == "Mesa 01"
    assert table_data["status"] == "AVAILABLE"
    table_id = table_data["id"]

    # 2. List tables
    r_list = await async_client.get("/orders/tables", headers=auth_headers)
    assert r_list.status_code == 200, r_list.text
    tables = r_list.json()
    assert any(t["id"] == table_id for t in tables)

    # 3. Update table status
    r_status = await async_client.patch(f"/orders/tables/{table_id}/status", json={
        "status": "RESERVED"
    }, headers=auth_headers)
    assert r_status.status_code == 200, r_status.text
    assert r_status.json()["status"] == "RESERVED"


@pytest.mark.asyncio
async def test_order_lifecycle_and_kds_queue(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create a table
    r_tab = await async_client.post("/orders/tables", json={
        "table_number": "Mesa 10",
        "capacity": 6,
        "section": "Varanda"
    }, headers=auth_headers)
    assert r_tab.status_code in [200, 201]
    table_id = r_tab.json()["id"]

    # 2. Open an Order for the table with 2 items (Kitchen + Bar)
    r_order = await async_client.post("/orders", json={
        "channel": "DINE_IN",
        "table_id": table_id,
        "waiter_name": "Marcos",
        "customer_name": "Família Souza",
        "items": [
            {
                "name": "Picanha na Chapa 500g",
                "quantity": "1.00",
                "unit_price": "110.00",
                "production_station": "KITCHEN",
                "preparation_notes": "Ao ponto para mal"
            },
            {
                "name": "Caipirinha de Limão",
                "quantity": "2.00",
                "unit_price": "25.00",
                "production_station": "BAR",
                "preparation_notes": "Com adoçante"
            }
        ]
    }, headers=auth_headers)
    assert r_order.status_code in [200, 201], r_order.text
    order = r_order.json()
    assert order["total_amount"] == 160.0 # 110 + (25*2)
    order_id = order["id"]

    # Check table status became OCCUPIED
    r_tab_check = await async_client.get("/orders/tables", headers=auth_headers)
    table_check = next(t for t in r_tab_check.json() if t["id"] == table_id)
    assert table_check["status"] == "OCCUPIED"
    assert table_check["active_order_id"] == order_id

    # 3. Check KDS queue
    r_kds = await async_client.get("/orders/kds/queue", headers=auth_headers)
    assert r_kds.status_code == 200, r_kds.text
    kds_items = r_kds.json()
    assert len(kds_items) >= 2

    kitchen_item = next(i for i in kds_items if i["order_number"] == order["order_number"] and i["item_name"] == "Picanha na Chapa 500g")
    assert kitchen_item["table_number"] == "Mesa 10"
    assert kitchen_item["status"] == "QUEUED"

    # 4. Advance KDS item status
    kds_item_id = kitchen_item["item_id"]
    r_prep = await async_client.patch(f"/orders/items/{kds_item_id}/kds-status", json={
        "status": "PREPARING"
    }, headers=auth_headers)
    assert r_prep.status_code == 200, r_prep.text
    assert r_prep.json()["status"] == "PREPARING"
    assert r_prep.json()["started_at"] is not None

    r_ready = await async_client.patch(f"/orders/items/{kds_item_id}/kds-status", json={
        "status": "READY"
    }, headers=auth_headers)
    assert r_ready.status_code == 200, r_ready.text
    assert r_ready.json()["status"] == "READY"
    assert r_ready.json()["ready_at"] is not None

    # 5. Add more items to the open order
    r_add = await async_client.post(f"/orders/{order_id}/items", json={
        "items": [
            {
                "name": "Petit Gâteau",
                "quantity": "1.00",
                "unit_price": "28.00",
                "production_station": "DESSERT"
            }
        ]
    }, headers=auth_headers)
    assert r_add.status_code == 200, r_add.text
    assert r_add.json()["total_amount"] == 188.0 # 160 + 28


@pytest.mark.asyncio
async def test_order_closing_and_table_release(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create table and order
    r_tab = await async_client.post("/orders/tables", json={
        "table_number": "Mesa 05",
        "capacity": 2
    }, headers=auth_headers)
    table_id = r_tab.json()["id"]

    r_ord = await async_client.post("/orders", json={
        "channel": "DINE_IN",
        "table_id": table_id,
        "items": [
            {"name": "Prato Executivo Salmão", "quantity": "2.00", "unit_price": "50.00"}
        ]
    }, headers=auth_headers)
    order_id = r_ord.json()["id"]

    # 2. Close and pay order
    r_close = await async_client.post(f"/orders/{order_id}/close-and-pay", json={
        "payment_method": "CREDIT_CARD"
    }, headers=auth_headers)
    assert r_close.status_code == 200, r_close.text
    closed = r_close.json()
    assert closed["is_paid"] is True
    assert closed["status"] == "COMPLETED"

    # Verify table released back to AVAILABLE
    r_tabs = await async_client.get("/orders/tables", headers=auth_headers)
    table = next(t for t in r_tabs.json() if t["id"] == table_id)
    assert table["status"] == "AVAILABLE"
    assert table["active_order_id"] is None


@pytest.mark.asyncio
async def test_delivery_hub_kanban_flow(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create delivery order
    r_del = await async_client.post("/orders", json={
        "channel": "DELIVERY",
        "customer_name": "Ana Clara",
        "customer_phone": "11988887777",
        "delivery_address": "Rua Augusta, 500, Apto 101",
        "delivery_fee": "12.00",
        "notes": "Tocar interfone 101",
        "items": [
            {"name": "Hambúrguer Trufado", "quantity": "2.00", "unit_price": "45.00"},
            {"name": "Refrigerante Lata", "quantity": "2.00", "unit_price": "7.00"}
        ]
    }, headers=auth_headers)
    assert r_del.status_code in [200, 201], r_del.text
    del_order = r_del.json()
    assert del_order["total_amount"] == 116.0 # (45*2) + (7*2) + 12
    order_id = del_order["id"]

    # 2. Check Kanban
    r_kanban = await async_client.get("/orders/delivery/kanban", headers=auth_headers)
    assert r_kanban.status_code == 200, r_kanban.text
    kanban = r_kanban.json()
    assert any(o["id"] == order_id for o in kanban["PREPARING"])

    # 3. Advance to OUT_FOR_DELIVERY
    r_up = await async_client.patch(f"/orders/{order_id}/delivery-status", json={
        "status": "OUT_FOR_DELIVERY"
    }, headers=auth_headers)
    assert r_up.status_code == 200, r_up.text
    assert r_up.json()["status"] == "OUT_FOR_DELIVERY"

    # 4. Advance to COMPLETED
    r_comp = await async_client.patch(f"/orders/{order_id}/delivery-status", json={
        "status": "COMPLETED"
    }, headers=auth_headers)
    assert r_comp.status_code == 200, r_comp.text
    assert r_comp.json()["status"] == "COMPLETED"
    assert r_comp.json()["is_paid"] is True


@pytest.mark.asyncio
async def test_cross_tenant_isolation_orders(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create table & order in Tenant A
    r_tab = await async_client.post("/orders/tables", json={
        "table_number": "Mesa Tenant A",
        "capacity": 4
    }, headers=auth_headers)
    assert r_tab.status_code in [200, 201]
    tab_a_id = r_tab.json()["id"]

    # 2. Attempt to view as another Tenant B
    tenant_b_id = str(uuid4())
    headers_b = {"Authorization": auth_headers["Authorization"], "X-Tenant-ID": tenant_b_id}

    r_b_tabs = await async_client.get("/orders/tables", headers=headers_b)
    # RLS or auth should not expose Tenant A's table
    if r_b_tabs.status_code == 200:
        tabs_b = r_b_tabs.json()
        assert not any(t["id"] == tab_a_id for t in tabs_b)
