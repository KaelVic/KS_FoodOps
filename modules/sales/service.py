from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from decimal import Decimal

from modules.sales.models import SalesImport, Sale, SaleLine, POSProductMapping
from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient
from modules.catalog.models import SKUConversionVersion, SKU
from modules.inventory.models import TheoreticalConsumption, StockBalanceProjection

class SalesService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def import_sales(self, tenant_id: UUID, pos_system: str, import_reference: str, sales_data: List[Dict[str, Any]]) -> SalesImport:
        """
        Idempotently import sales data.
        sales_data format:
        [
            {
                'pos_sale_id': '12345',
                'sale_date': datetime,
                'total_amount': '150.00',
                'lines': [
                    {'pos_product_id': 'P1', 'quantity': '2', 'unit_price': '75.00'}
                ]
            }
        ]
        """
        # Check idempotency
        stmt = select(SalesImport).where(
            SalesImport.tenant_id == tenant_id,
            SalesImport.pos_system == pos_system,
            SalesImport.import_reference == import_reference
        )
        existing_import = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if existing_import:
            return existing_import
            
        # Create new import
        sales_import = SalesImport(
            tenant_id=tenant_id,
            pos_system=pos_system,
            import_reference=import_reference,
            status='COMPLETED'
        )
        self.session.add(sales_import)
        await self.session.flush()
        
        # Normalize sales_data if it's in flat item format from POS adapters
        normalized_sales = []
        if sales_data and "pos_order_id" in sales_data[0]:
            from collections import defaultdict
            grouped = defaultdict(list)
            for item in sales_data:
                order_id = item.get("pos_order_id", "unknown")
                grouped[order_id].append(item)
            for order_id, items in grouped.items():
                first_item = items[0]
                total_val = sum(Decimal(str(i.get("net_amount", 0))) for i in items)
                sale_date = first_item.get("sale_date")
                lines = []
                for i in items:
                    lines.append({
                        "pos_product_id": str(i.get("sku_id") or i.get("pos_product_id")),
                        "quantity": str(i.get("quantity", 1)),
                        "unit_price": str(i.get("unit_price", 0))
                    })
                normalized_sales.append({
                    "pos_sale_id": str(order_id),
                    "sale_date": sale_date,
                    "total_amount": str(total_val),
                    "lines": lines
                })
        else:
            normalized_sales = sales_data

        for sale_dict in normalized_sales:
            sale_date = sale_dict['sale_date']
            if isinstance(sale_date, str):
                try:
                    sale_date = datetime.fromisoformat(sale_date.replace("Z", "+00:00"))
                except Exception:
                    sale_date = datetime.now(timezone.utc)

            sale = Sale(
                tenant_id=tenant_id,
                sales_import_id=sales_import.id,
                pos_sale_id=str(sale_dict['pos_sale_id']),
                sale_date=sale_date,
                total_amount=Decimal(str(sale_dict['total_amount']))
            )
            self.session.add(sale)
            await self.session.flush()
            
            for line_dict in sale_dict['lines']:
                sale_line = SaleLine(
                    tenant_id=tenant_id,
                    sale_id=sale.id,
                    pos_product_id=line_dict['pos_product_id'],
                    quantity=Decimal(line_dict['quantity']),
                    unit_price=Decimal(line_dict['unit_price'])
                )
                self.session.add(sale_line)
                
        return sales_import

    async def process_theoretical_consumption(self, sales_import_id: UUID, tenant_id: UUID):
        """
        Calculates theoretical consumption for all sales lines in a given import.
        """
        # Find all sale lines for this import
        stmt = select(SaleLine, Sale.sale_date).join(
            Sale, Sale.id == SaleLine.sale_id
        ).where(
            Sale.sales_import_id == sales_import_id,
            SaleLine.tenant_id == tenant_id
        )
        sale_lines = (await self.session.execute(stmt)).all()
        
        for line, sale_date in sale_lines:
            # Check if already processed
            stmt = select(TheoreticalConsumption).where(
                TheoreticalConsumption.sale_line_id == line.id,
                TheoreticalConsumption.tenant_id == tenant_id
            )
            existing = (await self.session.execute(stmt)).first()
            if existing:
                continue
                
            # Find POS mapping
            stmt = select(POSProductMapping).where(
                POSProductMapping.pos_product_id == line.pos_product_id,
                POSProductMapping.tenant_id == tenant_id
            )
            mapping = (await self.session.execute(stmt)).scalar_one_or_none()
            
            if not mapping or not mapping.recipe_id:
                continue # Unknown product, no recipe mapped
                
            # Find valid recipe version for the sale date
            stmt = select(RecipeVersion).where(
                RecipeVersion.recipe_id == mapping.recipe_id,
                RecipeVersion.tenant_id == tenant_id,
                RecipeVersion.status == 'PUBLISHED',
                RecipeVersion.valid_from <= sale_date,
                (RecipeVersion.valid_to >= sale_date) | (RecipeVersion.valid_to.is_(None))
            )
            recipe_version = (await self.session.execute(stmt)).scalar_one_or_none()
            
            if not recipe_version:
                continue # No valid recipe version at the time of sale
                
            # Fetch ingredients
            stmt = select(RecipeIngredient).where(
                RecipeIngredient.recipe_version_id == recipe_version.id,
                RecipeIngredient.tenant_id == tenant_id
            )
            ingredients = (await self.session.execute(stmt)).scalars().all()
            
            # The sale line quantity is in "portions" (e.g. 2 burgers). 
            # Theoretical consumption logic: required qty = (SaleLine Qty * Portion Size / Yield) * Ingredient Qty * (1 + Loss %)
            # For simplicity, if portion and yield are same UOM, we assume SaleLine Qty is the multiplier.
            # E.g. SaleLine Qty = 2. Ingredient Qty = 100g. Base requirement = 200g.
            # Let's use a simple multiplier: (SaleLine quantity) * (Ingredient quantity).
            # We can refine yield logic later.
            multiplier = line.quantity
            
            for ing in ingredients:
                required_qty = multiplier * ing.quantity
                if ing.loss_percentage > 0:
                    required_qty = required_qty * (Decimal('1') + (ing.loss_percentage / Decimal('100')))
                
                # Fetch SKU to ensure we convert to base UOM if necessary (For now, assume ingredient is in base UOM, or we'd do a conversion lookup)
                stmt = select(SKU).where(SKU.id == ing.sku_id)
                sku = (await self.session.execute(stmt)).scalar_one()
                
                final_qty = required_qty
                if ing.uom_id != sku.base_uom_id:
                    # Look up exact conversion from ingredient UOM to base UOM
                    stmt = select(SKUConversionVersion).where(
                        SKUConversionVersion.sku_id == ing.sku_id,
                        SKUConversionVersion.from_uom_id == ing.uom_id,
                        SKUConversionVersion.to_uom_id == sku.base_uom_id
                    ).order_by(SKUConversionVersion.version_number.desc()).limit(1)
                    conversion = (await self.session.execute(stmt)).scalar_one_or_none()
                    
                    if conversion:
                        final_qty = final_qty * Decimal(conversion.factor)
                    else:
                        raise ValueError(f"No conversion found for SKU {sku.id} from {ing.uom_id} to {sku.base_uom_id}")
                
                # Best effort to fetch cost_at_time. Simplest way is to grab current moving average cost
                stmt = select(func.coalesce(func.sum(StockBalanceProjection.total_value) / func.nullif(func.sum(StockBalanceProjection.quantity), 0), 0)).where(
                    StockBalanceProjection.sku_id == sku.id,
                    StockBalanceProjection.tenant_id == tenant_id
                )
                avg_cost = (await self.session.execute(stmt)).scalar_one_or_none() or Decimal('0')
                
                tc = TheoreticalConsumption(
                    tenant_id=tenant_id,
                    sale_line_id=line.id,
                    recipe_version_id=recipe_version.id,
                    sku_id=sku.id,
                    quantity=final_qty,
                    unit_cost_at_time=avg_cost
                )
                self.session.add(tc)
                
        await self.session.flush()
