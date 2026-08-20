export interface InventoryPolicy {
  id: string;
  location_id: string;
  location_name: string;
  sku_id: string;
  sku_name: string;
  base_uom: string;
  min_stock: number;
  target_stock: number;
  lead_time_days: number;
  abc_class: string | null;
}

export interface UpdatePolicyPayload {
  location_id: string;
  sku_id: string;
  min_stock: number;
  target_stock: number;
  lead_time_days: number;
}

export interface PurchaseSuggestion {
  id: string;
  location_id: string;
  sku_id: string;
  sku_name: string;
  base_uom: string;
  suggested_quantity: number;
  status: string;
  reason: string | null;
  created_at: string;
}

export interface ConvertToPOPayload {
  supplier_id: string;
}

export interface ConvertToPOResponse {
  purchase_order_id: string;
  status: string;
}

export interface OperationalAlert {
  id: string;
  location_id: string | null;
  sku_id: string;
  sku_name: string;
  metric: string;
  observed_value: number;
  reference_value: number;
  threshold: number;
  reason: string;
  is_resolved: boolean;
  created_at: string;
}

export interface DishCMVDrift {
  recipe_id: string;
  recipe_name: string;
  version_number: number;
  current_portion_cost: number;
  target_portion_cost: number;
  drift_percentage: number;
  status: "NORMAL" | "WARNING" | "CRITICAL";
}

export interface StockoutRisk {
  sku_id: string;
  sku_name: string;
  uom_symbol: string;
  on_hand: number;
  daily_burn_rate: number;
  days_remaining: number;
  lead_time_days: number;
  risk_level: "SAFE" | "WARNING" | "CRITICAL";
}
