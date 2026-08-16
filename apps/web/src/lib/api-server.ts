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

const API_URL = process.env.API_URL ?? "http://localhost:8000"

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
