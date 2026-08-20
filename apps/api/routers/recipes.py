from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from modules.recipes.models import Recipe, RecipeVersion, RecipeIngredient
from modules.recipes.service import RecipeService
from modules.catalog.models import SKU, UOM
from modules.inventory.models import StockBalanceProjection
from modules.costing.engine import CostingEngine
from packages.security.dependencies import get_secure_session, require_permission, get_current_user
from packages.security.auth import TokenPayload
from packages.audit.service import AuditService

router = APIRouter(tags=["Recipes"])


class RecipeIngredientInput(BaseModel):
    sku_id: UUID
    quantity: float
    uom_id: UUID
    loss_percentage: Optional[float] = 0


class RecipeVersionInput(BaseModel):
    yield_quantity: float
    yield_uom_id: UUID
    portion_size: float
    portion_uom_id: UUID
    ingredients: List[RecipeIngredientInput]


class RecipeCreate(BaseModel):
    name: str
    type: str
    pos_code: Optional[str] = None


class RecipeListResponse(BaseModel):
    id: UUID
    name: str
    type: str
    pos_code: Optional[str]
    version_number: Optional[int]
    yield_quantity: Optional[float]
    portion_size: Optional[float]
    portion_cost: float
    ingredients_count: int

    model_config = ConfigDict(from_attributes=True)


class RecipeIngredientDetail(BaseModel):
    sku_id: UUID
    sku_name: str
    quantity: float
    uom_symbol: str
    loss_percentage: float
    unit_cost: float
    total_cost: float


class RecipeDetailResponse(BaseModel):
    id: UUID
    name: str
    type: str
    pos_code: Optional[str]
    version_number: Optional[int]
    yield_quantity: Optional[float]
    portion_size: Optional[float]
    ingredients: List[RecipeIngredientDetail]


class SKUListResponse(BaseModel):
    id: UUID
    name: str


class UOMListResponse(BaseModel):
    id: UUID
    name: str
    symbol: str


class CatalogResponse(BaseModel):
    skus: List[SKUListResponse]
    uoms: List[UOMListResponse]


async def get_sku_unit_cost(db: AsyncSession, tenant_id: UUID, sku_id: UUID) -> Decimal:
    """Get the deterministic unit cost for a SKU from the central CostingEngine."""
    return await CostingEngine.get_sku_cost(db, tenant_id, sku_id)


