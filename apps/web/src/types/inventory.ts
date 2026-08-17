export interface InventoryBalance {
  sku_id: string
  sku_name: string
  category_name: string | null
  base_uom: string
  quantity: string
  total_value: string
  unit_cost: string
  location_name: string
}

export interface FetchInventoryBalancesParams {
  location_id?: string
}

export interface FetchInventoryBalancesResponse {
  data: InventoryBalance[]
  error?: string
}

export type StockTransferStatus = 'DRAFT' | 'IN_TRANSIT' | 'RECEIVED' | 'CANCELLED';

export interface StockTransferItem {
  id: string;
  sku_id: string;
  sku_name: string;
  quantity_sent: number;
  quantity_received?: number | null;
  unit_cost: number;
}

export interface StockTransfer {
  id: string;
  tenant_id: string;
  transfer_number: string;
  origin_location_id: string;
  origin_location_name: string;
  destination_location_id: string;
  destination_location_name: string;
  status: StockTransferStatus;
  items_count?: number;
  dispatched_at?: string | null;
  received_at?: string | null;
  notes?: string | null;
  items?: StockTransferItem[];
  created_at: string;
}

export interface CreateStockTransferPayload {
  origin_location_id: string;
  destination_location_id: string;
  items: { sku_id: string; quantity_sent: number }[];
  notes?: string;
}