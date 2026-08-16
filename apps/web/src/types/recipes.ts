export interface RecipeListItem {
  id: string
  name: string
  type: string
  pos_code: string | null
  version_number: number | null
  yield_quantity: number | null
  portion_size: number | null
  portion_cost: number
  ingredients_count: number
}

export interface RecipeIngredientDetail {
  sku_id: string
  sku_name: string
  quantity: number
  uom_symbol: string
  loss_percentage: number
  unit_cost: number
  total_cost: number
}

export interface RecipeDetailItem {
  id: string
  name: string
  type: string
  pos_code: string | null
  version_number: number | null
  yield_quantity: number | null
  portion_size: number | null
  ingredients: RecipeIngredientDetail[]
}

export interface CreateRecipePayload {
  name: string
  type: string
  pos_code?: string
}

export interface RecipeIngredientInput {
  sku_id: string
  quantity: number
  uom_id: string
  loss_percentage?: number
}

export interface PublishVersionPayload {
  yield_quantity: number
  yield_uom_id: string
  portion_size: number
  portion_uom_id: string
  ingredients: RecipeIngredientInput[]
}

export interface CatalogSkusAndUoms {
  skus: { id: string; name: string }[]
  uoms: { id: string; name: string; symbol: string }[]
}