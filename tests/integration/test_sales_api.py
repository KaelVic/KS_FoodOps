import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text

pytestmark = pytest.mark.asyncio


async def test_sales_and_losses_endpoints(
    async_client: AsyncClient,
    auth_headers: dict,
    owner_session,
    tenant_id: str,
):
    """
    End-to-end test covering:
      - POST  /inventory/losses
      - GET   /inventory/losses
      - POST  /sales/mappings
      - POST  /sales/import
      - GET   /sales/theoretical-vs-actual
    """
    # ------------------------------------------------------------------
    # Seed via owner_session (bypasses RLS)
    # ------------------------------------------------------------------
    bu_id = uuid4()
    await owner_session.execute(text("DELETE FROM inventory_sessions WHERE tenant_id = :tid"), {"tid": tenant_id})
    await owner_session.execute(text("DELETE FROM accounting_periods WHERE tenant_id = :tid"), {"tid": tenant_id})
    await owner_session.execute(
        text("INSERT INTO business_units (id, tenant_id, name) VALUES (:id, :tid, 'BU Sales')"),
        {"id": str(bu_id), "tid": tenant_id},
    )

    loc_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO locations (id, tenant_id, business_unit_id, name) "
            "VALUES (:id, :tid, :bu_id, 'Store 1')"
        ),
        {"id": str(loc_id), "tid": tenant_id, "bu_id": str(bu_id)},
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
        text("INSERT INTO categories (id, tenant_id, name) VALUES (:id, :tid, 'Pratos')"),
        {"id": str(cat_id), "tid": tenant_id},
    )

    sku_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO skus (id, tenant_id, name, base_uom_id, category_id) "
            "VALUES (:id, :tid, 'Tomate Seco', :uom_id, :cat_id)"
        ),
        {"id": str(sku_id), "tid": tenant_id, "uom_id": str(uom_id), "cat_id": str(cat_id)},
    )

    # Recipe + published version
    recipe_id = uuid4()
    await owner_session.execute(
        text(
            "INSERT INTO recipes (id, tenant_id, name, type) "
            "VALUES (:id, :tid, 'Prato Especial', 'MENU_ITEM')"
        ),
        {"id": str(recipe_id), "tid": tenant_id},
    )

    rv_id = uuid4()
    await owner_session.execute(
        text(
            """INSERT INTO recipe_versions
               (id, tenant_id, recipe_id, version_number, status,
                yield_quantity, yield_uom_id, portion_size, portion_uom_id, valid_from)
               VALUES (:id, :tid, :r_id, 1, 'PUBLISHED',
                       1, :uom_id, 1, :uom_id, :vf)"""
        ),
        {
            "id": str(rv_id),
            "tid": tenant_id,
            "r_id": str(recipe_id),
            "uom_id": str(uom_id),
            "vf": datetime.now(timezone.utc),
        },
    )

    ing_id = uuid4()
    await owner_session.execute(
        text(
            """INSERT INTO recipe_ingredients
               (id, tenant_id, recipe_version_id, sku_id, quantity, uom_id, loss_percentage)
               VALUES (:id, :tid, :rv_id, :sku_id, 0.200, :uom_id, 0)"""
        ),
        {
            "id": str(ing_id),
            "tid": tenant_id,
            "rv_id": str(rv_id),
            "sku_id": str(sku_id),
            "uom_id": str(uom_id),
        },
    )
    await owner_session.commit()

    # ------------------------------------------------------------------
    # 1. Register Loss
    # ------------------------------------------------------------------
    loss_payload = {
        "location_id": str(loc_id),
        "sku_id": str(sku_id),
        "quantity": "2.5",
        "reason": "Vencimento / Desperdício",
        "actor": "Chef Mario",
    }
    loss_res = await async_client.post(
        "/inventory/losses", json=loss_payload, headers=auth_headers
    )
    assert loss_res.status_code == 201, loss_res.text
    assert loss_res.json()["reason"] == "Vencimento / Desperdício"

    # List losses
    list_loss_res = await async_client.get("/inventory/losses", headers=auth_headers)
    assert list_loss_res.status_code == 200, list_loss_res.text
    assert len(list_loss_res.json()) >= 1

    # ------------------------------------------------------------------
    # 2. POS Mapping
    # ------------------------------------------------------------------
    mapping_payload = {
        "pos_product_id": f"POS_PRATO_{uuid4().hex[:6]}",
        "pos_product_name": "Prato Especial no PDV",
        "recipe_id": str(recipe_id),
    }
    map_res = await async_client.post(
        "/sales/mappings", json=mapping_payload, headers=auth_headers
    )
    assert map_res.status_code == 201, map_res.text
    pos_id = mapping_payload["pos_product_id"]

    # ------------------------------------------------------------------
    # 3. Import Sales
    # ------------------------------------------------------------------
    sales_payload = {
        "pos_system": "TOAST",
        "import_reference": f"IMPORT_TEST_{uuid4().hex[:6]}",
        "sales": [
            {
                "pos_sale_id": f"SALE_{uuid4().hex[:6]}",
                "sale_date": datetime.now(timezone.utc).isoformat(),
                "total_amount": "90.00",
                "lines": [
                    {"pos_product_id": pos_id, "quantity": "5.0", "unit_price": "18.00"}
                ],
            }
        ],
    }
    import_res = await async_client.post(
        "/sales/import", json=sales_payload, headers=auth_headers
    )
    assert import_res.status_code == 201, import_res.text
    assert import_res.json()["status"] == "COMPLETED"

    # ------------------------------------------------------------------
    # 4. Theoretical vs Actual Report
    # ------------------------------------------------------------------
    report_res = await async_client.get(
        "/sales/theoretical-vs-actual", headers=auth_headers
    )
    assert report_res.status_code == 200, report_res.text
    report_items = report_res.json()
    assert len(report_items) >= 1

    # 5 portions × 0.200 kg/portion = 1.000 kg theoretical
    target = next(
        (item for item in report_items if item["sku_id"] == str(sku_id)), None
    )
    assert target is not None, f"SKU {sku_id} not found in report"
    assert Decimal(str(target["theoretical_quantity"])) == Decimal("1.000000000000")
