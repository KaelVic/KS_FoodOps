import pytest
import uuid
import asyncio
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from sqlalchemy import text

from packages.tenant.database import async_session_maker
from packages.tenant.models import Tenant
from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient
from modules.sales.models import SalesImport, Sale, SaleLine, POSProductMapping
from modules.inventory.models import TheoreticalConsumption
from modules.catalog.models import SKU, UOM, SKUConversionVersion

from modules.recipes.service import RecipeService
from modules.sales.service import SalesService

pytestmark = pytest.mark.asyncio

async def setup_test_data(session, tenant_id: uuid.UUID):
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
    
    # 1. Base UOMs
    gram_id = uuid.uuid4()
    portion_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Gram', 'g', 'mass')"),
        {"id": str(gram_id), "t_id": str(tenant_id)}
    )
    await session.execute(
        text("INSERT INTO uoms (id, tenant_id, name, symbol, base_type) VALUES (:id, :t_id, 'Portion', 'pt', 'count')"),
        {"id": str(portion_id), "t_id": str(tenant_id)}
    )
    
    # 2. SKUs
    beef_id = uuid.uuid4()
    await session.execute(
        text("INSERT INTO skus (id, tenant_id, name, base_uom_id) VALUES (:id, :t_id, 'Ground Beef', :uom_id)"),
        {"id": str(beef_id), "t_id": str(tenant_id), "uom_id": str(gram_id)}
    )
    
    return gram_id, portion_id, beef_id

async def test_recipe_and_sales_theoretical_consumption():
    tenant_id = uuid.uuid4()
    
    async with async_session_maker() as session:
        await session.execute(text("INSERT INTO tenants (id, name) VALUES (:id, 'Tenant Phase5')"), {"id": str(tenant_id)})
        gram_id, portion_id, beef_id = await setup_test_data(session, tenant_id)
        await session.commit()
        
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        # 1. Create Recipe
        recipe_service = RecipeService(session)
        recipe = await recipe_service.create_recipe(tenant_id, "Classic Burger", "MENU_ITEM", "POS-BURGER-01")
        
        # 2. Publish version (150g beef per portion, 10% loss)
        version_data = {
            'yield_quantity': '1.0',
            'yield_uom_id': portion_id,
            'portion_size': '1.0',
            'portion_uom_id': portion_id
        }
        ingredients = [
            {'sku_id': beef_id, 'quantity': '150.0', 'uom_id': gram_id, 'loss_percentage': '10.0'} # 150g + 10% = 165g total base qty
        ]
        version = await recipe_service.publish_recipe_version(recipe.id, tenant_id, version_data, ingredients)
        await session.commit()
        
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        # 3. Create POS Mapping
        await session.execute(
            text("INSERT INTO pos_product_mappings (id, tenant_id, pos_product_id, pos_product_name, recipe_id) VALUES (:id, :t_id, 'POS-BURGER-01', 'Classic Burger', :r_id)"),
            {"id": str(uuid.uuid4()), "t_id": str(tenant_id), "r_id": str(recipe.id)}
        )
        await session.commit()
        
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        sales_service = SalesService(session)
        
        # 4. Import sales (idempotent)
        now = datetime.now(timezone.utc)
        sales_data = [
            {
                'pos_sale_id': 'SALE-001',
                'sale_date': now,
                'total_amount': '25.00',
                'lines': [
                    {'pos_product_id': 'POS-BURGER-01', 'quantity': '2.0', 'unit_price': '12.50'}
                ]
            }
        ]
        sales_import = await sales_service.import_sales(tenant_id, "TOAST", "TOAST-BATCH-001", sales_data)
        
        # 5. Idempotency check: import again
        sales_import_dup = await sales_service.import_sales(tenant_id, "TOAST", "TOAST-BATCH-001", sales_data)
        assert sales_import.id == sales_import_dup.id
        
        # 6. Calculate theoretical consumption
        await sales_service.process_theoretical_consumption(sales_import.id, tenant_id)
        await session.commit()
        
    async with async_session_maker() as session:
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": str(tenant_id)})
        
        # 7. Assert consumption
        stmt = select(TheoreticalConsumption).where(TheoreticalConsumption.tenant_id == tenant_id)
        consumptions = (await session.execute(stmt)).scalars().all()
        
        assert len(consumptions) == 1
        tc = consumptions[0]
        assert tc.sku_id == beef_id
        # Qty = 2.0 (sold) * 150g (recipe) * 1.10 (loss) = 330.0g
        assert tc.quantity == Decimal("330.0")
        assert tc.recipe_version_id == version.id
