import { fetchPurchaseOrdersServer } from "@/lib/api-server"
import ReconciliationClient from "./ReconciliationClient"

export const dynamic = "force-dynamic"

export default async function ReconciliationPage() {
  const purchaseOrders = await fetchPurchaseOrdersServer()
  // Pega apenas POs que não estão em DRAFT para reconciliar (ex: SENT, PARTIAL_RECEIPT, FULLY_RECEIVED)
  const activePOs = purchaseOrders.filter(po => po.status !== "DRAFT")

  return <ReconciliationClient activePOs={activePOs} />
}
