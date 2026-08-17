import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, desc

from modules.production.models import ProductionOrder, ProductionOrderIngredient
from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient
from modules.catalog.models import SKU
from modules.inventory.models import StockMovement, StockLedgerEntry, StockBalanceProjection
from packages.tenant.models import Location

class ProductionService:
    @staticmethod
    async def list_orders(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        status: Optional[str] = None,
        location_id: Optional[uuid.UUID] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(ProductionOrder).where(ProductionOrder.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(ProductionOrder.status == status)
        if location_id:
            stmt = stmt.where(ProductionOrder.location_id == location_id)
            
        stmt = stmt.order_by(desc(ProductionOrder.created_at))
        orders = (await session.execute(stmt)).scalars().all()
        
        result = []
        for o in orders:
            recipe = (await session.execute(select(Recipe).where(Recipe.id == o.recipe_id))).scalar_one_or_none()
            sku = (await session.execute(select(SKU).where(SKU.id == o.produced_sku_id))).scalar_one_or_none()
            loc = (await session.execute(select(Location).where(Location.id == o.location_id))).scalar_one_or_none()
            
            result.append({
                "id": str(o.id),
                "tenant_id": str(o.tenant_id),
                "order_number": o.order_number,
                "recipe_id": str(o.recipe_id),
                "recipe_name": recipe.name if recipe else "Receita Desconhecida",
                "produced_sku_id": str(o.produced_sku_id),
                "produced_sku_name": sku.name if sku else "SKU Desconhecido",
                "location_id": str(o.location_id),
                "location_name": loc.name if loc else "Local Desconhecido",
                "status": o.status,
                "planned_quantity": float(o.planned_quantity),
                "actual_quantity": float(o.actual_quantity) if o.actual_quantity is not None else None,
                "batch_number": o.batch_number,
                "produced_at": o.produced_at.isoformat() if o.produced_at else None,
                "expiration_date": o.expiration_date.isoformat() if o.expiration_date else None,
                "total_cost": float(o.total_cost),
                "unit_cost": float(o.unit_cost),
                "notes": o.notes,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            })
        return result

    @staticmethod
    async def get_order_dict(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        stmt = select(ProductionOrder).where(
            ProductionOrder.id == order_id,
            ProductionOrder.tenant_id == tenant_id,
        )
        o = (await session.execute(stmt)).scalar_one_or_none()
        if not o:
            return None
            
        recipe = (await session.execute(select(Recipe).where(Recipe.id == o.recipe_id))).scalar_one_or_none()
        sku = (await session.execute(select(SKU).where(SKU.id == o.produced_sku_id))).scalar_one_or_none()
        loc = (await session.execute(select(Location).where(Location.id == o.location_id))).scalar_one_or_none()
        
        # Load ingredients
        ing_stmt = select(ProductionOrderIngredient).where(
            ProductionOrderIngredient.production_order_id == o.id,
            ProductionOrderIngredient.tenant_id == tenant_id,
        )
        ingredients = (await session.execute(ing_stmt)).scalars().all()
        
        ing_list = []
        for ing in ingredients:
            ing_sku = (await session.execute(select(SKU).where(SKU.id == ing.sku_id))).scalar_one_or_none()
            ing_list.append({
                "id": str(ing.id),
                "sku_id": str(ing.sku_id),
                "sku_name": ing_sku.name if ing_sku else "Insumo",
                "planned_quantity": float(ing.planned_quantity),
                "actual_quantity": float(ing.actual_quantity) if ing.actual_quantity is not None else None,
                "unit_cost": float(ing.unit_cost),
                "total_cost": float(ing.total_cost),
            })
            
        return {
            "id": str(o.id),
            "tenant_id": str(o.tenant_id),
            "order_number": o.order_number,
            "recipe_id": str(o.recipe_id),
            "recipe_name": recipe.name if recipe else "Receita",
            "recipe_version_id": str(o.recipe_version_id),
            "produced_sku_id": str(o.produced_sku_id),
            "produced_sku_name": sku.name if sku else "SKU",
            "location_id": str(o.location_id),
            "location_name": loc.name if loc else "Local",
            "status": o.status,
            "planned_quantity": float(o.planned_quantity),
            "actual_quantity": float(o.actual_quantity) if o.actual_quantity is not None else None,
            "batch_number": o.batch_number,
            "produced_at": o.produced_at.isoformat() if o.produced_at else None,
            "expiration_date": o.expiration_date.isoformat() if o.expiration_date else None,
            "total_cost": float(o.total_cost),
            "unit_cost": float(o.unit_cost),
            "notes": o.notes,
            "ingredients": ing_list,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }

    @staticmethod
    async def create_order(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        recipe_id: uuid.UUID,
        produced_sku_id: uuid.UUID,
        location_id: uuid.UUID,
        planned_quantity: Decimal,
        notes: Optional[str] = None,
        batch_number: Optional[str] = None,
        expiration_date: Optional[datetime] = None,
    ) -> ProductionOrder:
        # 1. Fetch latest published recipe version
        stmt = (
            select(RecipeVersion)
            .where(
                RecipeVersion.recipe_id == recipe_id,
                RecipeVersion.tenant_id == tenant_id,
                RecipeVersion.status == "PUBLISHED",
            )
            .order_by(desc(RecipeVersion.version_number))
        )
        version = (await session.execute(stmt)).scalars().first()
        if not version:
            # Fallback to any version if no published
            stmt_any = (
                select(RecipeVersion)
                .where(RecipeVersion.recipe_id == recipe_id, RecipeVersion.tenant_id == tenant_id)
                .order_by(desc(RecipeVersion.version_number))
            )
            version = (await session.execute(stmt_any)).scalars().first()
            if not version:
                raise ValueError(f"Ficha técnica {recipe_id} não possui versões cadastradas.")

        # 2. Sequential order number
        count_stmt = select(func.count(ProductionOrder.id)).where(ProductionOrder.tenant_id == tenant_id)
        current_count = (await session.execute(count_stmt)).scalar() or 0
        year = datetime.now().year
        order_number = f"OP-{year}-{(current_count + 1):04d}"

        # 3. Create ProductionOrder
        order = ProductionOrder(
            tenant_id=tenant_id,
            order_number=order_number,
            recipe_id=recipe_id,
            recipe_version_id=version.id,
            produced_sku_id=produced_sku_id,
            location_id=location_id,
            status="PLANNED",
            planned_quantity=planned_quantity,
            batch_number=batch_number or f"LOTE-{datetime.now().strftime('%Y%m%d')}-{(current_count + 1):03d}",
            expiration_date=expiration_date,
            notes=notes,
        )
        session.add(order)
        await session.flush()

        # 4. Fetch Recipe Ingredients and compute planned scaling factor
        ing_stmt = select(RecipeIngredient).where(
            RecipeIngredient.recipe_version_id == version.id,
            RecipeIngredient.tenant_id == tenant_id,
        )
        recipe_ingredients = (await session.execute(ing_stmt)).scalars().all()
        
        scale_factor = planned_quantity / version.yield_quantity if version.yield_quantity > 0 else Decimal("1")
        total_estimated_cost = Decimal("0")

        for r_ing in recipe_ingredients:
            qty_needed = Decimal(r_ing.quantity) * scale_factor
            if r_ing.loss_percentage and r_ing.loss_percentage > 0:
                qty_needed = qty_needed / (Decimal("1") - (Decimal(r_ing.loss_percentage) / Decimal("100")))

            # Get current CMP of ingredient in location
            bal_stmt = select(StockBalanceProjection).where(
                StockBalanceProjection.sku_id == r_ing.sku_id,
                StockBalanceProjection.location_id == location_id,
                StockBalanceProjection.tenant_id == tenant_id,
            )
            bal = (await session.execute(bal_stmt)).scalar_one_or_none()
            unit_cost = (bal.total_value / bal.quantity) if (bal and bal.quantity > 0) else Decimal("0")
            line_cost = qty_needed * unit_cost
            total_estimated_cost += line_cost

            order_ing = ProductionOrderIngredient(
                tenant_id=tenant_id,
                production_order_id=order.id,
                sku_id=r_ing.sku_id,
                planned_quantity=qty_needed,
                unit_cost=unit_cost,
                total_cost=line_cost,
            )
            session.add(order_ing)

        order.total_cost = total_estimated_cost
        order.unit_cost = (total_estimated_cost / planned_quantity) if planned_quantity > 0 else Decimal("0")

        await session.flush()
        return order

    @staticmethod
    async def start_production(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> ProductionOrder:
        stmt = (
            select(ProductionOrder)
            .where(ProductionOrder.id == order_id, ProductionOrder.tenant_id == tenant_id)
            .with_for_update()
        )
        order = (await session.execute(stmt)).scalar_one_or_none()
        if not order:
            raise ValueError(f"Ordem de Produção {order_id} não encontrada.")
            
        if order.status != "PLANNED":
            raise ValueError(f"Ordem {order.order_number} está no status {order.status} e não pode ser iniciada.")

        order.status = "IN_PRODUCTION"
        order.produced_at = datetime.now(timezone.utc)
        await session.flush()
        return order

    @staticmethod
    async def complete_production(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        order_id: uuid.UUID,
        actual_quantity: Optional[Decimal] = None,
        batch_number: Optional[str] = None,
        expiration_date: Optional[datetime] = None,
        actual_ingredient_quantities: Optional[Dict[str, Decimal]] = None,
    ) -> ProductionOrder:
        """
        Completes the production batch, consumes raw ingredients from stock ledger,
        and posts receipt of the finished/semi-finished SKU in stock ledger.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(ProductionOrder)
            .where(ProductionOrder.id == order_id, ProductionOrder.tenant_id == tenant_id)
            .with_for_update()
        )
        order = (await session.execute(stmt)).scalar_one_or_none()
        if not order:
            raise ValueError(f"Ordem de Produção {order_id} não encontrada.")
            
        if order.status == "COMPLETED":
            return order
            
        final_yield = actual_quantity if actual_quantity is not None else order.planned_quantity
        if final_yield <= 0:
            raise ValueError("O rendimento real produzido deve ser maior que zero.")

        if batch_number:
            order.batch_number = batch_number
        if expiration_date:
            order.expiration_date = expiration_date

        order.actual_quantity = final_yield
        order.produced_at = now

        # 1. Fetch Order Ingredients
        ing_stmt = select(ProductionOrderIngredient).where(
            ProductionOrderIngredient.production_order_id == order.id,
            ProductionOrderIngredient.tenant_id == tenant_id,
        )
        order_ingredients = (await session.execute(ing_stmt)).scalars().all()

        # 2. Post Movement: PRODUCTION_CONSUMPTION (Outflow of raw ingredients)
        consumption_movement = StockMovement(
            tenant_id=tenant_id,
            location_id=order.location_id,
            type="PRODUCTION_CONSUMPTION",
            status="POSTED",
            reference_id=order.id,
            reference_type="ProductionOrder",
            posted_at=now,
        )
        session.add(consumption_movement)
        await session.flush()

        total_actual_cost = Decimal("0")

        for ing in order_ingredients:
            # Determine actual quantity consumed for this ingredient
            sku_str_id = str(ing.sku_id)
            consumed_qty = (
                actual_ingredient_quantities[sku_str_id]
                if (actual_ingredient_quantities and sku_str_id in actual_ingredient_quantities)
                else ing.planned_quantity
            )
            ing.actual_quantity = consumed_qty

            # Lock stock balance projection for ingredient
            bal_stmt = (
                select(StockBalanceProjection)
                .where(
                    StockBalanceProjection.sku_id == ing.sku_id,
                    StockBalanceProjection.location_id == order.location_id,
                    StockBalanceProjection.tenant_id == tenant_id,
                )
                .with_for_update()
            )
            balance = (await session.execute(bal_stmt)).scalar_one_or_none()
            if balance is None:
                balance = StockBalanceProjection(
                    tenant_id=tenant_id,
                    location_id=order.location_id,
                    sku_id=ing.sku_id,
                    quantity=Decimal("0"),
                    total_value=Decimal("0"),
                )
                session.add(balance)
                await session.flush()
                balance = (await session.execute(bal_stmt)).scalar_one()

            unit_cost = (balance.total_value / balance.quantity) if balance.quantity > 0 else Decimal("0")
            line_cost = consumed_qty * unit_cost
            total_actual_cost += line_cost

            ing.unit_cost = unit_cost
            ing.total_cost = line_cost

            # Deduct from balance
            balance.quantity -= consumed_qty
            balance.total_value -= line_cost

            # Create negative ledger entry
            ledger_entry = StockLedgerEntry(
                tenant_id=tenant_id,
                movement_id=consumption_movement.id,
                sku_id=ing.sku_id,
                quantity=-consumed_qty,
                unit_cost=unit_cost,
                balance_after=balance.quantity,
            )
            session.add(ledger_entry)

        # 3. Post Movement: PRODUCTION_RECEIPT (Inflow of produced SKU)
        receipt_movement = StockMovement(
            tenant_id=tenant_id,
            location_id=order.location_id,
            type="PRODUCTION_RECEIPT",
            status="POSTED",
            reference_id=order.id,
            reference_type="ProductionOrder",
            posted_at=now,
        )
        session.add(receipt_movement)
        await session.flush()

        unit_produced_cost = (total_actual_cost / final_yield) if final_yield > 0 else Decimal("0")
        order.total_cost = total_actual_cost
        order.unit_cost = unit_produced_cost

        # Lock stock balance projection for produced SKU
        prod_bal_stmt = (
            select(StockBalanceProjection)
            .where(
                StockBalanceProjection.sku_id == order.produced_sku_id,
                StockBalanceProjection.location_id == order.location_id,
                StockBalanceProjection.tenant_id == tenant_id,
            )
            .with_for_update()
        )
        prod_balance = (await session.execute(prod_bal_stmt)).scalar_one_or_none()
        if prod_balance is None:
            prod_balance = StockBalanceProjection(
                tenant_id=tenant_id,
                location_id=order.location_id,
                sku_id=order.produced_sku_id,
                quantity=Decimal("0"),
                total_value=Decimal("0"),
            )
            session.add(prod_balance)
            await session.flush()
            prod_balance = (await session.execute(prod_bal_stmt)).scalar_one()

        # Add produced quantity and value to balance
        prod_balance.quantity += final_yield
        prod_balance.total_value += total_actual_cost

        # Create positive ledger entry
        prod_ledger_entry = StockLedgerEntry(
            tenant_id=tenant_id,
            movement_id=receipt_movement.id,
            sku_id=order.produced_sku_id,
            quantity=final_yield,
            unit_cost=unit_produced_cost,
            balance_after=prod_balance.quantity,
        )
        session.add(prod_ledger_entry)

        order.status = "COMPLETED"
        await session.flush()
        return order
