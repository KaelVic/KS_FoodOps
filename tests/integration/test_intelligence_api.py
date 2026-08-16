import pytest
import uuid
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import FastAPI
import pytest_asyncio
from packages.tenant.database import async_session_maker
from httpx import ASGITransport

@pytest_asyncio.fixture
async def async_client(tenant_id, test_db):
    from apps.api.main import app
    from packages.security.dependencies import get_tenant_id_from_header, get_current_user, get_secure_session
    from packages.security.auth import TokenPayload
    
    app.dependency_overrides[get_tenant_id_from_header] = lambda: uuid.UUID(tenant_id)
    app.dependency_overrides[get_current_user] = lambda: TokenPayload(sub="admin@ksfoodops.com", role="admin")
    
    async def override_get_secure_session():
        from sqlalchemy import text
        await test_db.execute(
            text("SELECT set_config('app.current_tenant_id', :t, false)"),
            {"t": str(tenant_id)}
        )
        yield test_db

    app.dependency_overrides[get_secure_session] = override_get_secure_session
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_db():
    async with async_session_maker() as session:
        original_commit = session.commit
        async def mock_commit():
            await session.flush()
        session.commit = mock_commit
        try:
            yield session
        finally:
            await session.rollback()

@pytest.fixture
def tenant_id():
    return str(uuid4())

@pytest.fixture
def auth_headers(tenant_id):
    return {}

@pytest.mark.asyncio
async def test_intelligence_endpoints(async_client: AsyncClient, auth_headers: dict, test_db, tenant_id: str):
    from sqlalchemy import text
    from packages.tenant.models import Location, Tenant, BusinessUnit
    from modules.catalog.models import SKU, Category, UOM
    from modules.inventory.models import StockLedgerEntry, StockMovement, StockBalanceProjection
    from modules.suppliers.models import Supplier

    # Create tenant first
    tenant = Tenant(id=tenant_id, name="Test Tenant", is_active=True)
    test_db.add(tenant)
    await test_db.flush()

    await test_db.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
        {"tenant_id": str(tenant_id)}
    )

    bu = BusinessUnit(tenant_id=tenant_id, name="Test BU")
    test_db.add(bu)
    await test_db.flush()

    # Setup base data
    loc = Location(tenant_id=tenant_id, business_unit_id=bu.id, name="Main Kitchen")
    test_db.add(loc)

    uom = UOM(tenant_id=tenant_id, symbol="KG", name="Kilogram", base_type="MASS")
    test_db.add(uom)

    cat = Category(tenant_id=tenant_id, name="Groceries")
    test_db.add(cat)
    await test_db.flush()

    sku = SKU(tenant_id=tenant_id, name="Flour", base_uom_id=uom.id, category_id=cat.id)
    test_db.add(sku)
    await test_db.flush()

    supplier = Supplier(tenant_id=tenant_id, name="Alpha Supplier")
    test_db.add(supplier)
    await test_db.flush()

    # Create dummy movement and stock balance to simulate consumption (for ABC)
    movement = StockMovement(
        tenant_id=tenant_id,
        location_id=loc.id,
        type='CONSUMPTION',
        status='POSTED',
        posted_at=datetime.now(timezone.utc) - timedelta(days=5)
    )
    test_db.add(movement)
    await test_db.flush()

    balance = StockBalanceProjection(
        tenant_id=tenant_id,
        location_id=loc.id,
        sku_id=sku.id,
        quantity=Decimal("10"),
        total_value=Decimal("50")
    )
    test_db.add(balance)
    await test_db.flush()

    ledger = StockLedgerEntry(
        tenant_id=tenant_id,
        movement_id=movement.id,
        sku_id=sku.id,
        quantity=Decimal("-20"),
        unit_cost=Decimal("2.50"),
        balance_after=Decimal("10"),
        created_at=datetime.now(timezone.utc) - timedelta(days=5)
    )
    test_db.add(ledger)
    await test_db.commit()

    # 1. Update/Set Policy
    policy_payload = {
        "location_id": str(loc.id),
        "sku_id": str(sku.id),
        "min_stock": "50",
        "target_stock": "100",
        "lead_time_days": 3
    }
    res_policy = await async_client.put("/intelligence/policies", json=policy_payload, headers=auth_headers)
    assert res_policy.status_code == 200
    data_policy = res_policy.json()
    assert float(data_policy["min_stock"]) == 50.0
    assert float(data_policy["target_stock"]) == 100.0

    # 2. Calculate ABC
    res_abc = await async_client.post("/intelligence/abc/calculate", json={"location_id": str(loc.id)}, headers=auth_headers)
    assert res_abc.status_code == 200

    # 3. Generate Suggestions
    res_sugg_gen = await async_client.post("/intelligence/suggestions/generate", json={"location_id": str(loc.id)}, headers=auth_headers)
    assert res_sugg_gen.status_code == 200

    # Check Suggestions list
    res_sugg_list = await async_client.get("/intelligence/suggestions", headers=auth_headers)
    assert res_sugg_list.status_code == 200
    suggestions = res_sugg_list.json()
    assert len(suggestions) >= 1
    sugg = suggestions[0]
    assert sugg["status"] == "PENDING"
    assert Decimal(str(sugg["suggested_quantity"])) == Decimal("90.0") # Target (100) - OnHand (10) = 90

    # Convert to PO
    res_conv = await async_client.post(
        f"/intelligence/suggestions/{sugg['id']}/convert-to-po",
        json={"supplier_id": str(supplier.id)},
        headers=auth_headers
    )
    assert res_conv.status_code == 200
    assert res_conv.json()["status"] == "DRAFT"

    # 4. Generate Alerts
    res_alert_gen = await async_client.post("/intelligence/alerts/generate", json={"location_id": str(loc.id)}, headers=auth_headers)
    assert res_alert_gen.status_code == 200

    res_alert_list = await async_client.get("/intelligence/alerts", headers=auth_headers)
    assert res_alert_list.status_code == 200
    alerts = res_alert_list.json()
    assert len(alerts) >= 1
    alert = alerts[0]
    assert alert["metric"] == "STOCKOUT_RISK"
    assert Decimal(str(alert["observed_value"])) == Decimal("10.0")

    # Resolve Alert
    res_resolve = await async_client.post(f"/intelligence/alerts/{alert['id']}/resolve", headers=auth_headers)
    assert res_resolve.status_code == 200