@router.get("", response_model=List[RecipeListResponse])
async def list_recipes(
    _perm: bool = Depends(require_permission("recipes.read")),
    db: AsyncSession = Depends(get_secure_session)
) -> List[RecipeListResponse]:
    """List all recipes for the current tenant with their active published version and cost."""
    # Get tenant_id from RLS context
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context not found")
    
    # Get all recipes for the tenant
    stmt = select(Recipe).where(Recipe.tenant_id == tenant_id).order_by(Recipe.created_at.desc())
    result = await db.execute(stmt)
    recipes = result.scalars().all()
    
    response = []
    for recipe in recipes:
        # Get the active published version
        version_stmt = select(RecipeVersion).where(
            RecipeVersion.recipe_id == recipe.id,
            RecipeVersion.tenant_id == tenant_id,
            RecipeVersion.status == 'PUBLISHED',
            RecipeVersion.valid_to.is_(None)
        )
        version_result = await db.execute(version_stmt)
        version = version_result.scalar_one_or_none()
        
        # Get ingredients for cost calculation
        ingredients_count = 0
        total_cost = Decimal("0")
        
        if version:
            # Get ingredients with SKU and UOM
            ing_stmt = select(RecipeIngredient, SKU, UOM).where(
                RecipeIngredient.recipe_version_id == version.id,
                RecipeIngredient.tenant_id == tenant_id
            ).join(SKU, RecipeIngredient.sku_id == SKU.id).join(UOM, RecipeIngredient.uom_id == UOM.id)
            
            ing_result = await db.execute(ing_stmt)
            ingredients = ing_result.all()
            ingredients_count = len(ingredients)
            
            # Calculate total cost
            for ingredient, sku, uom in ingredients:
                unit_cost = await get_sku_unit_cost(db, tenant_id, sku.id)
                adjusted_qty = Decimal(str(ingredient.quantity)) * (Decimal("1") + Decimal(str(ingredient.loss_percentage)) / Decimal("100"))
                total_cost += adjusted_qty * unit_cost
        
        # Calculate portion cost: total_cost / (yield_quantity / portion_size)
        portion_cost = float(total_cost)
        if version and version.portion_size and version.portion_size > 0:
            if version.yield_quantity and version.yield_quantity > 0:
                num_portions = Decimal(str(version.yield_quantity)) / Decimal(str(version.portion_size))
                if num_portions > 0:
                    portion_cost = float((total_cost / num_portions).quantize(Decimal("0.01")))
        
        response.append(RecipeListResponse(
            id=recipe.id,
            name=recipe.name,
            type=recipe.type,
            pos_code=recipe.pos_code,
            version_number=version.version_number if version else None,
            yield_quantity=float(version.yield_quantity) if version else None,
            portion_size=float(version.portion_size) if version else None,
            portion_cost=portion_cost,
            ingredients_count=ingredients_count
        ))
    
    return response


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
async def get_recipe(
    recipe_id: UUID,
    _perm: bool = Depends(require_permission("recipes.read")),
    db: AsyncSession = Depends(get_secure_session)
) -> RecipeDetailResponse:
    """Get recipe detail with active version ingredients."""
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context not found")
    
    # Get recipe
    stmt = select(Recipe).where(Recipe.id == recipe_id, Recipe.tenant_id == tenant_id)
    result = await db.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    
    # Get active published version
    version_stmt = select(RecipeVersion).where(
        RecipeVersion.recipe_id == recipe.id,
        RecipeVersion.tenant_id == tenant_id,
        RecipeVersion.status == 'PUBLISHED',
        RecipeVersion.valid_to.is_(None)
    )
    version_result = await db.execute(version_stmt)
    version = version_result.scalar_one_or_none()
    
    ingredients = []
    if version:
        ing_stmt = select(RecipeIngredient, SKU, UOM).where(
            RecipeIngredient.recipe_version_id == version.id,
            RecipeIngredient.tenant_id == tenant_id
        ).join(SKU, RecipeIngredient.sku_id == SKU.id).join(UOM, RecipeIngredient.uom_id == UOM.id)
        
        ing_result = await db.execute(ing_stmt)
        for ingredient, sku, uom in ing_result.all():
            unit_cost = await get_sku_unit_cost(db, tenant_id, sku.id)
            adjusted_qty = Decimal(str(ingredient.quantity)) * (Decimal("1") + Decimal(str(ingredient.loss_percentage)) / Decimal("100"))
            total_cost = adjusted_qty * unit_cost
            
            ingredients.append(RecipeIngredientDetail(
                sku_id=sku.id,
                sku_name=sku.name,
                quantity=float(ingredient.quantity),
                uom_symbol=uom.symbol,
                loss_percentage=float(ingredient.loss_percentage),
                unit_cost=float(unit_cost),
                total_cost=float(total_cost)
            ))
    
    return RecipeDetailResponse(
        id=recipe.id,
        name=recipe.name,
        type=recipe.type,
        pos_code=recipe.pos_code,
        version_number=version.version_number if version else None,
        yield_quantity=float(version.yield_quantity) if version else None,
        portion_size=float(version.portion_size) if version else None,
        ingredients=ingredients
    )


