export interface SaleLineInput {
  pos_product_id: string
  quantity: number
  unit_price: number
}

export interface SaleInput {
  pos_sale_id: string
  sale_date: string
  total_amount: number
  lines: SaleLineInput[]
}

export interface SalesImportPayload {
  pos_system: string
  import_reference: string
  sales: SaleInput[]
}

export interface SalesImportItem {
  id: string
  pos_system: string
  import_reference: string
  status: string
  created_at: string
  sales_count: number
}

export interface POSMappingItem {
  id: string
  pos_product_id: string
  pos_product_name: string
  recipe_id: string | null
  recipe_name: string | null
  created_at: string
}

export interface POSMappingPayload {
  pos_product_id: string
  pos_product_name: string
  recipe_id: string | null
}

export interface TheoreticalConsumptionItem {
  sku_id: string
  sku_name: string
  uom_symbol: string
  theoretical_quantity: number
  theoretical_cost: number
  registered_losses_quantity: number
  total_expected_depletion: number
}

export interface RegisterLossPayload {
  location_id: string
  sku_id: string
  quantity: number
  reason: string
  actor?: string
}

export interface LossItem {
  id: string
  movement_id: string
  sku_id: string | null
  sku_name: string | null
  quantity: number
  reason: string
  actor: string | null
  created_at: string | null
}
