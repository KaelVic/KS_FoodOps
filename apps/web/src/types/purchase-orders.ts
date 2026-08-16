export interface PurchaseOrderLineItem {
  id: string
  sku_id: string
  ordered_quantity: number
  unit_price: number
}

export interface PurchaseOrderItem {
  id: string
  supplier_id: string
  location_id: string
  status: string
  order_date: string
  expected_delivery_date: string | null
  created_at: string
}

export interface PurchaseOrderDetail extends PurchaseOrderItem {
  lines: PurchaseOrderLineItem[]
}

export interface EnrichedReconResponse {
  id: string
  po_line_id: string
  sku_id: string
  sku_name: string
  uom_symbol: string
  ordered_qty: number
  ordered_price: number
  received_qty: number | null
  received_price: number | null
  invoiced_qty: number | null
  invoiced_price: number | null
  status: string
}

export interface CreatePOLinePayload {
  sku_id: string
  ordered_quantity: number
  unit_price: number
}

export interface CreatePOPayload {
  supplier_id: string
  location_id: string
  expected_delivery_date: string | null
  lines: CreatePOLinePayload[]
}

export interface ReceivePOLinePayload {
  po_line_id: string
  sku_id: string
  quantity: number
  unit_price: number
}

export interface ReceivePOPayload {
  lines: ReceivePOLinePayload[]
}

export interface InvoiceLinePayload {
  po_line_id: string
  sku_id: string
  invoiced_quantity: number
  unit_price: number
}

export interface InvoicePOPayload {
  invoice_number: string
  issue_date: string
  due_date: string | null
  total_amount: number
  lines: InvoiceLinePayload[]
}
