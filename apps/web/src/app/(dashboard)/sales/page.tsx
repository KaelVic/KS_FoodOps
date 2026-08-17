import { GlassPanel } from "@/components/ui/glass-panel"
import { TrendingUp, Utensils, AlertTriangle, DollarSign, Layers } from "lucide-react"
import {
  fetchSalesImportsServer,
  fetchTheoreticalVsActualServer,
  fetchPOSMappingsServer,
  fetchRecipesServer,
  fetchLossesServer,
  fetchCatalogSkusAndUomsServer,
  fetchLocationsServer
} from "@/lib/api-server"
import SalesClient from "./SalesClient"

export const dynamic = "force-dynamic"

export default async function SalesPage() {
  const [salesImports, theoReport, mappings, recipes, losses, catalog, locations] = await Promise.all([
    fetchSalesImportsServer(),
    fetchTheoreticalVsActualServer(),
    fetchPOSMappingsServer(),
    fetchRecipesServer(),
    fetchLossesServer(),
    fetchCatalogSkusAndUomsServer(),
    fetchLocationsServer()
  ])

  const totalImports = salesImports.length
  const totalTheoreticalCost = theoReport.reduce((acc, item) => acc + (Number(item.theoretical_cost) || 0), 0)
  const totalLossesCount = losses.length

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-[#00f0ff]" />
            Vendas, Consumo Teórico & Desperdício
          </h2>
          <p className="text-slate-400 mt-1">
            Reconciliação automática de vendas do PDV com a Engenharia de Cardápio (Teórico vs Real e Perdas).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassPanel accent="cyan" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <Utensils className="h-5 w-5 text-[#00f0ff]" />
            <span className="text-slate-400 text-sm font-medium">Lotes de Venda Ingeridos</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{totalImports}</span>
            <span className="text-xs text-slate-500">Importações PDV</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="violet" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="h-5 w-5 text-[#a855f7]" />
            <span className="text-slate-400 text-sm font-medium">Custo Teórico Acumulado</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{formatCurrency(totalTheoreticalCost)}</span>
            <span className="text-xs text-slate-500">Base Ficha Técnica</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="amber" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="h-5 w-5 text-[#f59e0b]" />
            <span className="text-slate-400 text-sm font-medium">Perdas / Desperdícios Registrados</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{totalLossesCount}</span>
            <span className="text-xs text-slate-500">Lançamentos de quebra</span>
          </div>
        </GlassPanel>
      </div>

      <SalesClient
        initialImports={salesImports}
        initialTheoReport={theoReport}
        initialMappings={mappings}
        recipes={recipes}
        initialLosses={losses}
        catalog={catalog}
        locations={locations}
      />
    </div>
  )
}
