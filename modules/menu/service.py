import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from modules.menu.models import MenuCategory, MenuItem
from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient
from modules.sales.models import Sale, SaleLine, POSProductMapping
from modules.inventory.models import StockLedgerEntry
from modules.catalog.models import SKU

class MenuService:

    # --- Categories ---
    @staticmethod
    async def list_categories(session: AsyncSession, tenant_id: uuid.UUID) -> List[Dict[str, Any]]:
        stmt = select(MenuCategory).where(
            MenuCategory.tenant_id == tenant_id
        ).order_by(MenuCategory.display_order.asc(), MenuCategory.name.asc())
        categories = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": str(c.id),
                "name": c.name,
                "display_order": c.display_order,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in categories
        ]

    @staticmethod
    async def create_category(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        category = MenuCategory(
            tenant_id=tenant_id,
            name=data["name"],
            display_order=data.get("display_order", 0),
            is_active=data.get("is_active", True)
        )
        session.add(category)
        await session.flush()
        return {
            "id": str(category.id),
            "name": category.name,
            "display_order": category.display_order,
            "is_active": category.is_active,
            "created_at": category.created_at.isoformat() if category.created_at else None
        }

    # --- Menu Items ---
    @staticmethod
    async def get_recipe_unit_cost(session: AsyncSession, tenant_id: uuid.UUID, recipe_id: uuid.UUID) -> Decimal:
        """Calculates dynamic cost per portion of a recipe based on its latest published version."""
        v_stmt = select(RecipeVersion).where(
            RecipeVersion.recipe_id == recipe_id,
            RecipeVersion.tenant_id == tenant_id,
            RecipeVersion.status == "PUBLISHED"
        ).order_by(RecipeVersion.version_number.desc()).limit(1)
        version = (await session.execute(v_stmt)).scalar_one_or_none()
        
        if not version:
            # Fallback to any latest version
            v_stmt = select(RecipeVersion).where(
                RecipeVersion.recipe_id == recipe_id,
                RecipeVersion.tenant_id == tenant_id
            ).order_by(RecipeVersion.version_number.desc()).limit(1)
            version = (await session.execute(v_stmt)).scalar_one_or_none()
            if not version:
                return Decimal("0")

        ing_stmt = select(RecipeIngredient).where(
            RecipeIngredient.recipe_version_id == version.id,
            RecipeIngredient.tenant_id == tenant_id
        )
        ingredients = (await session.execute(ing_stmt)).scalars().all()

        total_recipe_cost = Decimal("0")
        for ing in ingredients:
            # Find latest SKU cost from ledger or fallback
            entry_stmt = select(StockLedgerEntry).where(
                StockLedgerEntry.sku_id == ing.sku_id,
                StockLedgerEntry.tenant_id == tenant_id
            ).order_by(StockLedgerEntry.created_at.desc()).limit(1)
            entry = (await session.execute(entry_stmt)).scalar_one_or_none()
            unit_cost = entry.unit_cost if entry and entry.unit_cost else Decimal("10.00")
            
            # Loss adjustment
            loss_mult = Decimal("1") + (ing.loss_percentage / Decimal("100"))
            ing_cost = ing.quantity * unit_cost * loss_mult
            total_recipe_cost += ing_cost

        yield_qty = version.yield_quantity if version.yield_quantity > 0 else Decimal("1")
        portion_cost = (total_recipe_cost / yield_qty).quantize(Decimal("0.01"))
        return portion_cost

    @staticmethod
    async def list_menu_items(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        category_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        stmt = select(MenuItem).where(MenuItem.tenant_id == tenant_id)
        if category_id:
            stmt = stmt.where(MenuItem.category_id == category_id)
        if is_active is not None:
            stmt = stmt.where(MenuItem.is_active == is_active)

        stmt = stmt.order_by(MenuItem.display_order.asc(), MenuItem.name.asc())
        items = (await session.execute(stmt)).scalars().all()

        # Load categories mapping
        cats_stmt = select(MenuCategory).where(MenuCategory.tenant_id == tenant_id)
        categories = (await session.execute(cats_stmt)).scalars().all()
        cat_map = {c.id: c.name for c in categories}

        # Load recipes mapping
        rec_stmt = select(Recipe).where(Recipe.tenant_id == tenant_id)
        recipes = (await session.execute(rec_stmt)).scalars().all()
        rec_map = {r.id: r.name for r in recipes}

        result = []
        for item in items:
            cost = item.cost_price
            if item.recipe_id:
                calc_cost = await MenuService.get_recipe_unit_cost(session, tenant_id, item.recipe_id)
                if calc_cost > 0:
                    cost = calc_cost

            sale_price = item.sale_price
            unit_margin = sale_price - cost
            margin_pct = (unit_margin / sale_price * Decimal("100")).quantize(Decimal("0.1")) if sale_price > 0 else Decimal("0")
            cmv_pct = (cost / sale_price * Decimal("100")).quantize(Decimal("0.1")) if sale_price > 0 else Decimal("0")
            
            target_cmv = item.target_cmv_percentage
            suggested_price = (cost / (target_cmv / Decimal("100"))).quantize(Decimal("0.01")) if target_cmv > 0 else sale_price

            result.append({
                "id": str(item.id),
                "category_id": str(item.category_id) if item.category_id else None,
                "category_name": cat_map.get(item.category_id) if item.category_id else "Geral",
                "recipe_id": str(item.recipe_id) if item.recipe_id else None,
                "recipe_name": rec_map.get(item.recipe_id) if item.recipe_id else None,
                "name": item.name,
                "pos_code": item.pos_code,
                "description": item.description,
                "sale_price": float(sale_price),
                "cost_price": float(cost),
                "unit_margin": float(unit_margin),
                "margin_pct": float(margin_pct),
                "cmv_pct": float(cmv_pct),
                "target_cmv_percentage": float(target_cmv),
                "suggested_price": float(suggested_price),
                "is_active": item.is_active,
                "display_order": item.display_order,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })

        return result

    @staticmethod
    async def get_menu_item(session: AsyncSession, tenant_id: uuid.UUID, item_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        stmt = select(MenuItem).where(
            MenuItem.id == uuid.UUID(str(item_id)),
            MenuItem.tenant_id == uuid.UUID(str(tenant_id))
        )
        item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            return None

        category_name = None
        if item.category_id:
            cat_stmt = select(MenuCategory.name).where(MenuCategory.id == item.category_id)
            category_name = (await session.execute(cat_stmt)).scalar_one_or_none()

        recipe_name = None
        if item.recipe_id:
            rec_stmt = select(Recipe.name).where(Recipe.id == item.recipe_id)
            recipe_name = (await session.execute(rec_stmt)).scalar_one_or_none()

        cost = item.cost_price
        if item.recipe_id:
            calc_cost = await MenuService.get_recipe_unit_cost(session, tenant_id, item.recipe_id)
            if calc_cost > 0:
                cost = calc_cost

        sale_price = item.sale_price
        unit_margin = sale_price - cost
        margin_pct = (unit_margin / sale_price * Decimal("100")).quantize(Decimal("0.1")) if sale_price > 0 else Decimal("0")
        cmv_pct = (cost / sale_price * Decimal("100")).quantize(Decimal("0.1")) if sale_price > 0 else Decimal("0")
        
        target_cmv = item.target_cmv_percentage
        suggested_price = (cost / (target_cmv / Decimal("100"))).quantize(Decimal("0.01")) if target_cmv > 0 else sale_price

        return {
            "id": str(item.id),
            "category_id": str(item.category_id) if item.category_id else None,
            "category_name": category_name or "Geral",
            "recipe_id": str(item.recipe_id) if item.recipe_id else None,
            "recipe_name": recipe_name,
            "name": item.name,
            "pos_code": item.pos_code,
            "description": item.description,
            "sale_price": float(sale_price),
            "cost_price": float(cost),
            "unit_margin": float(unit_margin),
            "margin_pct": float(margin_pct),
            "cmv_pct": float(cmv_pct),
            "target_cmv_percentage": float(target_cmv),
            "suggested_price": float(suggested_price),
            "is_active": item.is_active,
            "display_order": item.display_order,
            "created_at": item.created_at.isoformat() if item.created_at else None
        }

    @staticmethod
    async def create_menu_item(session: AsyncSession, tenant_id: uuid.UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        sale_price = Decimal(str(data.get("sale_price", 0)))
        cost_price = Decimal(str(data.get("cost_price", 0)))
        recipe_id = uuid.UUID(str(data["recipe_id"])) if data.get("recipe_id") else None

        if recipe_id and cost_price == 0:
            calc_cost = await MenuService.get_recipe_unit_cost(session, tenant_id, recipe_id)
            if calc_cost > 0:
                cost_price = calc_cost

        target_cmv = Decimal(str(data.get("target_cmv_percentage", 30.00)))

        item = MenuItem(
            tenant_id=uuid.UUID(str(tenant_id)),
            category_id=uuid.UUID(str(data["category_id"])) if data.get("category_id") else None,
            recipe_id=recipe_id,
            name=data["name"],
            pos_code=data.get("pos_code"),
            description=data.get("description"),
            sale_price=sale_price,
            cost_price=cost_price,
            target_cmv_percentage=target_cmv,
            is_active=data.get("is_active", True),
            display_order=data.get("display_order", 0)
        )
        session.add(item)
        await session.flush()
        res = await MenuService.get_menu_item(session, tenant_id, item.id)
        return res # type: ignore

    @staticmethod
    async def update_menu_item(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        item_id: uuid.UUID,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        stmt = select(MenuItem).where(
            MenuItem.id == uuid.UUID(str(item_id)),
            MenuItem.tenant_id == uuid.UUID(str(tenant_id))
        )
        item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            raise ValueError("Item de cardápio não encontrado.")

        if "name" in data:
            item.name = data["name"]
        if "category_id" in data:
            item.category_id = uuid.UUID(str(data["category_id"])) if data["category_id"] else None
        if "recipe_id" in data:
            item.recipe_id = uuid.UUID(str(data["recipe_id"])) if data["recipe_id"] else None
        if "pos_code" in data:
            item.pos_code = data["pos_code"]
        if "description" in data:
            item.description = data["description"]
        if "sale_price" in data:
            item.sale_price = Decimal(str(data["sale_price"]))
        if "cost_price" in data:
            item.cost_price = Decimal(str(data["cost_price"]))
        if "target_cmv_percentage" in data:
            item.target_cmv_percentage = Decimal(str(data["target_cmv_percentage"]))
        if "is_active" in data:
            item.is_active = data["is_active"]
        if "display_order" in data:
            item.display_order = data["display_order"]

        await session.flush()
        return {
            "id": str(item.id),
            "name": item.name,
            "sale_price": float(item.sale_price),
            "cost_price": float(item.cost_price),
            "is_active": item.is_active
        }

    @staticmethod
    async def delete_menu_item(session: AsyncSession, tenant_id: uuid.UUID, item_id: uuid.UUID) -> bool:
        stmt = select(MenuItem).where(MenuItem.id == item_id, MenuItem.tenant_id == tenant_id)
        item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            return False
        await session.delete(item)
        await session.flush()
        return True

    # --- Menu Engineering / Matriz BCG ---
    @staticmethod
    async def calculate_menu_engineering(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        if not end_date:
            end_date = now
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # 1. Fetch Menu Items
        stmt = select(MenuItem).where(MenuItem.tenant_id == tenant_id, MenuItem.is_active == True)
        if category_id:
            stmt = stmt.where(MenuItem.category_id == category_id)
        menu_items = (await session.execute(stmt)).scalars().all()

        if not menu_items:
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_items": 0,
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                    "total_margin": 0.0,
                    "average_cmv_pct": 0.0,
                    "average_margin_pct": 0.0,
                    "cutoff_volume": 0.0,
                    "cutoff_margin": 0.0
                },
                "bcg_distribution": {
                    "stars_count": 0,
                    "plowhorses_count": 0,
                    "puzzles_count": 0,
                    "dogs_count": 0
                },
                "items": []
            }

        # Categories mapping
        cats_stmt = select(MenuCategory).where(MenuCategory.tenant_id == tenant_id)
        categories = (await session.execute(cats_stmt)).scalars().all()
        cat_map = {c.id: c.name for c in categories}

        # Recipes mapping
        rec_stmt = select(Recipe).where(Recipe.tenant_id == tenant_id)
        recipes = (await session.execute(rec_stmt)).scalars().all()
        rec_map = {r.id: r.name for r in recipes}

        # POS product mapping to resolve sales
        pos_map_stmt = select(POSProductMapping).where(POSProductMapping.tenant_id == tenant_id)
        pos_mappings = (await session.execute(pos_map_stmt)).scalars().all()
        # map recipe_id -> [pos_product_ids]
        recipe_to_pos = {}
        for pm in pos_mappings:
            if pm.recipe_id:
                recipe_to_pos.setdefault(pm.recipe_id, []).append(pm.pos_product_id)

        # 2. Query Sale Lines in period
        sales_stmt = select(SaleLine).join(Sale, SaleLine.sale_id == Sale.id).where(
            SaleLine.tenant_id == tenant_id,
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date
        )
        sale_lines = (await session.execute(sales_stmt)).scalars().all()

        # Group sales by pos_product_id
        pos_sales_qty: Dict[str, Decimal] = {}
        pos_sales_revenue: Dict[str, Decimal] = {}
        for sl in sale_lines:
            pos_sales_qty[sl.pos_product_id] = pos_sales_qty.get(sl.pos_product_id, Decimal("0")) + sl.quantity
            pos_sales_revenue[sl.pos_product_id] = pos_sales_revenue.get(sl.pos_product_id, Decimal("0")) + (sl.quantity * sl.unit_price)

        # 3. Build Raw Analysis per Item
        analyzed_items = []
        total_units_sold = Decimal("0")
        total_revenue = Decimal("0")
        total_cost = Decimal("0")
        total_margin = Decimal("0")

        for item in menu_items:
            # Determine cost
            cost = item.cost_price
            if item.recipe_id:
                calc_cost = await MenuService.get_recipe_unit_cost(session, tenant_id, item.recipe_id)
                if calc_cost > 0:
                    cost = calc_cost

            sale_price = item.sale_price
            unit_margin = sale_price - cost

            # Determine sales volume
            qty_sold = Decimal("0")
            if item.pos_code and item.pos_code in pos_sales_qty:
                qty_sold += pos_sales_qty[item.pos_code]
            elif item.recipe_id and item.recipe_id in recipe_to_pos:
                for pos_id in recipe_to_pos[item.recipe_id]:
                    qty_sold += pos_sales_qty.get(pos_id, Decimal("0"))
            
            # If no POS sales registered, default to 1 unit to allow simulation
            if len(sale_lines) == 0:
                qty_sold = Decimal("10") # Default baseline simulation weight

            item_rev = qty_sold * sale_price
            item_cost = qty_sold * cost
            item_margin = qty_sold * unit_margin

            total_units_sold += qty_sold
            total_revenue += item_rev
            total_cost += item_cost
            total_margin += item_margin

            analyzed_items.append({
                "item_obj": item,
                "sale_price": sale_price,
                "cost_price": cost,
                "unit_margin": unit_margin,
                "quantity_sold": qty_sold,
                "total_revenue": item_rev,
                "total_cost": item_cost,
                "total_margin": item_margin,
                "cmv_pct": (cost / sale_price * Decimal("100")).quantize(Decimal("0.1")) if sale_price > 0 else Decimal("0"),
                "margin_pct": (unit_margin / sale_price * Decimal("100")).quantize(Decimal("0.1")) if sale_price > 0 else Decimal("0"),
            })

        total_items_count = Decimal(str(len(analyzed_items)))
        
        # 4. Compute Benchmark Cutoffs (Kasavana & Smith Standard: 70% of average popularity)
        cutoff_volume = (total_units_sold / total_items_count * Decimal("0.7")).quantize(Decimal("0.1")) if total_items_count > 0 else Decimal("0")
        cutoff_margin = (total_margin / total_units_sold).quantize(Decimal("0.01")) if total_units_sold > 0 else ((total_margin / total_items_count).quantize(Decimal("0.01")) if total_items_count > 0 else Decimal("0"))

        stars_count = 0
        plowhorses_count = 0
        puzzles_count = 0
        dogs_count = 0

        final_items = []
        for a in analyzed_items:
            item: MenuItem = a["item_obj"]
            is_high_volume = a["quantity_sold"] >= cutoff_volume
            is_high_margin = a["unit_margin"] >= cutoff_margin

            if is_high_volume and is_high_margin:
                classification = "STAR"
                badge_label = "Estrela 🌟"
                recommendation = "Manter qualidade e ficha técnica rigorosamente. Prato campeão em lucro e volume. Não alterar receita."
                stars_count += 1
            elif is_high_volume and not is_high_margin:
                classification = "PLOWHORSE"
                badge_label = "Burro de Carga 🐴"
                recommendation = "Alta popularidade com margem abaixo da média. Aumentar ligeiramente o preço (+5% a +10%) ou renegociar custos dos insumos."
                plowhorses_count += 1
            elif not is_high_volume and is_high_margin:
                classification = "PUZZLE"
                badge_label = "Quebra-Cabeça 🧩"
                recommendation = "Alta lucratividade mas baixa saída. Dar destaque no cardápio, treinar garçons para venda sugestiva ou criar combos."
                puzzles_count += 1
            else:
                classification = "DOG"
                badge_label = "Cão 🐕"
                recommendation = "Baixo volume e baixa margem. Avaliar substituição ou reformulação completa do prato ou remoção do cardápio."
                dogs_count += 1

            # Sales share %
            sales_share_pct = (a["quantity_sold"] / total_units_sold * Decimal("100")).quantize(Decimal("0.1")) if total_units_sold > 0 else Decimal("0")
            revenue_share_pct = (a["total_revenue"] / total_revenue * Decimal("100")).quantize(Decimal("0.1")) if total_revenue > 0 else Decimal("0")

            target_cmv = item.target_cmv_percentage
            suggested_price = (a["cost_price"] / (target_cmv / Decimal("100"))).quantize(Decimal("0.01")) if target_cmv > 0 else a["sale_price"]

            final_items.append({
                "id": str(item.id),
                "name": item.name,
                "category_id": str(item.category_id) if item.category_id else None,
                "category_name": cat_map.get(item.category_id) if item.category_id else "Geral",
                "recipe_id": str(item.recipe_id) if item.recipe_id else None,
                "recipe_name": rec_map.get(item.recipe_id) if item.recipe_id else None,
                "pos_code": item.pos_code,
                "sale_price": float(a["sale_price"]),
                "cost_price": float(a["cost_price"]),
                "unit_margin": float(a["unit_margin"]),
                "margin_pct": float(a["margin_pct"]),
                "cmv_pct": float(a["cmv_pct"]),
                "target_cmv_percentage": float(target_cmv),
                "suggested_price": float(suggested_price),
                "quantity_sold": float(a["quantity_sold"]),
                "total_revenue": float(a["total_revenue"]),
                "total_cost": float(a["total_cost"]),
                "total_margin": float(a["total_margin"]),
                "sales_share_pct": float(sales_share_pct),
                "revenue_share_pct": float(revenue_share_pct),
                "classification": classification,
                "badge_label": badge_label,
                "action_recommendation": recommendation,
                "is_high_volume": is_high_volume,
                "is_high_margin": is_high_margin
            })

        # Sort items: Stars first, then Plowhorses, Puzzles, Dogs
        order_rank = {"STAR": 1, "PLOWHORSE": 2, "PUZZLE": 3, "DOG": 4}
        final_items.sort(key=lambda x: (order_rank.get(x["classification"], 5), -x["total_margin"]))

        avg_cmv = (total_cost / total_revenue * Decimal("100")).quantize(Decimal("0.1")) if total_revenue > 0 else Decimal("0")
        avg_margin = (total_margin / total_revenue * Decimal("100")).quantize(Decimal("0.1")) if total_revenue > 0 else Decimal("0")

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_items": len(final_items),
                "total_units_sold": float(total_units_sold),
                "total_revenue": float(total_revenue),
                "total_cost": float(total_cost),
                "total_margin": float(total_margin),
                "average_cmv_pct": float(avg_cmv),
                "average_margin_pct": float(avg_margin),
                "cutoff_volume": float(cutoff_volume),
                "cutoff_margin": float(cutoff_margin)
            },
            "bcg_distribution": {
                "stars_count": stars_count,
                "plowhorses_count": plowhorses_count,
                "puzzles_count": puzzles_count,
                "dogs_count": dogs_count
            },
            "items": final_items
        }

    # --- Pricing Simulator ---
    @staticmethod
    async def simulate_pricing(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        item_id: uuid.UUID,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        stmt = select(MenuItem).where(
            MenuItem.id == uuid.UUID(str(item_id)),
            MenuItem.tenant_id == uuid.UUID(str(tenant_id))
        )
        item = (await session.execute(stmt)).scalar_one_or_none()
        if not item:
            raise ValueError("Item de cardápio não encontrado.")

        cost = item.cost_price
        if item.recipe_id:
            calc_cost = await MenuService.get_recipe_unit_cost(session, tenant_id, item.recipe_id)
            if calc_cost > 0:
                cost = calc_cost

        target_cmv = Decimal(str(data.get("target_cmv_pct", item.target_cmv_percentage)))
        if target_cmv <= 0 or target_cmv >= 100:
            target_cmv = Decimal("30.00")

        # If user explicitly gave new_price, compute resulting CMV
        if "new_price" in data and data["new_price"] is not None:
            proposed_price = Decimal(str(data["new_price"]))
            resulting_cmv = (cost / proposed_price * Decimal("100")).quantize(Decimal("0.1")) if proposed_price > 0 else Decimal("0")
        else:
            proposed_price = (cost / (target_cmv / Decimal("100"))).quantize(Decimal("0.01"))
            resulting_cmv = target_cmv

        current_price = item.sale_price
        current_margin = current_price - cost
        current_cmv = (cost / current_price * Decimal("100")).quantize(Decimal("0.1")) if current_price > 0 else Decimal("0")

        proposed_margin = proposed_price - cost
        margin_delta = proposed_margin - current_margin
        margin_pct = (proposed_margin / proposed_price * Decimal("100")).quantize(Decimal("0.1")) if proposed_price > 0 else Decimal("0")

        return {
            "item_id": str(item.id),
            "item_name": item.name,
            "cost_price": float(cost),
            "current_price": float(current_price),
            "current_margin": float(current_margin),
            "current_cmv_pct": float(current_cmv),
            "proposed_price": float(proposed_price),
            "proposed_margin": float(proposed_margin),
            "proposed_margin_pct": float(margin_pct),
            "resulting_cmv_pct": float(resulting_cmv),
            "margin_delta": float(margin_delta),
            "price_delta": float(proposed_price - current_price)
        }
