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