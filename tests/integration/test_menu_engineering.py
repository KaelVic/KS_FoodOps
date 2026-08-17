import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text

@pytest.mark.asyncio
async def test_menu_categories_and_items_crud(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create a Menu Category
    r_cat = await async_client.post("/menu/categories", json={
        "name": "Hambúrgueres Artesanais",
        "display_order": 1,
        "is_active": True
    }, headers=auth_headers)
    assert r_cat.status_code in [200, 201], r_cat.text
    cat_id = r_cat.json()["id"]

    # 2. List Categories
    r_cats = await async_client.get("/menu/categories", headers=auth_headers)
    assert r_cats.status_code == 200, r_cats.text
    cats = r_cats.json()
    assert any(c["id"] == cat_id for c in cats)

    # 3. Create a Menu Item
    r_item = await async_client.post("/menu/items", json={
        "category_id": cat_id,
        "name": "Classic Smash Burger",
        "pos_code": "SMASH-01",
        "description": "Blend 160g, queijo cheddar inglês e maionese da casa",
        "sale_price": "38.00",
        "cost_price": "11.40",
        "target_cmv_percentage": "30.00",
        "is_active": True
    }, headers=auth_headers)
    assert r_item.status_code in [200, 201], r_item.text
    item_data = r_item.json()
    assert item_data["name"] == "Classic Smash Burger"
    assert item_data["sale_price"] == 38.0
    assert item_data["cost_price"] == 11.4
    assert item_data["cmv_pct"] == 30.0
    item_id = item_data["id"]

    # 4. Update Menu Item Price
    r_up = await async_client.put(f"/menu/items/{item_id}", json={
        "sale_price": "42.00"
    }, headers=auth_headers)
    assert r_up.status_code == 200, r_up.text
    assert r_up.json()["sale_price"] == 42.0

    # 5. List Menu Items
    r_list = await async_client.get("/menu/items", headers=auth_headers)
    assert r_list.status_code == 200, r_list.text
    items = r_list.json()
    assert any(i["id"] == item_id for i in items)


@pytest.mark.asyncio
async def test_menu_engineering_bcg_matrix(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create Category
    r_cat = await async_client.post("/menu/categories", json={"name": "Pratos Principais"}, headers=auth_headers)
    cat_id = r_cat.json()["id"]

    # 2. Create 4 Distinct Items:
    # Item 1: High Price 50, Low Cost 15 -> High Margin (35)
    r_star = await async_client.post("/menu/items", json={
        "category_id": cat_id,
        "name": "Picanha Premium Grelhada",
        "pos_code": "POS-STAR-01",
        "sale_price": "60.00",
        "cost_price": "18.00" # Margin = 42.00
    }, headers=auth_headers)
    
    # Item 2: Low Margin (Price 25, Cost 18 -> Margin = 7)
    r_plow = await async_client.post("/menu/items", json={
        "category_id": cat_id,
        "name": "Batata Frita Rústica Família",
        "pos_code": "POS-PLOW-02",
        "sale_price": "25.00",
        "cost_price": "18.00" # Margin = 7.00
    }, headers=auth_headers)

    # Item 3: High Margin (Price 70, Cost 20 -> Margin = 50)
    r_puz = await async_client.post("/menu/items", json={
        "category_id": cat_id,
        "name": "Salmão com Crosta de Pistache",
        "pos_code": "POS-PUZ-03",
        "sale_price": "70.00",
        "cost_price": "20.00" # Margin = 50.00
    }, headers=auth_headers)

    # Item 4: Low Margin (Price 20, Cost 15 -> Margin = 5)
    r_dog = await async_client.post("/menu/items", json={
        "category_id": cat_id,
        "name": "Salada Simples",
        "pos_code": "POS-DOG-04",
        "sale_price": "20.00",
        "cost_price": "15.00" # Margin = 5.00
    }, headers=auth_headers)

    # 3. Seed Sales Import & Sale Lines:
    imp_id = uuid4()
    sale_id = uuid4()
    now_iso = datetime.now(timezone.utc)
    
    await owner_session.execute(
        text("INSERT INTO sales_imports (id, tenant_id, pos_system, import_reference, status) VALUES (:id, :tid, 'POS_TEST', :ref, 'COMPLETED')"),
        {"id": str(imp_id), "tid": tenant_id, "ref": f"REF-{uuid4()}"}
    )
    await owner_session.execute(
        text("INSERT INTO sales (id, tenant_id, sales_import_id, pos_sale_id, sale_date, total_amount) VALUES (:id, :tid, :imp_id, 'SALE-999', :dt, 5000)"),
        {"id": str(sale_id), "tid": tenant_id, "imp_id": str(imp_id), "dt": now_iso}
    )
    
    # Add sale lines:
    # Star: 40 units sold
    await owner_session.execute(
        text("INSERT INTO sale_lines (id, tenant_id, sale_id, pos_product_id, quantity, unit_price) VALUES (:id, :tid, :sid, 'POS-STAR-01', 40, 60.00)"),
        {"id": str(uuid4()), "tid": tenant_id, "sid": str(sale_id)}
    )
    # Plowhorse: 35 units sold
    await owner_session.execute(
        text("INSERT INTO sale_lines (id, tenant_id, sale_id, pos_product_id, quantity, unit_price) VALUES (:id, :tid, :sid, 'POS-PLOW-02', 35, 25.00)"),
        {"id": str(uuid4()), "tid": tenant_id, "sid": str(sale_id)}
    )
    # Puzzle: 3 units sold
    await owner_session.execute(
        text("INSERT INTO sale_lines (id, tenant_id, sale_id, pos_product_id, quantity, unit_price) VALUES (:id, :tid, :sid, 'POS-PUZ-03', 3, 70.00)"),
        {"id": str(uuid4()), "tid": tenant_id, "sid": str(sale_id)}
    )
    # Dog: 2 units sold
    await owner_session.execute(
        text("INSERT INTO sale_lines (id, tenant_id, sale_id, pos_product_id, quantity, unit_price) VALUES (:id, :tid, :sid, 'POS-DOG-04', 2, 20.00)"),
        {"id": str(uuid4()), "tid": tenant_id, "sid": str(sale_id)}
    )
    await owner_session.commit()

    # 4. Fetch Menu Engineering Analysis
    r_eng = await async_client.get("/menu/engineering", headers=auth_headers)
    assert r_eng.status_code == 200, r_eng.text
    eng_data = r_eng.json()

    assert "summary" in eng_data
    assert "bcg_distribution" in eng_data
    assert "items" in eng_data
    assert len(eng_data["items"]) >= 4

    items = eng_data["items"]
    star_item = next((i for i in items if i["pos_code"] == "POS-STAR-01"), None)
    plow_item = next((i for i in items if i["pos_code"] == "POS-PLOW-02"), None)
    puz_item = next((i for i in items if i["pos_code"] == "POS-PUZ-03"), None)
    dog_item = next((i for i in items if i["pos_code"] == "POS-DOG-04"), None)

    assert star_item is not None and star_item["classification"] == "STAR"
    assert plow_item is not None and plow_item["classification"] == "PLOWHORSE"
    assert puz_item is not None and puz_item["classification"] == "PUZZLE"
    assert dog_item is not None and dog_item["classification"] == "DOG"


@pytest.mark.asyncio
async def test_pricing_simulator(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create an item with cost $15.00 and price $40.00 (CMV = 37.5%)
    r_item = await async_client.post("/menu/items", json={
        "name": "Risoto de Cogumelos",
        "sale_price": "40.00",
        "cost_price": "15.00",
        "target_cmv_percentage": "25.00"
    }, headers=auth_headers)
    assert r_item.status_code in [200, 201], r_item.text
    item_id = r_item.json()["id"]

    # 2. Simulate Target CMV of 25% -> Proposed price should be $60.00
    r_sim = await async_client.post(f"/menu/items/{item_id}/simulate-pricing", json={
        "target_cmv_pct": "25.00"
    }, headers=auth_headers)
    assert r_sim.status_code == 200, r_sim.text
    sim_data = r_sim.json()

    assert sim_data["cost_price"] == 15.0
    assert sim_data["current_price"] == 40.0
    assert sim_data["proposed_price"] == 60.0
    assert sim_data["resulting_cmv_pct"] == 25.0
    assert sim_data["margin_delta"] == 20.0 # From $25 margin to $45 margin


@pytest.mark.asyncio
async def test_cross_tenant_isolation_menu(
    async_client: AsyncClient, auth_headers: dict, owner_session, tenant_id: str
):
    # 1. Create Category and Item in Tenant 1
    r_cat = await async_client.post("/menu/categories", json={"name": "Tenant 1 Drinks"}, headers=auth_headers)
    cat_id = r_cat.json()["id"]
    r_item = await async_client.post("/menu/items", json={
        "category_id": cat_id,
        "name": "Caipirinha Tenant 1",
        "sale_price": "22.00",
        "cost_price": "5.00"
    }, headers=auth_headers)
    item_id = r_item.json()["id"]

    # 2. Create Tenant 2 and membership
    t2_id = str(uuid4())
    await owner_session.execute(
        text("INSERT INTO tenants (id, name) VALUES (:id, :name)"),
        {"id": t2_id, "name": "Tenant 2"}
    )
    await owner_session.execute(
        text("INSERT INTO tenant_memberships (id, tenant_id, user_id, role) VALUES (:id, :tenant_id, 'test-user-123', 'admin')"),
        {"id": str(uuid4()), "tenant_id": t2_id}
    )
    await owner_session.commit()

    t2_headers = {
        "X-Tenant-ID": t2_id,
        "Authorization": auth_headers.get("Authorization", "")
    }

    # 3. Tenant 2 listing menu items must not see Tenant 1 item
    r_t2_items = await async_client.get("/menu/items", headers=t2_headers)
    assert r_t2_items.status_code == 200
    assert not any(i["id"] == item_id for i in r_t2_items.json())

    # 4. Tenant 2 trying to update Tenant 1 item should get 404
    r_t2_up = await async_client.put(f"/menu/items/{item_id}", json={"sale_price": "99.00"}, headers=t2_headers)
    assert r_t2_up.status_code == 404
