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
import {
  MenuCategory,
  MenuItem,
  MenuEngineeringResponse,
  SimulatePricingPayload,
  SimulatePricingResponse,
} from "@/types/menu"

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

import { Location, Supplier } from "@/types/master-data"

export async function fetchLocations(): Promise<Location[]> {
  try {
    const response = await fetch(`${API_URL}/locations`, {
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

export async function fetchSuppliers(): Promise<Supplier[]> {
  try {
    const response = await fetch(`${API_URL}/suppliers`, {
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
  CreatePayableBillPayload,
  SettleInstallmentPayload,
  PayableBill,
  BankAccount,
  FinancialCategory,
  CostCenter
} from "@/types/financial"

export async function createPayableBill(payload: CreatePayableBillPayload): Promise<PayableBill | null> {
  try {
    const response = await fetch(`${API_URL}/financial/payables`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to create payable bill:", err)
    return null
  }
}

export async function settleInstallment(installmentId: string, payload: SettleInstallmentPayload): Promise<PayableBill | null> {
  try {
    const response = await fetch(`${API_URL}/financial/payables/installments/${installmentId}/settle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to settle installment:", err)
    return null
  }
}

export async function cancelPayableBill(billId: string, reason?: string): Promise<boolean> {
  try {
    let url = `${API_URL}/financial/payables/${billId}`
    if (reason) url += `?reason=${encodeURIComponent(reason)}`
    const response = await fetch(url, {
      method: "DELETE",
      credentials: "include",
    })
    return response.ok
  } catch (err) {
    console.error("Failed to cancel payable bill:", err)
    return false
  }
}

export async function createBankAccount(payload: {
  name: string
  account_type?: string
  bank_code?: string
  agency_number?: string
  account_number?: string
  pix_key?: string
  initial_balance?: number
}): Promise<BankAccount | null> {
  try {
    const response = await fetch(`${API_URL}/financial/bank-accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to create bank account:", err)
    return null
  }
}

export async function createFinancialCategory(payload: {
  code?: string
  name: string
  type: string
  parent_id?: string
}): Promise<FinancialCategory | null> {
  try {
    const response = await fetch(`${API_URL}/financial/categories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to create category:", err)
    return null
  }
}

export async function createCostCenter(payload: {
  code?: string
  name: string
  description?: string
}): Promise<CostCenter | null> {
  try {
    const response = await fetch(`${API_URL}/financial/cost-centers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to create cost center:", err)
    return null
  }
}

// --- Accounts Receivable Client Mutations ---

import {
  CreateReceivableInvoicePayload,
  SettleReceivableInstallmentPayload,
  CreateAcquirerPayload,
  ReceivableInvoice,
  PaymentAcquirer
} from "@/types/financial"

export async function createReceivableInvoice(payload: CreateReceivableInvoicePayload): Promise<ReceivableInvoice | null> {
  try {
    const response = await fetch(`${API_URL}/financial/receivables`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || "Falha ao criar título a receber")
    }
    return await response.json()
  } catch (err) {
    console.error("Failed to create receivable invoice:", err)
    throw err
  }
}

export async function settleReceivableInstallment(
  installmentId: string,
  payload: SettleReceivableInstallmentPayload
): Promise<any> {
  try {
    const response = await fetch(`${API_URL}/financial/receivables/installments/${installmentId}/settle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || "Falha ao liquidar recebível")
    }
    return await response.json()
  } catch (err) {
    console.error("Failed to settle receivable installment:", err)
    throw err
  }
}

export async function cancelReceivableInvoice(invoiceId: string, reason?: string): Promise<boolean> {
  try {
    let url = `${API_URL}/financial/receivables/${invoiceId}`
    if (reason) url += `?reason=${encodeURIComponent(reason)}`
    const response = await fetch(url, {
      method: "DELETE",
      credentials: "include",
    })
    return response.ok
  } catch (err) {
    console.error("Failed to cancel receivable invoice:", err)
    return false
  }
}

export async function createPaymentAcquirer(payload: CreateAcquirerPayload): Promise<PaymentAcquirer | null> {
  try {
    const response = await fetch(`${API_URL}/financial/acquirers`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to create acquirer:", err)
    return null
  }
}

export async function fetchPaymentAcquirersClient(): Promise<PaymentAcquirer[]> {
  try {
    const response = await fetch(`${API_URL}/financial/acquirers`, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function fetchReceivableInvoicesClient(status?: string, channel?: string): Promise<ReceivableInvoice[]> {
  try {
    const params = new URLSearchParams()
    if (status) params.append("status", status)
    if (channel) params.append("channel", channel)
    const url = `${API_URL}/financial/receivables${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

// --- Phase 3: Cash Flow, DRE & Bank Statement Client Methods ---

import {
  CashFlowProjection,
  FinancialDREResponse,
  BankStatementTransaction,
  UploadOFXPayload,
  ReconcileBankTransactionPayload
} from "@/types/financial"

export async function fetchCashFlowClient(startDate?: string, endDate?: string): Promise<CashFlowProjection | null> {
  try {
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    const url = `${API_URL}/financial/cash-flow${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchFinancialDREClient(startDate?: string, endDate?: string, viewType?: string): Promise<FinancialDREResponse | null> {
  try {
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    if (viewType) params.append("view_type", viewType)
    const url = `${API_URL}/financial/dre${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

export async function fetchBankStatementsClient(bankAccountId?: string, isReconciled?: boolean): Promise<BankStatementTransaction[]> {
  try {
    const params = new URLSearchParams()
    if (bankAccountId) params.append("bank_account_id", bankAccountId)
    if (isReconciled !== undefined) params.append("is_reconciled", String(isReconciled))
    const url = `${API_URL}/financial/bank-statements${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    return []
  }
}

export async function uploadBankStatementOFX(payload: UploadOFXPayload): Promise<{ imported_count: number; skipped_count: number } | null> {
  try {
    const response = await fetch(`${API_URL}/financial/bank-statements/upload`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || "Falha ao importar arquivo OFX")
    }
    return await response.json()
  } catch (err) {
    console.error("Failed to upload OFX:", err)
    throw err
  }
}

export async function reconcileBankStatementTransaction(txId: string, payload: ReconcileBankTransactionPayload): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/financial/bank-statements/${txId}/reconcile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    return response.ok
  } catch (err) {
    console.error("Failed to reconcile bank transaction:", err)
    return false
  }
}

// --- Menu & Menu Engineering Client Functions ---

export async function fetchMenuCategoriesClient(): Promise<MenuCategory[]> {
  try {
    const response = await fetch(`${API_URL}/menu/categories`, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch menu categories:", err)
    return []
  }
}

export async function createMenuCategoryClient(payload: Partial<MenuCategory>): Promise<MenuCategory | null> {
  try {
    const response = await fetch(`${API_URL}/menu/categories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || "Falha ao criar categoria")
    }
    return await response.json()
  } catch (err) {
    console.error("Failed to create menu category:", err)
    throw err
  }
}

export async function fetchMenuItemsClient(categoryId?: string, isActive?: boolean): Promise<MenuItem[]> {
  try {
    const params = new URLSearchParams()
    if (categoryId) params.append("category_id", categoryId)
    if (isActive !== undefined) params.append("is_active", String(isActive))
    const url = `${API_URL}/menu/items${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch menu items:", err)
    return []
  }
}

export async function createMenuItemClient(payload: Partial<MenuItem>): Promise<MenuItem | null> {
  try {
    const response = await fetch(`${API_URL}/menu/items`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || "Falha ao criar item de cardápio")
    }
    return await response.json()
  } catch (err) {
    console.error("Failed to create menu item:", err)
    throw err
  }
}

export async function updateMenuItemClient(itemId: string, payload: Partial<MenuItem>): Promise<MenuItem | null> {
  try {
    const response = await fetch(`${API_URL}/menu/items/${itemId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || "Falha ao atualizar item")
    }
    return await response.json()
  } catch (err) {
    console.error("Failed to update menu item:", err)
    throw err
  }
}

export async function deleteMenuItemClient(itemId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/menu/items/${itemId}`, {
      method: "DELETE",
      credentials: "include",
    })
    return response.ok
  } catch (err) {
    console.error("Failed to delete menu item:", err)
    return false
  }
}

export async function fetchMenuEngineeringClient(startDate?: string, endDate?: string, categoryId?: string): Promise<MenuEngineeringResponse | null> {
  try {
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    if (categoryId) params.append("category_id", categoryId)
    const url = `${API_URL}/menu/engineering${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch menu engineering:", err)
    return null
  }
}

export async function simulateItemPricingClient(itemId: string, payload: SimulatePricingPayload): Promise<SimulatePricingResponse | null> {
  try {
    const response = await fetch(`${API_URL}/menu/items/${itemId}/simulate-pricing`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || "Falha ao simular precificação")
    }
    return await response.json()
  } catch (err) {
    console.error("Failed to simulate pricing:", err)
    throw err
  }
}

import { DiningTable, Order, KDSItem, DeliveryKanban } from "@/types/orders"

// --- Tables ---
export async function fetchDiningTablesClient(section?: string, status?: string): Promise<DiningTable[]> {
  try {
    const params = new URLSearchParams()
    if (section) params.append("section", section)
    if (status) params.append("status", status)
    const url = `${API_URL}/orders/tables${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", credentials: "include" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch dining tables:", err)
    return []
  }
}

export async function createDiningTableClient(payload: { table_number: string; capacity?: number; section?: string; status?: string }): Promise<DiningTable> {
  const response = await fetch(`${API_URL}/orders/tables`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao criar mesa")
  }
  return await response.json()
}

export async function updateDiningTableStatusClient(tableId: string, status: string): Promise<DiningTable> {
  const response = await fetch(`${API_URL}/orders/tables/${tableId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ status }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao atualizar status da mesa")
  }
  return await response.json()
}

// --- Orders ---
export async function fetchOrdersClient(channel?: string, status?: string, isPaid?: boolean): Promise<Order[]> {
  try {
    const params = new URLSearchParams()
    if (channel) params.append("channel", channel)
    if (status) params.append("status", status)
    if (isPaid !== undefined) params.append("is_paid", String(isPaid))
    const url = `${API_URL}/orders${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", credentials: "include" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch orders:", err)
    return []
  }
}

export async function fetchOrderDetailClient(orderId: string): Promise<Order | null> {
  try {
    const response = await fetch(`${API_URL}/orders/${orderId}`, { method: "GET", credentials: "include" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch order detail:", err)
    return null
  }
}

export async function createOrderClient(payload: any): Promise<Order> {
  const response = await fetch(`${API_URL}/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao criar comanda / pedido")
  }
  return await response.json()
}

export async function addItemsToOrderClient(orderId: string, items: any[]): Promise<Order> {
  const response = await fetch(`${API_URL}/orders/${orderId}/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ items }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao adicionar itens na comanda")
  }
  return await response.json()
}

export async function closeAndPayOrderClient(orderId: string, payload: { payment_method: string; acquirer_id?: string; bank_account_id?: string }): Promise<Order> {
  const response = await fetch(`${API_URL}/orders/${orderId}/close-and-pay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao fechar e liquidar comanda")
  }
  return await response.json()
}

// --- KDS ---
export async function fetchKDSQueueClient(station?: string): Promise<KDSItem[]> {
  try {
    const params = new URLSearchParams()
    if (station) params.append("station", station)
    const url = `${API_URL}/orders/kds/queue${params.toString() ? `?${params.toString()}` : ""}`
    const response = await fetch(url, { method: "GET", credentials: "include" })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch KDS queue:", err)
    return []
  }
}

export async function updateKDSItemStatusClient(itemId: string, status: string): Promise<any> {
  const response = await fetch(`${API_URL}/orders/items/${itemId}/kds-status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ status }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao atualizar status no KDS")
  }
  return await response.json()
}

// --- Delivery ---
export async function fetchDeliveryKanbanClient(): Promise<DeliveryKanban | null> {
  try {
    const response = await fetch(`${API_URL}/orders/delivery/kanban`, { method: "GET", credentials: "include" })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Failed to fetch delivery kanban:", err)
    return null
  }
}

export async function updateDeliveryStatusClient(orderId: string, status: string): Promise<Order> {
  const response = await fetch(`${API_URL}/orders/${orderId}/delivery-status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ status }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao atualizar status do delivery")
  }
  return await response.json()
}

// --- Production Orders ---
export async function createProductionOrderClient(payload: any): Promise<any> {
  const response = await fetch(`${API_URL}/production/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao criar Ordem de Produção")
  }
  return await response.json()
}

export async function startProductionOrderClient(orderId: string): Promise<any> {
  const response = await fetch(`${API_URL}/production/orders/${orderId}/start`, {
    method: "POST",
    credentials: "include",
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao iniciar produção")
  }
  return await response.json()
}

export async function completeProductionOrderClient(orderId: string, payload: any): Promise<any> {
  const response = await fetch(`${API_URL}/production/orders/${orderId}/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao concluir produção")
  }
  return await response.json()
}

// --- Stock Transfers ---
export async function createStockTransferClient(payload: any): Promise<any> {
  const response = await fetch(`${API_URL}/inventory/transfers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao criar transferência de estoque")
  }
  return await response.json()
}

export async function dispatchStockTransferClient(transferId: string): Promise<any> {
  const response = await fetch(`${API_URL}/inventory/transfers/${transferId}/dispatch`, {
    method: "POST",
    credentials: "include",
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao despachar transferência")
  }
  return await response.json()
}

export async function receiveStockTransferClient(transferId: string, payload?: any): Promise<any> {
  const response = await fetch(`${API_URL}/inventory/transfers/${transferId}/receive`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload || {}),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao receber transferência")
  }
  return await response.json()
}

// --- RFQ / B2B Cotações ---
export async function fetchRFQs(statusFilter?: string): Promise<any[]> {
  try {
    const url = statusFilter 
      ? `${API_URL}/purchasing/rfqs?status_filter=${statusFilter}` 
      : `${API_URL}/purchasing/rfqs`
    const response = await fetch(url, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return []
    return await response.json()
  } catch (err) {
    console.error("Erro ao buscar RFQs:", err)
    return []
  }
}

export async function fetchRFQDetails(rfqId: string): Promise<any | null> {
  try {
    const response = await fetch(`${API_URL}/purchasing/rfqs/${rfqId}`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Erro ao buscar detalhes da RFQ:", err)
    return null
  }
}

export async function createRFQClient(payload: any): Promise<any> {
  const response = await fetch(`${API_URL}/purchasing/rfqs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao criar cotação")
  }
  return await response.json()
}

export async function addRFQSuppliersClient(rfqId: string, supplierIds: string[]): Promise<any> {
  const response = await fetch(`${API_URL}/purchasing/rfqs/${rfqId}/suppliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ supplier_ids: supplierIds }),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao convidar fornecedores")
  }
  return await response.json()
}

export async function submitRFQProposalClient(rfqId: string, payload: any): Promise<any> {
  const response = await fetch(`${API_URL}/purchasing/rfqs/${rfqId}/proposals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao enviar proposta")
  }
  return await response.json()
}

export async function fetchRFQComparisonClient(rfqId: string): Promise<any | null> {
  try {
    const response = await fetch(`${API_URL}/purchasing/rfqs/${rfqId}/comparison`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!response.ok) return null
    return await response.json()
  } catch (err) {
    console.error("Erro ao carregar quadro comparativo:", err)
    return null
  }
}

export async function awardRFQClient(rfqId: string, payload: any): Promise<any> {
  const response = await fetch(`${API_URL}/purchasing/rfqs/${rfqId}/award`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao homologar cotação")
  }
  return await response.json()
}

// --- Team & Labor (Phase 8) ---
export async function fetchEmployeesClient(department?: string): Promise<any[]> {
  try {
    const url = department ? `${API_URL}/team/employees?department=${department}` : `${API_URL}/team/employees`
    const res = await fetch(url, { method: "GET", credentials: "include", cache: "no-store" })
    if (!res.ok) return []
    return await res.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function createEmployeeClient(payload: any): Promise<any> {
  const res = await fetch(`${API_URL}/team/employees`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao cadastrar colaborador")
  }
  return await res.json()
}

export async function updateEmployeeClient(employeeId: string, payload: any): Promise<any> {
  const res = await fetch(`${API_URL}/team/employees/${employeeId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao atualizar colaborador")
  }
  return await res.json()
}

export async function fetchShiftsClient(startDate?: string, endDate?: string): Promise<any[]> {
  try {
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    const res = await fetch(`${API_URL}/team/shifts?${params.toString()}`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!res.ok) return []
    return await res.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function createShiftClient(payload: any): Promise<any> {
  const res = await fetch(`${API_URL}/team/shifts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao agendar turno")
  }
  return await res.json()
}

export async function clockInClient(payload: any): Promise<any> {
  const res = await fetch(`${API_URL}/team/time-clock/in`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao registrar entrada de ponto")
  }
  return await res.json()
}

export async function clockOutClient(payload: any): Promise<any> {
  const res = await fetch(`${API_URL}/team/time-clock/out`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao registrar saída de ponto")
  }
  return await res.json()
}

export async function fetchTimeClockClient(): Promise<any[]> {
  try {
    const res = await fetch(`${API_URL}/team/time-clock`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!res.ok) return []
    return await res.json()
  } catch (err) {
    console.error(err)
    return []
  }
}

export async function calculateTipsClient(payload: any): Promise<any> {
  const res = await fetch(`${API_URL}/team/tips/calculate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao calcular rateio de gorjetas")
  }
  return await res.json()
}

export async function fetchPrimeCostClient(startDate?: string, endDate?: string): Promise<any | null> {
  try {
    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)
    const res = await fetch(`${API_URL}/team/prime-cost?${params.toString()}`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!res.ok) return null
    return await res.json()
  } catch (err) {
    console.error(err)
    return null
  }
}

// --- FoodOps Copilot & Predictive AI (Phase 9) ---
export async function sendCopilotMessageClient(prompt: string, conversationId?: string): Promise<any> {
  const res = await fetch(`${API_URL}/copilot/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ prompt, conversation_id: conversationId || null }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao comunicar com o FoodOps Copilot")
  }
  return await res.json()
}

export async function fetchCopilotAuditClient(): Promise<any | null> {
  try {
    const res = await fetch(`${API_URL}/copilot/audit`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!res.ok) return null
    return await res.json()
  } catch (err) {
    console.error("Erro ao carregar auditoria do Copilot:", err)
    return null
  }
}

export async function fetchTodayBriefingClient(): Promise<any | null> {
  try {
    const res = await fetch(`${API_URL}/copilot/briefings/today`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!res.ok) return null
    return await res.json()
  } catch (err) {
    console.error("Erro ao carregar briefing executivo:", err)
    return null
  }
}

export async function dispatchBriefingClient(channel: string = "WHATSAPP", destination?: string): Promise<any> {
  const res = await fetch(`${API_URL}/copilot/briefings/dispatch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ channel, destination }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Falha ao despachar briefing")
  }
  return await res.json()
}

export async function fetchCopilotConversationsClient(): Promise<any[]> {
  try {
    const res = await fetch(`${API_URL}/copilot/conversations`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    })
    if (!res.ok) return []
    return await res.json()
  } catch (err) {
    console.error(err)
    return []
  }
}