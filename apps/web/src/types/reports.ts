export interface VarianceReportItem {
  sku_id: string
  sku_name: string
  uom_symbol: string
  theoretical_quantity: number
  theoretical_cost: number
  registered_losses_quantity: number
  total_expected_depletion: number
}

export interface ConsolidatedReport {
  total_revenue: number
  actual_cmv: number
  theoretical_consumption: number
  registered_losses: number
  unexplained_variance: number
  cmv_percentage: number
}

export interface LossReasonItem {
  reason: string
  quantity: number
  total_value: number
}

export interface LossDetailItem {
  sku_name: string
  uom_symbol: string
  reason: string
  quantity: number
  unit_cost: number
  total_value: number
  posted_at: string | null
}

export interface LossesAnalysisReport {
  total_losses_value: number
  by_reason: LossReasonItem[]
  items: LossDetailItem[]
}

export interface StockPositionItem {
  sku_id: string
  sku_name: string
  category_name: string
  uom_symbol: string
  total_quantity: number
  unit_cost: number
  total_value: number
}
