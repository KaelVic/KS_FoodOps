export interface InventoryCountLineItem {
  id: string
  sku_id: string
  counted_quantity: number
}

export interface InventorySessionItem {
  id: string
  status: string // "DRAFT" | "OPEN" | "CLOSED"
  cutoff_at: string | null
  created_at: string
  closed_at: string | null
}

export interface InventorySessionDetail extends InventorySessionItem {
  lines: InventoryCountLineItem[]
}

export interface CreateSessionPayload {
  location_id: string
}

export interface CountLinePayload {
  sku_id: string
  counted_quantity: number
}

export interface CloseResultItem {
  sku_id: string
  expected_quantity: number
  counted_quantity: number
  variance_quantity: number
  variance_value: number
}
