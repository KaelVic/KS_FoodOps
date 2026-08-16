import { fetchPurchaseOrderDetailServer } from "@/lib/api-server"
import { fetchCatalogSkusAndUomsServer } from "@/lib/api-server"
import { redirect } from "next/navigation"
import PODetailClient from "./PODetailClient"

export const dynamic = "force-dynamic"

export default async function PurchaseOrderDetailPage({
  params
}: {
  params: { id: string }
}) {
  const [poDetail, catalog] = await Promise.all([
    fetchPurchaseOrderDetailServer(params.id),
    fetchCatalogSkusAndUomsServer()
  ])

  if (!poDetail) {
    redirect("/purchase-orders")
  }

  return (
    <div className="h-full flex flex-col space-y-6">
      <PODetailClient initialDetail={poDetail} catalog={catalog} />
    </div>
  )
}
