import { Metadata } from "next"
import { IntelligenceClient } from "./IntelligenceClient"
import { fetchPoliciesServer, fetchSuggestionsServer, fetchAlertsServer } from "@/lib/api-server"
import { fetchInventoryBalancesServer } from "@/lib/api-server"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Inteligência Operacional | KS FoodOps",
  description: "Curva ABC, Sugestões de Compra e Alertas",
}

export default async function IntelligencePage() {
  const [policies, suggestions, alerts] = await Promise.all([
    fetchPoliciesServer(),
    fetchSuggestionsServer(),
    fetchAlertsServer(),
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
      locations={uniqueLocations}
      defaultLocationId={defaultLocationId}
    />
  )
}
