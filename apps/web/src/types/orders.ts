export type TableStatus = "AVAILABLE" | "OCCUPIED" | "RESERVED" | "BILL_REQUESTED" | "CLEANING"
export type OrderChannel = "DINE_IN" | "TAKEOUT" | "DELIVERY" | "QR_CODE" | "WHATSAPP"
export type OrderStatus = "PENDING" | "PREPARING" | "READY" | "OUT_FOR_DELIVERY" | "COMPLETED" | "CANCELLED"
export type KDSItemStatus = "QUEUED" | "PREPARING" | "READY" | "SERVED" | "CANCELLED"
export type ProductionStation = "KITCHEN" | "BAR" | "PIZZERIA" | "DESSERT"
export type SLAStatus = "GREEN" | "YELLOW" | "RED"

export interface DiningTable {
  id: string
  table_number: string
  capacity: number
  section: string
  status: TableStatus
  active_order_id?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface OrderItem {
  id: string
  menu_item_id?: string | null
  name: string
  quantity: number
  unit_price: number
  total_price: number
  preparation_notes?: string | null
  production_station: ProductionStation
  status: KDSItemStatus
  started_at?: string | null
  ready_at?: string | null
  served_at?: string | null
}

export interface Order {
  id: string
  order_number: string
  channel: OrderChannel
  status: OrderStatus
  table_id?: string | null
  customer_name?: string | null
  customer_phone?: string | null
  delivery_address?: string | null
  waiter_name?: string | null
  subtotal: number
  delivery_fee: number
  discount_amount: number
  total_amount: number
  notes?: string | null
  payment_method?: string | null
  is_paid: boolean
  created_at?: string | null
  items: OrderItem[]
}

export interface KDSItem {
  item_id: string
  order_id: string
  order_number: string
  channel: OrderChannel
  table_number?: string | null
  customer_name: string
  waiter_name?: string | null
  item_name: string
  quantity: number
  preparation_notes?: string | null
  production_station: ProductionStation
  status: KDSItemStatus
  created_at: string
  started_at?: string | null
  ready_at?: string | null
  wait_minutes: number
  sla_status: SLAStatus
}

export interface DeliveryKanban {
  PENDING: DeliveryOrderSummary[]
  PREPARING: DeliveryOrderSummary[]
  READY: DeliveryOrderSummary[]
  OUT_FOR_DELIVERY: DeliveryOrderSummary[]
  COMPLETED: DeliveryOrderSummary[]
}

export interface DeliveryOrderSummary {
  id: string
  order_number: string
  channel: OrderChannel
  status: OrderStatus
  customer_name: string
  customer_phone?: string | null
  delivery_address?: string | null
  subtotal: number
  delivery_fee: number
  total_amount: number
  notes?: string | null
  payment_method: string
  is_paid: boolean
  created_at: string
  wait_minutes: number
  items_count: number
  items_summary: string[]
}