@router.post("", response_model=RecipeListResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    data: RecipeCreate,
    _perm: bool = Depends(require_permission("recipes.edit")),
    db: AsyncSession = Depends(get_secure_session)
) -> RecipeListResponse:
    """Create a new recipe."""
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context not found")
    
    try:
        service = RecipeService(db)
        recipe = await service.create_recipe(tenant_id, data.name, data.type, data.pos_code)
        await db.commit()
        
        return RecipeListResponse(
            id=recipe.id,
            name=recipe.name,
            type=recipe.type,
            pos_code=recipe.pos_code,
            version_number=None,
            yield_quantity=None,
            portion_size=None,
            portion_cost=0.0,
            ingredients_count=0
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{recipe_id}/versions", response_model=RecipeDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe_version(
    recipe_id: UUID, 
    version_data: RecipeVersionInput,
    _perm: bool = Depends(require_permission("recipes.publish")),
    user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_secure_session)
) -> RecipeDetailResponse:
    """Create a new published version of a recipe."""
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context not found")
    
    actor_user_id = None
    try:
        actor_user_id = UUID(user.sub)
    except Exception:
        pass

    try:
        # Verify recipe exists and belongs to tenant
        stmt = select(Recipe).where(Recipe.id == recipe_id, Recipe.tenant_id == tenant_id)
        result = await db.execute(stmt)
        recipe = result.scalar_one_or_none()
        
        if not recipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
        
        # Convert ingredients to dict format
        ingredients_dict = [
            {
                "sku_id": ing.sku_id,
                "quantity": ing.quantity,
                "uom_id": ing.uom_id,
                "loss_percentage": ing.loss_percentage
            }
            for ing in version_data.ingredients
        ]
        
        version_dict = {
            "yield_quantity": version_data.yield_quantity,
            "yield_uom_id": version_data.yield_uom_id,
            "portion_size": version_data.portion_size,
            "portion_uom_id": version_data.portion_uom_id
        }
        
        service = RecipeService(db)
        version = await service.publish_recipe_version(recipe_id, tenant_id, version_dict, ingredients_dict)
        
        await AuditService.log_action(
            db=db,
            tenant_id=tenant_id,
            actor_id=actor_user_id or recipe_id,
            action="RECIPE_VERSION_PUBLISHED",
            resource_type="recipes",
            resource_id=recipe_id,
            changes_payload={
                "recipe_id": str(recipe_id),
                "version_number": version.version_number,
                "ingredients_count": len(ingredients_dict)
            }
        )

        await db.commit()
        
        # Return detail response
        ingredients = []
        for ing in version_data.ingredients:
            # Get SKU and UOM for response
            sku_stmt = select(SKU).where(SKU.id == ing.sku_id)
            sku_result = await db.execute(sku_stmt)
            sku = sku_result.scalar_one()
            
            uom_stmt = select(UOM).where(UOM.id == ing.uom_id)
            uom_result = await db.execute(uom_stmt)
            uom = uom_result.scalar_one()
            
            unit_cost = await get_sku_unit_cost(db, tenant_id, sku.id)
            adjusted_qty = Decimal(str(ing.quantity)) * (Decimal("1") + Decimal(str(ing.loss_percentage)) / Decimal("100"))
            total_cost = adjusted_qty * unit_cost
            
            ingredients.append(RecipeIngredientDetail(
                sku_id=sku.id,
                sku_name=sku.name,
                quantity=ing.quantity,
                uom_symbol=uom.symbol,
                loss_percentage=ing.loss_percentage,
                unit_cost=float(unit_cost),
                total_cost=float(total_cost)
            ))
        
        return RecipeDetailResponse(
            id=recipe.id,
            name=recipe.name,
            type=recipe.type,
            pos_code=recipe.pos_code,
            version_number=version.version_number,
            yield_quantity=float(version.yield_quantity),
            portion_size=float(version.portion_size),
            ingredients=ingredients
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog/skus-and-uoms", response_model=CatalogResponse)
async def get_catalog(
    _perm: bool = Depends(require_permission("recipes.read")),
    db: AsyncSession = Depends(get_secure_session)
) -> CatalogResponse:
    """Get SKUs and UOMs for the current tenant."""
    from packages.tenant.rls import get_current_tenant_id
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context not found")
    
    # Get SKUs
    sku_stmt = select(SKU).where(SKU.tenant_id == tenant_id, SKU.is_active == True).order_by(SKU.name)
    sku_result = await db.execute(sku_stmt)
    skus = sku_result.scalars().all()
    
    # Get UOMs
    uom_stmt = select(UOM).where(UOM.tenant_id == tenant_id).order_by(UOM.name)
    uom_result = await db.execute(uom_stmt)
    uoms = uom_result.scalars().all()
    
    return CatalogResponse(
        skus=[SKUListResponse(id=sku.id, name=sku.name) for sku in skus],
        uoms=[UOMListResponse(id=uom.id, name=uom.name, symbol=uom.symbol) for uom in uoms]
    )