export type ProductionOrderStatus = 'PLANNED' | 'IN_PRODUCTION' | 'COMPLETED' | 'CANCELLED';

export interface ProductionOrderIngredient {
  id: string;
  sku_id: string;
  sku_name: string;
  planned_quantity: number;
  actual_quantity?: number | null;
  unit_cost: number;
  total_cost: number;
}

export interface ProductionOrder {
  id: string;
  tenant_id: string;
  order_number: string;
  recipe_id: string;
  recipe_name: string;
  recipe_version_id: string;
  produced_sku_id: string;
  produced_sku_name: string;
  location_id: string;
  location_name: string;
  status: ProductionOrderStatus;
  planned_quantity: number;
  actual_quantity?: number | null;
  batch_number?: string | null;
  produced_at?: string | null;
  expiration_date?: string | null;
  total_cost: number;
  unit_cost: number;
  notes?: string | null;
  ingredients?: ProductionOrderIngredient[];
  created_at: string;
}

export interface CreateProductionOrderPayload {
  recipe_id: string;
  produced_sku_id: string;
  location_id: string;
  planned_quantity: number;
  batch_number?: string;
  expiration_date?: string;
  notes?: string;
}

export interface CompleteProductionPayload {
  actual_quantity?: number;
  batch_number?: string;
  expiration_date?: string;
  actual_ingredient_quantities?: Record<string, number>;
}
