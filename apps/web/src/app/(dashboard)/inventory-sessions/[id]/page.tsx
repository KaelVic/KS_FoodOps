import { fetchInventorySessionDetailServer, fetchInventorySessionsServer } from "@/lib/api-server"
import { fetchCatalogSkusAndUomsServer } from "@/lib/api-server"
import { redirect } from "next/navigation"
import SessionDetailClient from "./SessionDetailClient"

export const dynamic = "force-dynamic"

export default async function InventorySessionDetailPage({
  params
}: {
  params: { id: string }
}) {
  const [sessionDetail, catalog] = await Promise.all([
    fetchInventorySessionDetailServer(params.id),
    fetchCatalogSkusAndUomsServer()
  ])

  if (!sessionDetail) {
    redirect("/inventory-sessions")
  }

  return (
    <div className="h-full flex flex-col space-y-6">
      <SessionDetailClient initialDetail={sessionDetail} catalog={catalog} />
    </div>
  )
}
