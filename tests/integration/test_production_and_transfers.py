import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.catalog.models import SKU, Category, UOM
from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient
from modules.production.models import ProductionOrder, ProductionOrderIngredient
from modules.inventory.models import StockMovement, StockLedgerEntry, StockBalanceProjection, StockTransfer, StockTransferItem
from packages.tenant.models import BusinessUnit, Location


@pytest.mark.asyncio
async def test_production_order_lifecycle_and_ledger_effects(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    t_id = uuid.UUID(tenant_id)

    # 1. Setup Base Data: BusinessUnit, UOM, Location, Category, Raw SKUs and Produced SKU
    bu = BusinessUnit(tenant_id=t_id, name="Unidade Matriz Teste")
    owner_session.add(bu)
    await owner_session.flush()

    uom_kg = UOM(tenant_id=t_id, name="Quilograma", symbol="kg", base_type="mass")
    uom_un = UOM(tenant_id=t_id, name="Unidade", symbol="un", base_type="count")
    cat = Category(tenant_id=t_id, name="Carnes e Pré-preparos")
    loc = Location(tenant_id=t_id, business_unit_id=bu.id, name="Cozinha Central / Açougue")
    owner_session.add_all([uom_kg, uom_un, cat, loc])
    await owner_session.flush()

    sku_carne = SKU(tenant_id=t_id, category_id=cat.id, base_uom_id=uom_kg.id, name="Carne Fraldinha In Natura")
    sku_bacon = SKU(tenant_id=t_id, category_id=cat.id, base_uom_id=uom_kg.id, name="Bacon Especial")
    sku_burger_blend = SKU(tenant_id=t_id, category_id=cat.id, base_uom_id=uom_un.id, name="Blend Burger 180g (Semi-Acabado)")
    owner_session.add_all([sku_carne, sku_bacon, sku_burger_blend])
    await owner_session.flush()

    # Initial Stock Receipts for raw ingredients
    # Carne: 10kg @ R$ 40.00 = R$ 400.00
    # Bacon: 5kg @ R$ 30.00 = R$ 150.00
    mov_init = StockMovement(tenant_id=t_id, location_id=loc.id, type="RECEIPT", status="POSTED")
    owner_session.add(mov_init)
    await owner_session.flush()

    bal_carne = StockBalanceProjection(tenant_id=t_id, location_id=loc.id, sku_id=sku_carne.id, quantity=Decimal("10.00"), total_value=Decimal("400.00"))
    bal_bacon = StockBalanceProjection(tenant_id=t_id, location_id=loc.id, sku_id=sku_bacon.id, quantity=Decimal("5.00"), total_value=Decimal("150.00"))
    owner_session.add_all([bal_carne, bal_bacon])

    led_carne = StockLedgerEntry(tenant_id=t_id, movement_id=mov_init.id, sku_id=sku_carne.id, quantity=Decimal("10.00"), unit_cost=Decimal("40.00"), balance_after=Decimal("10.00"))
    led_bacon = StockLedgerEntry(tenant_id=t_id, movement_id=mov_init.id, sku_id=sku_bacon.id, quantity=Decimal("5.00"), unit_cost=Decimal("30.00"), balance_after=Decimal("5.00"))
    owner_session.add_all([led_carne, led_bacon])

    # 2. Setup Recipe & Version (10 burgers = 1.6kg carne + 0.4kg bacon)
    recipe = Recipe(tenant_id=t_id, name="Ficha Técnica Blend Burger 180g", type="PREPARED_ITEM")
    owner_session.add(recipe)
    await owner_session.flush()

    version = RecipeVersion(
        tenant_id=t_id,
        recipe_id=recipe.id,
        version_number=1,
        status="PUBLISHED",
        yield_quantity=Decimal("10.00"),
        yield_uom_id=uom_un.id,
        portion_size=Decimal("1.00"),
        portion_uom_id=uom_un.id,
    )
    owner_session.add(version)
    await owner_session.flush()

    ing1 = RecipeIngredient(tenant_id=t_id, recipe_version_id=version.id, sku_id=sku_carne.id, quantity=Decimal("1.60"), uom_id=uom_kg.id, loss_percentage=Decimal("0"))
    ing2 = RecipeIngredient(tenant_id=t_id, recipe_version_id=version.id, sku_id=sku_bacon.id, quantity=Decimal("0.40"), uom_id=uom_kg.id, loss_percentage=Decimal("0"))
    owner_session.add_all([ing1, ing2])

    recipe_id_str = str(recipe.id)
    produced_sku_id_str = str(sku_burger_blend.id)
    location_id_str = str(loc.id)

    await owner_session.commit()

    # 3. Create Production Order via API (Planned for 10 burgers)
    r_create = await async_client.post("/production/orders", json={
        "recipe_id": recipe_id_str,
        "produced_sku_id": produced_sku_id_str,
        "location_id": location_id_str,
        "planned_quantity": "10.00",
        "notes": "Batelada matinal de hambúrgueres"
    }, headers=auth_headers)
    assert r_create.status_code == 201, r_create.text
    order = r_create.json()
    order_id = order["id"]
    assert order["status"] == "PLANNED"
    assert order["planned_quantity"] == 10.0
    # Expected estimated cost: 1.6*40 (64) + 0.4*30 (12) = R$ 76.00 (unit cost 7.60)
    assert order["total_cost"] == 76.0
    assert order["unit_cost"] == 7.6

    # 4. Start Production
    r_start = await async_client.post(f"/production/orders/{order_id}/start", headers=auth_headers)
    assert r_start.status_code == 200
    assert r_start.json()["status"] == "IN_PRODUCTION"

    # 5. Complete Production with actual yield 10 units
    r_complete = await async_client.post(f"/production/orders/{order_id}/complete", json={
        "actual_quantity": "10.00",
        "batch_number": "LOTE-BURGER-001",
    }, headers=auth_headers)
    assert r_complete.status_code == 200, r_complete.text
    completed_order = r_complete.json()
    assert completed_order["status"] == "COMPLETED"
    assert completed_order["actual_quantity"] == 10.0
    assert completed_order["total_cost"] == 76.0

    # 6. Verify Stock Ledger Invariants
    # Raw Ingredients stock should be decremented: Carne was 10.0 -> now 8.4, Bacon was 5.0 -> now 4.6
    # Produced SKU should be created: Blend Burger was 0.0 -> now 10.0
    r_balances = await async_client.get(f"/inventory/balances?location_id={location_id_str}", headers=auth_headers)
    assert r_balances.status_code == 200
    b_map = {b["sku_name"]: b for b in r_balances.json()}

    assert float(b_map["Carne Fraldinha In Natura"]["quantity"]) == 8.4
    assert float(b_map["Bacon Especial"]["quantity"]) == 4.6
    assert float(b_map["Blend Burger 180g (Semi-Acabado)"]["quantity"]) == 10.0
    assert float(b_map["Blend Burger 180g (Semi-Acabado)"]["unit_cost"]) == 7.6


@pytest.mark.asyncio
async def test_stock_transfer_lifecycle_between_locations(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    t_id = uuid.UUID(tenant_id)

    # 1. Setup BusinessUnit and 2 Locations: Cozinha Central (Origin) and Salão Loja 1 (Destination)
    bu = BusinessUnit(tenant_id=t_id, name="Unidade Matriz Transfer")
    owner_session.add(bu)
    await owner_session.flush()

    uom = UOM(tenant_id=t_id, name="Unidade", symbol="un", base_type="count")
    cat = Category(tenant_id=t_id, name="Bebidas e Vinhos")
    loc_orig = Location(tenant_id=t_id, business_unit_id=bu.id, name="Depósito Central")
    loc_dest = Location(tenant_id=t_id, business_unit_id=bu.id, name="Bar Salão")
    owner_session.add_all([uom, cat, loc_orig, loc_dest])
    await owner_session.flush()

    sku_cerveja = SKU(tenant_id=t_id, category_id=cat.id, base_uom_id=uom.id, name="Cerveja Artesanal IPA 500ml")
    owner_session.add(sku_cerveja)
    await owner_session.flush()

    # Initial stock at Origin: 50 units @ R$ 12.00 = R$ 600.00
    mov_init = StockMovement(tenant_id=t_id, location_id=loc_orig.id, type="RECEIPT", status="POSTED")
    owner_session.add(mov_init)
    await owner_session.flush()

    bal_orig = StockBalanceProjection(tenant_id=t_id, location_id=loc_orig.id, sku_id=sku_cerveja.id, quantity=Decimal("50.00"), total_value=Decimal("600.00"))
    owner_session.add(bal_orig)
    led_orig = StockLedgerEntry(tenant_id=t_id, movement_id=mov_init.id, sku_id=sku_cerveja.id, quantity=Decimal("50.00"), unit_cost=Decimal("12.00"), balance_after=Decimal("50.00"))
    owner_session.add(led_orig)

    orig_loc_id_str = str(loc_orig.id)
    dest_loc_id_str = str(loc_dest.id)
    sku_cerveja_id_str = str(sku_cerveja.id)

    await owner_session.commit()

    # 2. Create Stock Transfer (20 units from Origin to Destination)
    r_trf = await async_client.post("/inventory/transfers", json={
        "origin_location_id": orig_loc_id_str,
        "destination_location_id": dest_loc_id_str,
        "items": [
            {
                "sku_id": sku_cerveja_id_str,
                "quantity_sent": "20.00"
            }
        ],
        "notes": "Abastecimento diário do bar"
    }, headers=auth_headers)
    assert r_trf.status_code == 201, r_trf.text
    trf = r_trf.json()
    trf_id = trf["id"]
    assert trf["status"] == "DRAFT"
    assert len(trf["items"]) == 1

    # 3. Dispatch Transfer
    r_disp = await async_client.post(f"/inventory/transfers/{trf_id}/dispatch", headers=auth_headers)
    assert r_disp.status_code == 200
    assert r_disp.json()["status"] == "IN_TRANSIT"

    # 4. Receive Transfer
    r_rec = await async_client.post(f"/inventory/transfers/{trf_id}/receive", headers=auth_headers)
    assert r_rec.status_code == 200
    assert r_rec.json()["status"] == "RECEIVED"

    # 5. Check Balances in both locations
    # Origin should be 50 - 20 = 30
    # Destination should be 0 + 20 = 20
    r_bal_orig = await async_client.get(f"/inventory/balances?location_id={orig_loc_id_str}", headers=auth_headers)
    b_orig = next(b for b in r_bal_orig.json() if b["sku_id"] == sku_cerveja_id_str)
    assert float(b_orig["quantity"]) == 30.0

    r_bal_dest = await async_client.get(f"/inventory/balances?location_id={dest_loc_id_str}", headers=auth_headers)
    b_dest = next(b for b in r_bal_dest.json() if b["sku_id"] == sku_cerveja_id_str)
    assert float(b_dest["quantity"]) == 20.0
    assert float(b_dest["unit_cost"]) == 12.0


@pytest.mark.asyncio
async def test_cross_tenant_isolation_production_and_transfers(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession
):
    # Tenant 2
    from packages.tenant.models import Tenant
    tenant_2 = Tenant(name="Restaurante Outro Tenant")
    owner_session.add(tenant_2)
    await owner_session.flush()
    t2_id = tenant_2.id

    bu2 = BusinessUnit(tenant_id=t2_id, name="Unidade T2")
    owner_session.add(bu2)
    await owner_session.flush()

    uom2 = UOM(tenant_id=t2_id, name="Kg", symbol="kg", base_type="mass")
    loc2 = Location(tenant_id=t2_id, business_unit_id=bu2.id, name="Cozinha T2")
    owner_session.add_all([uom2, loc2])
    await owner_session.flush()

    sku2 = SKU(tenant_id=t2_id, base_uom_id=uom2.id, name="Insumo Secreto T2")
    recipe2 = Recipe(tenant_id=t2_id, name="Receita Secreta T2", type="PREPARED_ITEM")
    owner_session.add_all([sku2, recipe2])
    await owner_session.flush()

    version2 = RecipeVersion(tenant_id=t2_id, recipe_id=recipe2.id, version_number=1, status="PUBLISHED", yield_quantity=Decimal("1"), yield_uom_id=uom2.id, portion_size=Decimal("1"), portion_uom_id=uom2.id)
    owner_session.add(version2)
    await owner_session.flush()

    op2 = ProductionOrder(tenant_id=t2_id, order_number="OP-T2-0001", recipe_id=recipe2.id, recipe_version_id=version2.id, produced_sku_id=sku2.id, location_id=loc2.id, status="PLANNED", planned_quantity=Decimal("5"))
    trf2 = StockTransfer(tenant_id=t2_id, transfer_number="TRF-T2-0001", origin_location_id=loc2.id, destination_location_id=loc2.id, status="DRAFT")
    owner_session.add_all([op2, trf2])

    op2_id_str = str(op2.id)
    trf2_id_str = str(trf2.id)

    await owner_session.commit()

    # Query with Tenant 1 auth headers
    r_ops = await async_client.get("/production/orders", headers=auth_headers)
    assert r_ops.status_code == 200
    assert all(o["id"] != op2_id_str for o in r_ops.json())

    r_trfs = await async_client.get("/inventory/transfers", headers=auth_headers)
    assert r_trfs.status_code == 200
    assert all(t["id"] != trf2_id_str for t in r_trfs.json())
