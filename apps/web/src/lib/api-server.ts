import { cookies } from "next/headers"
import { InventoryBalance, FetchInventoryBalancesParams } from "@/types/inventory"
import {
  DocumentExtractionItem,
  DocumentExtractionDetail,
  UploadNFEResponse,
  ApproveResponse,
} from "@/types/documents"
import {
  RecipeListItem,
  RecipeDetailItem,
  CatalogSkusAndUoms,
} from "@/types/recipes"
import {
  MenuCategory,
  MenuItem,
  MenuEngineeringResponse,
  SimulatePricingResponse,
} from "@/types/menu"

const API_URL = 
  process.env.API_URL || 
  process.env.NEXT_PUBLIC_API_URL || 
  (process.env.NODE_ENV === "production" ? "http://api:8000" : "http://localhost:8000")

async function getAuthHeaders(): Promise<Headers> {
  const cookieStore = await cookies()
  const token = cookieStore.get("session_token")?.value
  const tenantId = cookieStore.get("active_tenant_id")?.value

  if (!token || !tenantId) {
    throw new Error("Missing auth credentials")
  }

  const headers = new Headers()
  headers.set("Authorization", `Bearer ${token}`)
  headers.set("X-Tenant-ID", tenantId)
  return headers
}

export async function fetchInventoryBalancesServer(params: FetchInventoryBalancesParams = {}): Promise<InventoryBalance[]> {
  try {
    const headers = await getAuthHeaders()
    
    const searchParams = new URLSearchParams()
    if (params.location_id) {
      searchParams.set("location_id", params.location_id)
    }

    const response = await fetch(`${API_URL}/inventory/balances?${searchParams.toString()}`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return []
      }
      throw new Error(`API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as InventoryBalance[]
  } catch (error) {
    console.error("Failed to fetch inventory balances:", error)
    return []
  }
}

export async function fetchTheoreticalBalancesServer(locationId?: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const searchParams = new URLSearchParams()
    if (locationId) {
      searchParams.set("location_id", locationId)
    }

    const response = await fetch(`${API_URL}/inventory/theoretical-balances?${searchParams.toString()}`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      return []
    }

    return await response.json()
  } catch (error) {
    console.error("Failed to fetch theoretical balances:", error)
    return []
  }
}

export async function fetchDishCMVDriftServer(threshold: number = 5.0): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/intelligence/dishes/cmv-drift?threshold=${threshold}`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      return []
    }

    return await response.json()
  } catch (error) {
    console.error("Failed to fetch dish CMV drift:", error)
    return []
  }
}

export async function fetchStockoutRisksServer(locationId?: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const searchParams = new URLSearchParams()
    if (locationId) {
      searchParams.set("location_id", locationId)
    }

    const response = await fetch(`${API_URL}/intelligence/stockout-risks?${searchParams.toString()}`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      return []
    }

    return await response.json()
  } catch (error) {
    console.error("Failed to fetch stockout risks:", error)
    return []
  }
}

export async function fetchExtractionsServer(): Promise<DocumentExtractionItem[]> {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(`${API_URL}/documents/extractions`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return []
      }
      throw new Error(`API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as DocumentExtractionItem[]
  } catch (error) {
    console.error("Failed to fetch extractions:", error)
    return []
  }
}

export async function fetchExtractionDetailServer(extractionId: string): Promise<DocumentExtractionDetail | null> {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(`${API_URL}/documents/extractions/${extractionId}`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      if (response.status === 404) {
        return null
      }
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return null
      }
      throw new Error(`API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as DocumentExtractionDetail
  } catch (error) {
    console.error("Failed to fetch extraction detail:", error)
    return null
  }
}

