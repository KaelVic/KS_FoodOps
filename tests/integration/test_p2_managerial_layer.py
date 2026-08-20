import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from modules.inventory.service import InventoryService
from modules.intelligence.service import IntelligenceService
from modules.catalog.models import SKU, UOM, Category
from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient


@pytest.mark.asyncio
async def test_calculate_theoretical_stock_by_sku():
    """Validates perpetual theoretical stock calculation and variance analysis."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    location_id = uuid.uuid4()
    sku_id = uuid.uuid4()

    sku = SKU(id=sku_id, tenant_id=tenant_id, name="Picanha Bovina", is_active=True)
    uom = UOM(id=uuid.uuid4(), name="Kilogram", symbol="kg", base_type="mass")
    cat = Category(id=uuid.uuid4(), name="Carnes")

    # Mock SKU query
    mock_sku_res = MagicMock()
    mock_sku_res.all.return_value = [(sku, uom, cat)]

    # Mock ledger net inflows: 100 kg
    mock_ledger_res = MagicMock()
    mock_ledger_res.scalar_one.return_value = Decimal("100.00")

    # Mock theoretical sales consumption: 30 kg
    mock_theo_res = MagicMock()
    mock_theo_res.scalar_one.return_value = Decimal("30.00")

    # Mock actual live balance: 65 kg (so theoretical is 70 kg, variance is -5 kg shortage)
    mock_bal_res = MagicMock()
    mock_bal_res.one.return_value = (Decimal("65.00"), Decimal("1950.00")) # cost = 30.00

    # Mock CostingEngine inside:
    # 1st query in CostingEngine: StockBalanceProjection
    mock_cost_bal = MagicMock()
    mock_cost_bal.scalars.return_value.all.return_value = []
    # 2nd query: last ledger entry
    mock_cost_ledger = MagicMock()
    mock_cost_ledger.scalar_one_or_none.return_value = Decimal("30.00")

    mock_db.execute = AsyncMock(side_effect=[
        mock_sku_res,
        mock_ledger_res,
        mock_theo_res,
        mock_bal_res,
        mock_cost_bal,
        mock_cost_ledger
    ])

    service = InventoryService(mock_db)
    balances = await service.calculate_theoretical_stock_by_sku(tenant_id, location_id)

    assert len(balances) == 1
    item = balances[0]
    assert item["sku_name"] == "Picanha Bovina"
    assert item["actual_quantity"] == 65.0
    assert item["theoretical_quantity"] == 70.0 # 100 - 30
    assert item["theoretical_consumption"] == 30.0
    assert item["variance_quantity"] == -5.0 # 65 - 70
    assert item["status"] == "SHORTAGE"
    assert item["unit_cost"] == 30.0
    assert item["variance_value"] == -150.0 # -5 * 30


@pytest.mark.asyncio
async def test_detect_dish_cmv_drift():
    """Validates detection of dish CMV drift when current ingredient prices change."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    recipe_id = uuid.uuid4()
    version_id = uuid.uuid4()
    sku_id = uuid.uuid4()

    recipe = Recipe(id=recipe_id, tenant_id=tenant_id, name="Picanha na Brasa")
    version = RecipeVersion(
        id=version_id,
        tenant_id=tenant_id,
        recipe_id=recipe_id,
        version_number=1,
        status="PUBLISHED",
        yield_quantity=Decimal("1.0"),
        portion_size=Decimal("1.0"),
        valid_to=None
    )

    # 1 portion uses 0.5 kg of Picanha
    ingredient = RecipeIngredient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        recipe_version_id=version_id,
        sku_id=sku_id,
        quantity=Decimal("0.5"),
        loss_percentage=Decimal("0")
    )

    # Mock recipe query
    mock_rec_res = MagicMock()
    mock_rec_res.all.return_value = [(recipe, version)]

    # Mock ingredients query
    mock_ing_res = MagicMock()
    mock_ing_res.scalars.return_value.all.return_value = [ingredient]

    # Mock CostingEngine: price is R$ 80/kg, so 0.5kg = R$ 40 portion cost
    mock_cost_bal = MagicMock()
    mock_cost_bal.scalars.return_value.all.return_value = []
    mock_cost_led = MagicMock()
    mock_cost_led.scalar_one_or_none.return_value = Decimal("80.00")

    mock_db.execute = AsyncMock(side_effect=[
        mock_rec_res,
        mock_ing_res,
        mock_cost_bal,
        mock_cost_led
    ])

    service = IntelligenceService(mock_db)
    drift_alerts = await service.detect_dish_cmv_drift(tenant_id, threshold_percentage=5.0)

    assert len(drift_alerts) == 1
    drift = drift_alerts[0]
    assert drift["recipe_name"] == "Picanha na Brasa"
    assert drift["current_portion_cost"] == 40.0
    assert drift["status"] in ["WARNING", "CRITICAL", "NORMAL"]


@pytest.mark.asyncio
async def test_calculate_supplier_lead_time_stockouts():
    """Validates supplier lead time computation and stockout risk projection."""
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    sku_id = uuid.uuid4()

    sku = SKU(id=sku_id, tenant_id=tenant_id, name="Queijo Coalho", is_active=True)
    uom = UOM(id=uuid.uuid4(), name="Kilogram", symbol="kg", base_type="mass")

    # Mock historical lead time query: 5 days
    mock_lead_res = MagicMock()
    mock_lead_item = MagicMock()
    mock_lead_item.supplier_id = uuid.uuid4()
    mock_lead_item.avg_lead_days = 5.0
    mock_lead_res.all.return_value = [mock_lead_item]

    # Mock active SKUs query
    mock_skus_res = MagicMock()
    mock_skus_res.all.return_value = [(sku, uom, None)]

    # Mock 30-day consumption: 60 kg -> 2 kg/day
    mock_cons_res = MagicMock()
    mock_cons_res.scalar_one.return_value = Decimal("60.00")

    # Mock on-hand stock: 4 kg (so days remaining = 4 / 2 = 2 days, <= 5 lead days -> CRITICAL)
    mock_stock_res = MagicMock()
    mock_stock_res.scalar_one.return_value = Decimal("4.00")

    mock_db.execute = AsyncMock(side_effect=[
        mock_lead_res,
        mock_skus_res,
        mock_cons_res,
        mock_stock_res
    ])

    service = IntelligenceService(mock_db)
    risks = await service.calculate_supplier_lead_time_stockouts(tenant_id)

    assert len(risks) == 1
    risk = risks[0]
    assert risk["sku_name"] == "Queijo Coalho"
    assert risk["on_hand"] == 4.0
    assert risk["daily_burn_rate"] == 2.0
    assert risk["days_remaining"] == 2.0
    assert risk["risk_level"] == "CRITICAL"
