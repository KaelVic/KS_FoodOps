import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.catalog.models import SKU, Category, UOM
from modules.suppliers.models import Supplier
from modules.purchasing.models import RFQ, RFQItem, RFQSupplier, RFQProposal, PurchaseOrder, PurchaseOrderLine
from packages.tenant.models import BusinessUnit, Location, Tenant


@pytest.mark.asyncio
async def test_rfq_lifecycle_proposals_comparison_and_award(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession, tenant_id: str
):
    t_id = uuid.UUID(tenant_id)

    # 1. Setup Base Data: BU, Location, UOMs, Category, SKUs and Suppliers
    bu = BusinessUnit(tenant_id=t_id, name="Matriz Compras")
    owner_session.add(bu)
    await owner_session.flush()

    uom_kg = UOM(tenant_id=t_id, name="Quilograma", symbol="kg", base_type="mass")
    cat = Category(tenant_id=t_id, name="Insumos Gastronomia")
    loc = Location(tenant_id=t_id, business_unit_id=bu.id, name="Estoque Central")
    owner_session.add_all([uom_kg, cat, loc])
    await owner_session.flush()

    sku_tomate = SKU(tenant_id=t_id, category_id=cat.id, base_uom_id=uom_kg.id, name="Tomate Italiano Selecionado")
    sku_queijo = SKU(tenant_id=t_id, category_id=cat.id, base_uom_id=uom_kg.id, name="Queijo Mussarela Barra")
    owner_session.add_all([sku_tomate, sku_queijo])

    supp_a = Supplier(tenant_id=t_id, name="Hortifruti Bom Preço Ltda", tax_id="11.111.111/0001-11")
    supp_b = Supplier(tenant_id=t_id, name="Distribuidora Laticínios Central", tax_id="22.222.222/0001-22")
    owner_session.add_all([supp_a, supp_b])
    await owner_session.flush()

    tomate_id_str = str(sku_tomate.id)
    queijo_id_str = str(sku_queijo.id)
    supp_a_id_str = str(supp_a.id)
    supp_b_id_str = str(supp_b.id)
    loc_id_str = str(loc.id)

    await owner_session.commit()

    # 2. Create RFQ via API
    r_create = await async_client.post("/purchasing/rfqs", json={
        "title": "Cotação Semanal de Perecíveis e Laticínios",
        "location_id": loc_id_str,
        "notes": "Entrega até sexta-feira 08h",
        "items": [
            {
                "sku_id": tomate_id_str,
                "quantity": "50.00",
                "target_price": "7.50"
            },
            {
                "sku_id": queijo_id_str,
                "quantity": "20.00",
                "target_price": "36.00"
            }
        ],
        "supplier_ids": [supp_a_id_str, supp_b_id_str]
    }, headers=auth_headers)
    assert r_create.status_code == 201, r_create.text
    rfq = r_create.json()
    rfq_id = rfq["id"]
    assert rfq["status"] == "OPEN"
    assert "RFQ-" in rfq["rfq_number"]

    # 3. Get RFQ Details
    r_get = await async_client.get(f"/purchasing/rfqs/{rfq_id}", headers=auth_headers)
    assert r_get.status_code == 200
    details = r_get.json()
    assert len(details["items"]) == 2
    assert len(details["suppliers"]) == 2

    # Map item ids
    item_tomate_id = next(i["id"] for i in details["items"] if i["sku_id"] == tomate_id_str)
    item_queijo_id = next(i["id"] for i in details["items"] if i["sku_id"] == queijo_id_str)

    # 4. Submit Proposal for Supplier A:
    # Tomate @ 6.00 (best), Queijo @ 38.00, Freight = 20.00
    r_prop_a = await async_client.post(f"/purchasing/rfqs/{rfq_id}/proposals", json={
        "supplier_id": supp_a_id_str,
        "freight_cost": "20.00",
        "delivery_days": "1",
        "payment_terms": "28 dias boleto",
        "min_order_value": "200.00",
        "item_prices": [
            {
                "rfq_item_id": item_tomate_id,
                "unit_price": "6.00",
                "brand_or_spec": "Tomate Campo Limpo"
            },
            {
                "rfq_item_id": item_queijo_id,
                "unit_price": "38.00",
                "brand_or_spec": "Mussarela Premium"
            }
        ]
    }, headers=auth_headers)
    assert r_prop_a.status_code == 200

    # 5. Submit Proposal for Supplier B:
    # Tomate @ 8.00, Queijo @ 32.00 (best), Freight = 0.00
    r_prop_b = await async_client.post(f"/purchasing/rfqs/{rfq_id}/proposals", json={
        "supplier_id": supp_b_id_str,
        "freight_cost": "0.00",
        "delivery_days": "2",
        "payment_terms": "À vista PIX",
        "min_order_value": "300.00",
        "item_prices": [
            {
                "rfq_item_id": item_tomate_id,
                "unit_price": "8.00",
                "brand_or_spec": "Tomate Paulista"
            },
            {
                "rfq_item_id": item_queijo_id,
                "unit_price": "32.00",
                "brand_or_spec": "Mussarela Scala"
            }
        ]
    }, headers=auth_headers)
    assert r_prop_b.status_code == 200

    # 6. Check Comparison Matrix
    r_comp = await async_client.get(f"/purchasing/rfqs/{rfq_id}/comparison", headers=auth_headers)
    assert r_comp.status_code == 200
    comp = r_comp.json()

    # Verify best price per item
    item_tomate_comp = next(i for i in comp["items"] if i["sku_id"] == tomate_id_str)
    assert float(item_tomate_comp["best_price"]) == 6.0
    assert item_tomate_comp["best_supplier_id"] == supp_a_id_str

    item_queijo_comp = next(i for i in comp["items"] if i["sku_id"] == queijo_id_str)
    assert float(item_queijo_comp["best_price"]) == 32.0
    assert item_queijo_comp["best_supplier_id"] == supp_b_id_str

    # Split order total: 50*6 (300) + 20*32 (640) = 940.00
    assert float(comp["split_order_total"]) == 940.0

    # Target total: 50*7.50 (375) + 20*36 (720) = 1095.00
    # Potential savings: 1095 - 940 = 155.00
    assert float(comp["target_grand_total"]) == 1095.0
    assert float(comp["potential_savings"]) == 155.0

    # Single supplier best:
    # Supp A: 300 + 760 + 20 = 1080.00
    # Supp B: 400 + 640 + 0 = 1040.00 -> Supp B is best global
    assert comp["best_global_supplier_id"] == supp_b_id_str
    assert float(comp["best_global_total"]) == 1040.0

    # 7. Award RFQ with SPLIT order
    r_award = await async_client.post(f"/purchasing/rfqs/{rfq_id}/award", json={
        "award_type": "SPLIT"
    }, headers=auth_headers)
    assert r_award.status_code == 200
    award_res = r_award.json()
    assert award_res["status"] == "AWARDED"
    assert len(award_res["purchase_order_ids"]) == 2

    # Verify Purchase Orders in DB
    po_ids = award_res["purchase_order_ids"]
    r_pos = await async_client.get("/purchasing/orders", headers=auth_headers)
    assert r_pos.status_code == 200
    pos_data = r_pos.json()
    matching_pos = [p for p in pos_data if p["id"] in po_ids]
    assert len(matching_pos) == 2
    assert all(p["status"] == "APPROVED" for p in matching_pos)


@pytest.mark.asyncio
async def test_cross_tenant_isolation_rfqs(
    async_client: AsyncClient, auth_headers: dict, owner_session: AsyncSession
):
    # Tenant 2 setup
    t2 = Tenant(name="Outro Restaurante Franchising")
    owner_session.add(t2)
    await owner_session.flush()

    rfq2 = RFQ(
        tenant_id=t2.id,
        rfq_number="RFQ-T2-9999",
        title="Cotação Exclusiva Tenant 2",
        status="OPEN"
    )
    owner_session.add(rfq2)
    await owner_session.flush()
    rfq2_id_str = str(rfq2.id)
    await owner_session.commit()

    # Query with Tenant 1
    r_list = await async_client.get("/purchasing/rfqs", headers=auth_headers)
    assert r_list.status_code == 200
    assert all(r["id"] != rfq2_id_str for r in r_list.json())


    r_get = await async_client.get(f"/purchasing/rfqs/{rfq2_id_str}", headers=auth_headers)
    assert r_get.status_code == 404
