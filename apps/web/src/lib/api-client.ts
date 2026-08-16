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
  CreateRecipePayload,
  PublishVersionPayload,
} from "@/types/recipes"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? process.env.API_URL ?? "http://localhost:8000"

export async function fetchExtractions(): Promise<DocumentExtractionItem[]> {
  try {
    const response = await fetch(`${API_URL}/documents/extractions`, {
      method: "GET",
      credentials: "include",
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

export async function uploadNFeFile(formData: FormData): Promise<UploadNFEResponse | null> {
  try {
    const response = await fetch(`${API_URL}/documents/upload-nfe`, {
      method: "POST",
      credentials: "include",
      body: formData,
    })

    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return null
      }
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as UploadNFEResponse
  } catch (error) {
    console.error("Failed to upload NFe file:", error)
    return null
  }
}

export async function approveExtractionAction(extractionId: string): Promise<ApproveResponse | null> {
  try {
    const response = await fetch(`${API_URL}/documents/extractions/${extractionId}/approve`, {
      method: "POST",
      credentials: "include",
    })

    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return null
      }
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as ApproveResponse
  } catch (error) {
    console.error("Failed to approve extraction:", error)
    return null
  }
}

export async function fetchRecipes(): Promise<RecipeListItem[]> {
  try {
    const response = await fetch(`${API_URL}/recipes`, {
      method: "GET",
      credentials: "include",
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

export async function fetchRecipeDetail(recipeId: string): Promise<RecipeDetailItem | null> {
  try {
    const response = await fetch(`${API_URL}/recipes/${recipeId}`, {
      method: "GET",
      credentials: "include",
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

export async function fetchCatalogSkusAndUoms(): Promise<CatalogSkusAndUoms> {
  try {
    const response = await fetch(`${API_URL}/recipes/catalog/skus-and-uoms`, {
      method: "GET",
      credentials: "include",
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

export async function createRecipe(payload: CreateRecipePayload): Promise<RecipeListItem | null> {
  try {
    const response = await fetch(`${API_URL}/recipes`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return null
      }
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as RecipeListItem
  } catch (error) {
    console.error("Failed to create recipe:", error)
    return null
  }
}

export async function publishRecipeVersion(recipeId: string, payload: PublishVersionPayload): Promise<RecipeDetailItem | null> {
  try {
    const response = await fetch(`${API_URL}/recipes/${recipeId}/versions`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      if (response.status === 500 || response.status === 502 || response.status === 503 || response.status === 504) {
        return null
      }
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `API call failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return data as RecipeDetailItem
  } catch (error) {
    console.error("Failed to publish recipe version:", error)
    return null
  }
}

import {
  InventorySessionItem,
  InventorySessionDetail,
  CreateSessionPayload,
  CountLinePayload,
  CloseResultItem
} from "@/types/inventory-sessions"

export async function fetchInventorySessions(): Promise<InventorySessionItem[]> {
  try {
    const response = await fetch(`${API_URL}/inventory/sessions`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function createInventorySession(payload: CreateSessionPayload): Promise<InventorySessionItem | null> {
  try {
    const response = await fetch(`${API_URL}/inventory/sessions`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchInventorySessionDetail(id: string): Promise<InventorySessionDetail | null> {
  try {
    const response = await fetch(`${API_URL}/inventory/sessions/${id}`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function addCountLine(id: string, payload: CountLinePayload): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/inventory/sessions/${id}/lines`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    return response.ok
  } catch (err) {
    console.error(err)
    return false
  }
}

export async function closeInventorySession(id: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/inventory/sessions/${id}/close`, {
      method: "POST",
      credentials: "include",
    })
    return response.ok
  } catch (err) {
    console.error(err)
    return false
  }
}

export async function fetchCloseResults(id: string): Promise<CloseResultItem[]> {
  try {
    const response = await fetch(`${API_URL}/inventory/sessions/${id}/results`, {
      method: "GET",
      credentials: "include",
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
  PurchaseOrderItem,
  PurchaseOrderDetail,
  CreatePOPayload,
  ReceivePOPayload,
  InvoicePOPayload,
  EnrichedReconResponse
} from "@/types/purchase-orders"

export async function fetchPurchaseOrders(): Promise<PurchaseOrderItem[]> {
  try {
    const response = await fetch(`${API_URL}/purchasing/orders`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function fetchPurchaseOrderDetail(id: string): Promise<PurchaseOrderDetail | null> {
  try {
    const response = await fetch(`${API_URL}/purchasing/orders/${id}`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function createPurchaseOrder(payload: CreatePOPayload): Promise<PurchaseOrderItem | null> {
  try {
    const response = await fetch(`${API_URL}/purchasing/orders`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function receivePurchaseOrder(id: string, payload: ReceivePOPayload): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/purchasing/orders/${id}/receive`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    return response.ok
  } catch (err) {
    console.error(err)
    return false
  }
}

export async function invoicePurchaseOrder(id: string, payload: InvoicePOPayload): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/purchasing/orders/${id}/invoice`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    return response.ok
  } catch (err) {
    console.error(err)
    return false
  }
}

export async function fetchPOReconciliations(po_id: string): Promise<EnrichedReconResponse[]> {
  try {
    const response = await fetch(`${API_URL}/purchasing/orders/${po_id}/reconciliation`, {
      method: "GET",
      credentials: "include",
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
  SalesImportItem,
  SalesImportPayload,
  POSMappingItem,
  POSMappingPayload,
  TheoreticalConsumptionItem,
  RegisterLossPayload,
  LossItem
} from "@/types/sales"

export async function fetchSalesImports(): Promise<SalesImportItem[]> {
  try {
    const response = await fetch(`${API_URL}/sales/imports`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function importSales(payload: SalesImportPayload): Promise<SalesImportItem | null> {
  try {
    const response = await fetch(`${API_URL}/sales/import`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchPOSMappings(): Promise<POSMappingItem[]> {
  try {
    const response = await fetch(`${API_URL}/sales/mappings`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function createOrUpdatePOSMapping(payload: POSMappingPayload): Promise<POSMappingItem | null> {
  try {
    const response = await fetch(`${API_URL}/sales/mappings`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchTheoreticalVsActual(): Promise<TheoreticalConsumptionItem[]> {
  try {
    const response = await fetch(`${API_URL}/sales/theoretical-vs-actual`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function registerLoss(payload: RegisterLossPayload): Promise<LossItem | null> {
  try {
    const response = await fetch(`${API_URL}/inventory/losses`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchLosses(): Promise<LossItem[]> {
  try {
    const response = await fetch(`${API_URL}/inventory/losses`, {
      method: "GET",
      credentials: "include",
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
  UpdatePolicyPayload,
  PurchaseSuggestion,
  ConvertToPOPayload,
  ConvertToPOResponse,
  OperationalAlert
} from "@/types/intelligence"

export async function fetchPolicies(): Promise<InventoryPolicy[]> {
  try {
    const response = await fetch(`${API_URL}/intelligence/policies`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function updatePolicy(payload: UpdatePolicyPayload): Promise<InventoryPolicy | null> {
  try {
    const response = await fetch(`${API_URL}/intelligence/policies`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function calculateABC(locationId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/intelligence/abc/calculate`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location_id: locationId }),
    })
    return response.ok
  } catch (err) {
    console.error(err)
    return false
  }
}

export async function fetchSuggestions(): Promise<PurchaseSuggestion[]> {
  try {
    const response = await fetch(`${API_URL}/intelligence/suggestions`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function generateSuggestions(locationId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/intelligence/suggestions/generate`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location_id: locationId }),
    })
    return response.ok
  } catch (err) {
    console.error(err)
    return false
  }
}

export async function convertToPO(suggestionId: string, payload: ConvertToPOPayload): Promise<ConvertToPOResponse | null> {
  try {
    const response = await fetch(`${API_URL}/intelligence/suggestions/${suggestionId}/convert-to-po`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchAlerts(): Promise<OperationalAlert[]> {
  try {
    const response = await fetch(`${API_URL}/intelligence/alerts`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function generateAlerts(locationId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/intelligence/alerts/generate`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location_id: locationId }),
    })
    return response.ok
  } catch (err) {
    console.error(err)
    return false
  }
}

export async function resolveAlert(alertId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/intelligence/alerts/${alertId}/resolve`, {
      method: "POST",
      credentials: "include",
    })
    return response.ok
  } catch (err) {
    console.error(err)
    return false
  }
}

export async function fetchNotificationsClient(): Promise<any[]> {
  try {
    const response = await fetch(`${API_URL}/notifications`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch notifications:", err)
    return []
  }
}

export async function markNotificationReadClient(notificationId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/notifications/${notificationId}/read`, {
      method: "PUT",
      credentials: "include",
    })
    return response.ok
  } catch (err) {
    console.error("Failed to mark notification as read:", err)
    return false
  }
}

export async function submitOnboardingClient(restaurantName: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const response = await fetch(`${API_URL}/onboarding`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ restaurant_name: restaurantName }),
    })
    const data = await response.json()
    if (!response.ok) {
      return { success: false, error: data.detail || "Falha ao criar restaurante" }
    }
    return { success: true, data }
  } catch (err: any) {
    return { success: false, error: err.message || "Erro de conexão" }
  }
}

export function getExportInventoryCsvUrl(locationId?: string): string {
  return `${API_URL}/reports/inventory/export/csv${locationId ? `?location_id=${locationId}` : ""}`
}

export function getExportSpedUrl(): string {
  return `${API_URL}/reports/inventory/export/sped`
}