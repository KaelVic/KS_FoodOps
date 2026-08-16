import { InventoryBalance, FetchInventoryBalancesParams } from "@/types/inventory"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? process.env.API_URL ?? "http://localhost:8000"

export async function apiClient(path: string, options: RequestInit = {}) {
  // Client-side version - relies on cookies being sent automatically
  const headers = new Headers(options.headers)
  
  if (options.body && typeof options.body === 'string' && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json")
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error(`API call failed: ${response.status} ${response.statusText}`)
  }

  return response
}

export async function fetchInventoryBalances(params: FetchInventoryBalancesParams = {}): Promise<InventoryBalance[]> {
  try {
    const searchParams = new URLSearchParams()
    if (params.location_id) {
      searchParams.set("location_id", params.location_id)
    }

    const response = await fetch(`${API_URL}/inventory/balances?${searchParams.toString()}`, {
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
    return data as InventoryBalance[]
  } catch (error) {
    console.error("Failed to fetch inventory balances:", error)
    return []
  }
}