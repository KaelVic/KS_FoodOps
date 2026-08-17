import { Metadata } from "next"
import { fetchCopilotAuditServer, fetchTodayBriefingServer } from "@/lib/api-server"
import { CopilotClient } from "./CopilotClient"

export const metadata: Metadata = {
  title: "FoodOps Copilot | KS FoodOps",
  description: "IA Agêntica & Automação Preditiva de Restaurante",
}

export const dynamic = "force-dynamic"

export default async function CopilotPage() {
  const [audit, briefing] = await Promise.all([
    fetchCopilotAuditServer(),
    fetchTodayBriefingServer()
  ])

  return (
    <div className="p-6 md:p-8">
      <CopilotClient initialAudit={audit} initialBriefing={briefing} />
    </div>
  )
}
