from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import update, insert, and_, func
from decimal import Decimal

from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient

class RecipeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_recipe(self, tenant_id: UUID, name: str, recipe_type: str, pos_code: Optional[str] = None) -> Recipe:
        recipe = Recipe(
            tenant_id=tenant_id,
            name=name,
            type=recipe_type,
            pos_code=pos_code
        )
        self.session.add(recipe)
        await self.session.flush()
        return recipe

    async def publish_recipe_version(self, recipe_id: UUID, tenant_id: UUID, version_data: Dict[str, Any], ingredients_data: List[Dict[str, Any]]) -> RecipeVersion:
        """
        Creates a new published version of a recipe.
        Older versions valid_to dates should be updated if necessary.
        """
        # Close previous active version if any
        now = datetime.now(timezone.utc)
        
        stmt = select(RecipeVersion).where(
            RecipeVersion.recipe_id == recipe_id,
            RecipeVersion.tenant_id == tenant_id,
            RecipeVersion.status == 'PUBLISHED',
            RecipeVersion.valid_to.is_(None)
        )
        prev_version = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if prev_version:
            prev_version.valid_to = now
            
        # Calculate new version number
        stmt = select(func.coalesce(func.max(RecipeVersion.version_number), 0)).where(
            RecipeVersion.recipe_id == recipe_id,
            RecipeVersion.tenant_id == tenant_id
        )
        next_version_num = (await self.session.execute(stmt)).scalar_one() + 1
        
        # Create new version
        new_version = RecipeVersion(
            tenant_id=tenant_id,
            recipe_id=recipe_id,
            version_number=next_version_num,
            status='PUBLISHED',
            valid_from=now,
            valid_to=None,
            yield_quantity=Decimal(version_data['yield_quantity']),
            yield_uom_id=version_data['yield_uom_id'],
            portion_size=Decimal(version_data['portion_size']),
            portion_uom_id=version_data['portion_uom_id']
        )
        self.session.add(new_version)
        await self.session.flush()
        
        # Add ingredients
        for ing in ingredients_data:
            ingredient = RecipeIngredient(
                tenant_id=tenant_id,
                recipe_version_id=new_version.id,
                sku_id=ing['sku_id'],
                quantity=Decimal(ing['quantity']),
                uom_id=ing['uom_id'],
                loss_percentage=Decimal(ing.get('loss_percentage', 0))
            )
            self.session.add(ingredient)
            
        return new_version
