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
