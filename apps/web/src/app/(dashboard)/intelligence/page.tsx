import { Metadata } from "next"
import { IntelligenceClient } from "./IntelligenceClient"
import { 
  fetchPoliciesServer, 
  fetchSuggestionsServer, 
  fetchAlertsServer,
  fetchDishCMVDriftServer,
  fetchStockoutRisksServer 
} from "@/lib/api-server"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Inteligência Operacional & CMV | KS FoodOps",
  description: "Curva ABC, Sugestões de Compra, Desvio de CMV por Prato e Projeção de Ruptura",
}

export default async function IntelligencePage() {
  const [policies, suggestions, alerts, dishDrifts, stockoutRisks] = await Promise.all([
    fetchPoliciesServer(),
    fetchSuggestionsServer(),
    fetchAlertsServer(),
    fetchDishCMVDriftServer(),
    fetchStockoutRisksServer(),
  ])

  // Extract unique locations from policies
  const uniqueLocationsMap = new Map<string, string>()
  policies.forEach(p => {
    uniqueLocationsMap.set(p.location_id, p.location_name)
  })
  
  const uniqueLocations = Array.from(uniqueLocationsMap.entries()).map(([id, name]) => ({ id, name }))
  
  const defaultLocationId = uniqueLocations.length > 0 ? uniqueLocations[0].id : null

  return (
    <IntelligenceClient 
      initialPolicies={policies}
      initialSuggestions={suggestions}
      initialAlerts={alerts}
      initialDishDrifts={dishDrifts}
      initialStockoutRisks={stockoutRisks}
      locations={uniqueLocations}
      defaultLocationId={defaultLocationId}
    />
  )
}
