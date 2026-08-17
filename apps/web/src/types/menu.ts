export type BCGClassification = 'STAR' | 'PLOWHORSE' | 'PUZZLE' | 'DOG';

export interface MenuCategory {
  id: string;
  tenant_id?: string;
  name: string;
  display_order: number;
  is_active: boolean;
  created_at?: string;
}

export interface MenuItem {
  id: string;
  category_id: string | null;
  category_name?: string;
  recipe_id: string | null;
  recipe_name?: string | null;
  name: string;
  pos_code: string | null;
  description: string | null;
  sale_price: number;
  cost_price: number;
  unit_margin: number;
  margin_pct: number;
  cmv_pct: number;
  target_cmv_percentage: number;
  suggested_price: number;
  is_active: boolean;
  display_order: number;
  created_at?: string;
}

export interface BCGItem {
  item_id: string;
  pos_code: string;
  name: string;
  category_name: string;
  units_sold: number;
  sale_price: number;
  cost_price: number;
  unit_margin: number;
  total_revenue: number;
  total_cost: number;
  total_margin: number;
  cmv_pct: number;
  volume_share_pct: number;
  revenue_share_pct: number;
  classification: BCGClassification;
  is_high_volume: boolean;
  is_high_margin: boolean;
  recommendation: string;
}

export interface BCGSummary {
  total_revenue: number;
  total_cost: number;
  total_margin: number;
  average_cmv_pct: number;
  total_units_sold: number;
  total_items_analyzed: number;
  cutoff_volume: number;
  cutoff_margin: number;
}

export interface BCGDistribution {
  stars: number;
  plowhorses: number;
  puzzles: number;
  dogs: number;
}

export interface MenuEngineeringResponse {
  summary: BCGSummary;
  bcg_distribution: BCGDistribution;
  items: BCGItem[];
  analyzed_at: string;
}

export interface SimulatePricingPayload {
  target_cmv_pct?: number;
  new_price?: number;
}

export interface SimulatePricingResponse {
  item_id: string;
  item_name: string;
  cost_price: number;
  current_price: number;
  current_margin: number;
  current_cmv_pct: number;
  proposed_price: number;
  proposed_margin: number;
  proposed_margin_pct: number;
  resulting_cmv_pct: number;
  margin_delta: number;
  price_delta: number;
}