export async function fetchRecipesServer(): Promise<RecipeListItem[]> {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(`${API_URL}/recipes`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return []
      }
      throw new Error(`API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as RecipeListItem[]
  } catch (error) {
    console.error("Failed to fetch recipes:", error)
    return []
  }
}

export async function fetchRecipeDetailServer(recipeId: string): Promise<RecipeDetailItem | null> {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(`${API_URL}/recipes/${recipeId}`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      if (response.status === 404) {
        return null
      }
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return null
      }
      throw new Error(`API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as RecipeDetailItem
  } catch (error) {
    console.error("Failed to fetch recipe detail:", error)
    return null
  }
}

export async function fetchCatalogSkusAndUomsServer(): Promise<CatalogSkusAndUoms> {
  try {
    const headers = await getAuthHeaders()

    const response = await fetch(`${API_URL}/recipes/catalog/skus-and-uoms`, {
      method: "GET",
      headers,
      cache: "no-store",
    })

    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return { skus: [], uoms: [] }
      }
      throw new Error(`API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as CatalogSkusAndUoms
  } catch (error) {
    console.error("Failed to fetch catalog SKUs and UOMs:", error)
    return { skus: [], uoms: [] }
  }
}

import { InventorySessionItem, InventorySessionDetail } from "@/types/inventory-sessions"

export async function fetchInventorySessionsServer(): Promise<InventorySessionItem[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/inventory/sessions`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchInventorySessionDetailServer(id: string): Promise<InventorySessionDetail | null> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/inventory/sessions/${id}`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

import { PurchaseOrderItem, PurchaseOrderDetail } from "@/types/purchase-orders"

export async function fetchPurchaseOrdersServer(): Promise<PurchaseOrderItem[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/purchasing/orders`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchPurchaseOrderDetailServer(id: string): Promise<PurchaseOrderDetail | null> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/purchasing/orders/${id}`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

import {
  SalesImportItem,
  POSMappingItem,
  TheoreticalConsumptionItem,
  LossItem
} from "@/types/sales"

export async function fetchSalesImportsServer(): Promise<SalesImportItem[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/sales/imports`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchPOSMappingsServer(): Promise<POSMappingItem[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/sales/mappings`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchTheoreticalVsActualServer(): Promise<TheoreticalConsumptionItem[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/sales/theoretical-vs-actual`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchLossesServer(): Promise<LossItem[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/inventory/losses`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

import {
  InventoryPolicy,
  PurchaseSuggestion,
  OperationalAlert
} from "@/types/intelligence"

export async function fetchPoliciesServer(): Promise<InventoryPolicy[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/intelligence/policies`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchSuggestionsServer(): Promise<PurchaseSuggestion[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/intelligence/suggestions`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchAlertsServer(): Promise<OperationalAlert[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/intelligence/alerts`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchReconciliationServer(poId: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/purchasing/orders/${poId}/reconciliation`, {
      method: "GET",
      headers,
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (error) {
    console.error("Failed to fetch reconciliation:", error)
    return []
  }
}

import { SKU, Supplier, Location, TeamMember } from "@/types/master-data"

export async function fetchSkusServer(): Promise<SKU[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/catalog/skus`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function fetchSuppliersServer(): Promise<Supplier[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/suppliers`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function fetchLocationsServer(): Promise<Location[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/locations`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function fetchTeamServer(): Promise<TeamMember[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/team`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

import { ConsolidatedReport, LossesAnalysisReport, StockPositionItem } from "@/types/reports"

export async function fetchConsolidatedReportServer(
  locationId: string,
  startDate: string,
  endDate: string
): Promise<ConsolidatedReport | null> {
  try {
    const headers = await getAuthHeaders()
    const url = `${API_URL}/reports/consolidated?location_id=${locationId}&start_date=${startDate}&end_date=${endDate}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    return null
  }
}

export async function fetchLossesReportServer(
  startDate?: string,
  endDate?: string
): Promise<LossesAnalysisReport | null> {
  try {
    const headers = await getAuthHeaders()
    let url = `${API_URL}/reports/losses`
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    if (params.toString()) url += `?${params.toString()}`
    
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    return null
  }
}

export async function fetchStockPositionServer(
  locationId?: string
): Promise<StockPositionItem[]> {
  try {
    const headers = await getAuthHeaders()
    let url = `${API_URL}/reports/inventory/position`
    if (locationId) url += `?location_id=${locationId}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

import {
  FinancialCategory,
  CostCenter,
  BankAccount,
  PayableBill,
  PayablesDashboardMetrics
} from "@/types/financial"

export async function fetchPayablesDashboardServer(): Promise<PayablesDashboardMetrics | null> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/financial/payables/dashboard`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    return null
  }
}

export async function fetchPayableBillsServer(status?: string): Promise<PayableBill[]> {
  try {
    const headers = await getAuthHeaders()
    let url = `${API_URL}/financial/payables`
    if (status) url += `?status=${status}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function fetchFinancialCategoriesServer(): Promise<FinancialCategory[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/financial/categories`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function fetchCostCentersServer(): Promise<CostCenter[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/financial/cost-centers`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function fetchBankAccountsServer(): Promise<BankAccount[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/financial/bank-accounts`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

import {
  PaymentAcquirer,
  ReceivableInvoice,
  ReceivablesDashboardMetrics
} from "@/types/financial"

export async function fetchReceivablesDashboardServer(): Promise<ReceivablesDashboardMetrics | null> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/financial/receivables/dashboard`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    return null
  }
}

export async function fetchReceivableInvoicesServer(status?: string, channel?: string): Promise<ReceivableInvoice[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (status) params.append("status", status)
    if (channel) params.append("channel", channel)
    const url = `${API_URL}/financial/receivables${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function fetchPaymentAcquirersServer(): Promise<PaymentAcquirer[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/financial/acquirers`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

import {
  CashFlowProjection,
  FinancialDREResponse,
  BankStatementTransaction
} from "@/types/financial"

export async function fetchCashFlowServer(startDate?: string, endDate?: string): Promise<CashFlowProjection | null> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    const url = `${API_URL}/financial/cash-flow${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchFinancialDREServer(startDate?: string, endDate?: string, viewType?: string): Promise<FinancialDREResponse | null> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    if (viewType) params.append("view_type", viewType)
    const url = `${API_URL}/financial/dre${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchBankStatementsServer(bankAccountId?: string, isReconciled?: boolean): Promise<BankStatementTransaction[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (bankAccountId) params.append("bank_account_id", bankAccountId)
    if (isReconciled !== undefined) params.append("is_reconciled", String(isReconciled))
    const url = `${API_URL}/financial/bank-statements${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

// --- Menu & Menu Engineering Server Fetchers ---

export async function fetchMenuCategoriesServer(): Promise<MenuCategory[]> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/menu/categories`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch menu categories:", err)
    return []
  }
}

export async function fetchMenuItemsServer(categoryId?: string, isActive?: boolean): Promise<MenuItem[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (categoryId) params.append("category_id", categoryId)
    if (isActive !== undefined) params.append("is_active", String(isActive))
    const url = `${API_URL}/menu/items${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch menu items:", err)
    return []
  }
}

export async function fetchMenuEngineeringServer(startDate?: string, endDate?: string, categoryId?: string): Promise<MenuEngineeringResponse | null> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    if (categoryId) params.append("category_id", categoryId)
    const url = `${API_URL}/menu/engineering${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch menu engineering:", err)
    return null
  }
}

import { DiningTable, Order, KDSItem, DeliveryKanban } from "@/types/orders"

export async function fetchDiningTablesServer(section?: string, status?: string): Promise<DiningTable[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (section) params.append("section", section)
    if (status) params.append("status", status)
    const url = `${API_URL}/orders/tables${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch dining tables:", err)
    return []
  }
}

export async function fetchOrdersServer(channel?: string, status?: string, isPaid?: boolean): Promise<Order[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (channel) params.append("channel", channel)
    if (status) params.append("status", status)
    if (isPaid !== undefined) params.append("is_paid", String(isPaid))
    const url = `${API_URL}/orders${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch orders:", err)
    return []
  }
}

export async function fetchKDSQueueServer(station?: string): Promise<KDSItem[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (station) params.append("station", station)
    const url = `${API_URL}/orders/kds/queue${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch KDS queue:", err)
    return []
  }
}

export async function fetchDeliveryKanbanServer(): Promise<DeliveryKanban | null> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/orders/delivery/kanban`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch delivery kanban:", err)
    return null
  }
}

export async function fetchProductionOrdersServer(status?: string, locationId?: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (status) params.append("status", status)
    if (locationId) params.append("location_id", locationId)
    const url = `${API_URL}/production/orders${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch production orders:", err)
    return []
  }
}

export async function fetchStockTransfersServer(status?: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (status) params.append("status", status)
    const url = `${API_URL}/inventory/transfers${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch stock transfers:", err)
    return []
  }
}

// --- RFQ / B2B Cotações Server ---
export async function fetchRFQsServer(status?: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const url = status ? `${API_URL}/purchasing/rfqs?status_filter=${status}` : `${API_URL}/purchasing/rfqs`
    const response = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch RFQs:", err)
    return []
  }
}

export async function fetchRFQDetailsServer(rfqId: string): Promise<any | null> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/purchasing/rfqs/${rfqId}`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch RFQ details:", err)
    return null
  }
}

export async function fetchRFQComparisonServer(rfqId: string): Promise<any | null> {
  try {
    const headers = await getAuthHeaders()
    const response = await fetch(`${API_URL}/purchasing/rfqs/${rfqId}/comparison`, { method: "GET", headers, cache: "no-store" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch RFQ comparison:", err)
    return null
  }
}

// --- Team & Labor Server (Phase 8) ---
export async function fetchEmployeesServer(department?: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const url = department ? `${API_URL}/team/employees?department=${department}` : `${API_URL}/team/employees`
    const res = await fetch(url, { method: "GET", headers, cache: "no-store" })
    if (!res.ok) return []
    return await res.json()
  } catch (err) {
    console.error("Failed to fetch employees:", err)
    return []
  }
}

export async function fetchShiftsServer(startDate?: string, endDate?: string): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    const res = await fetch(`${API_URL}/team/shifts?${params.toString()}`, { method: "GET", headers, cache: "no-store" })
    if (!res.ok) return []
    return await res.json()
  } catch (err) {
    console.error("Failed to fetch shifts:", err)
    return []
  }
}

export async function fetchTimeClockServer(): Promise<any[]> {
  try {
    const headers = await getAuthHeaders()
    const res = await fetch(`${API_URL}/team/time-clock`, { method: "GET", headers, cache: "no-store" })
    if (!res.ok) return []
    return await res.json()
  } catch (err) {
    console.error("Failed to fetch time clock:", err)
    return []
  }
}

export async function fetchPrimeCostServer(startDate?: string, endDate?: string): Promise<any | null> {
  try {
    const headers = await getAuthHeaders()
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    const res = await fetch(`${API_URL}/team/prime-cost?${params.toString()}`, { method: "GET", headers, cache: "no-store" })
    if (!res.ok) return null
    return await res.json()
  } catch (err) {
    console.error("Failed to fetch prime cost:", err)
    return null
  }
}

// --- FoodOps Copilot Server (Phase 9) ---
export async function fetchCopilotAuditServer(): Promise<any | null> {
  try {
    const headers = await getAuthHeaders()
    const res = await fetch(`${API_URL}/copilot/audit`, { method: "GET", headers, cache: "no-store" })
    if (!res.ok) return null
    return await res.json()
  } catch (err) {
    console.error("Failed to fetch copilot audit:", err)
    return null
  }
}

export async function fetchTodayBriefingServer(): Promise<any | null> {
  try {
    const headers = await getAuthHeaders()
    const res = await fetch(`${API_URL}/copilot/briefings/today`, { method: "GET", headers, cache: "no-store" })
    if (!res.ok) return null
    return await res.json()
  } catch (err) {
    console.error("Failed to fetch today briefing:", err)
    return null
  }
}









