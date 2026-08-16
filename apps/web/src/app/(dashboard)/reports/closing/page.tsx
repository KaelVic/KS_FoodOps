import { Metadata } from "next"
import ClosingClient from "./ClosingClient"
import { 
  fetchConsolidatedReportServer, 
  fetchLossesReportServer, 
  fetchStockPositionServer,
  fetchLocationsServer 
} from "@/lib/api-server"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Fechamento Contábil & CMV | KS FoodOps",
  description: "DRE Operacional, Análise de CMV, Perdas e Exportações SPED/CSV",
}

export default async function ClosingPage() {
  const locations = await fetchLocationsServer()
  const defaultLocationId = locations.length > 0 ? locations[0].id : "00000000-0000-0000-0000-000000000000"

  const now = new Date()
  const startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString()
  const endDate = now.toISOString()

  const [report, losses, stock] = await Promise.all([
    fetchConsolidatedReportServer(defaultLocationId, startDate, endDate),
    fetchLossesReportServer(startDate, endDate),
    fetchStockPositionServer(defaultLocationId)
  ])

  return (
    <ClosingClient 
      initialReport={report}
      initialLosses={losses}
      initialStock={stock}
      locations={locations}
    />
  )
}
