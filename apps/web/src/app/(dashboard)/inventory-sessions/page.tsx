import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { ClipboardList, AlertTriangle, CheckCircle, Clock } from "lucide-react"
import { fetchInventorySessionsServer } from "@/lib/api-server"
import InventorySessionsClient from "./InventorySessionsClient"

export const dynamic = "force-dynamic"

export default async function InventorySessionsPage() {
  const sessions = await fetchInventorySessionsServer()

  const openSessionsCount = sessions.filter(s => s.status === "OPEN").length
  const closedSessionsCount = sessions.filter(s => s.status === "CLOSED").length

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <ClipboardList className="h-8 w-8 text-[#00f0ff]" />
            Inventário Físico & CMV
          </h2>
          <p className="text-slate-400 mt-1">
            Gestão de sessões de contagem física, variâncias e auditoria de estoque.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassPanel accent="cyan" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="h-5 w-5 text-[#00f0ff]" />
            <span className="text-slate-400 text-sm font-medium">Contagens em Andamento</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{openSessionsCount}</span>
            <span className="text-xs text-slate-500">Sessões "OPEN"</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="violet" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle className="h-5 w-5 text-[#a855f7]" />
            <span className="text-slate-400 text-sm font-medium">Inventários Fechados</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{closedSessionsCount}</span>
            <span className="text-xs text-slate-500">Histórico mantido</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="amber" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="h-5 w-5 text-[#f59e0b]" />
            <span className="text-slate-400 text-sm font-medium">CMV Operacional</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">--</span>
            <span className="text-xs text-slate-500">Cálculo no fechamento mensal</span>
          </div>
        </GlassPanel>
      </div>

      <InventorySessionsClient initialSessions={sessions} />
    </div>
  )
}
