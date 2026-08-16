import { fetchInventoryBalances } from "@/lib/api"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"

export const dynamic = "force-dynamic"
import {
  PackageSearch,
  Box,
  DollarSign,
  Activity,
  AlertTriangle,
  Warehouse,
  Package,
  TrendingUp,
  ChevronDown,
  ChevronUp,
} from "lucide-react"

function formatCurrency(value: string): string {
  const num = parseFloat(value)
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
}

function formatQuantity(value: string, uom: string): string {
  const num = parseFloat(value)
  return `${new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: num % 1 !== 0 ? 3 : 0,
    maximumFractionDigits: 3,
  }).format(num)} ${uom}`
}

async function getInventoryData() {
  return await fetchInventoryBalances()
}

export default async function InventoryPage() {
  const balances = await getInventoryData()

  const totalSkus = balances.length
  const totalValue = balances.reduce((sum, item) => sum + parseFloat(item.total_value), 0)

  const sortedBalances = [...balances].sort((a, b) => 
    parseFloat(b.total_value) - parseFloat(a.total_value)
  )

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <PackageSearch className="h-8 w-8 text-[#00f0ff]" />
            Estoque & Inventário
          </h2>
          <p className="text-slate-400 mt-1">Radar de insumos, curva ABC e sessões de contagem física.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-slate-950 
          bg-gradient-to-r from-[#00f0ff] to-[#a855f7] 
          hover:from-[#00d4e0] hover:to-[#9333ea] 
          active:scale-[0.98] transition-all duration-200 
          shadow-[0_4px_20px_rgba(0,240,255,0.3)] 
          border border-transparent whitespace-nowrap">
          <PackageSearch className="h-4 w-4" />
          Nova Contagem
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassPanel accent="cyan" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <Box className="h-5 w-5 text-[#00f0ff]" />
            <span className="text-slate-400 text-sm font-medium">Total SKUs Ativos</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{totalSkus}</span>
            <TrendingUp className="h-4 w-4 text-[#10b981]" />
            <span className="text-xs text-[#10b981] font-medium">vs mês anterior</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="violet" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="h-5 w-5 text-[#a855f7]" />
            <span className="text-slate-400 text-sm font-medium">Valor Financeiro em Estoque</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{formatCurrency(totalValue.toString())}</span>
            <TrendingUp className="h-4 w-4 text-[#a855f7]" />
            <span className="text-xs text-[#a855f7] font-medium">total acumulado</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="emerald" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <Activity className="h-5 w-5 text-[#10b981]" />
            <span className="text-slate-400 text-sm font-medium">Status do Radar</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold text-[#10b981] text-glow-cyan flex items-center gap-1">
              <span className="relative">
                Normal
                <span className="absolute inset-0 bg-[#10b981] animate-pulse opacity-30 rounded" />
              </span>
            </span>
            <span className="text-xs text-slate-500">sistema operacional</span>
          </div>
        </GlassPanel>
      </div>

      <GlassPanel accent="cyan" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[800px]">
            <thead>
              <tr className="border-b border-white/5 bg-slate-950/50">
                <th className="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span className="flex items-center gap-2">
                    <Package className="h-3.5 w-3.5" />
                    Produto (SKU)
                  </span>
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span className="flex items-center gap-2">
                    <Warehouse className="h-3.5 w-3.5" />
                    Categoria
                  </span>
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span className="flex items-center gap-2">
                    <PackageSearch className="h-3.5 w-3.5" />
                    Local
                  </span>
                </th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span className="flex items-center gap-2 justify-end">
                    <Activity className="h-3.5 w-3.5" />
                    Qtd Atual
                  </span>
                </th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span className="flex items-center gap-2 justify-end">
                    <DollarSign className="h-3.5 w-3.5" />
                    Custo Médio
                  </span>
                </th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span className="flex items-center gap-2 justify-end">
                    <TrendingUp className="h-3.5 w-3.5" />
                    Valor Total
                  </span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {sortedBalances.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center">
                    <div className="flex flex-col items-center gap-3 text-slate-500">
                      <PackageSearch className="h-12 w-12 opacity-30" />
                      <p className="text-lg">Nenhum item em estoque</p>
                      <p className="text-sm">Os saldos aparecerão aqui quando houver movimentações</p>
                    </div>
                  </td>
                </tr>
              ) : (
                sortedBalances.map((item) => {
                  const quantity = parseFloat(item.quantity)
                  const isLowStock = quantity > 0 && quantity < 5
                  const isOutOfStock = quantity <= 0

                  return (
                    <tr key={item.sku_id} className="hover:bg-white/2.5 transition-colors">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-lg bg-slate-800/50 flex items-center justify-center border border-white/5">
                            <Package className="h-5 w-5 text-slate-400" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-100">{item.sku_name}</p>
                            <p className="text-xs text-slate-500 font-mono">{item.sku_id.slice(0, 8)}...</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-slate-300">{item.category_name || "Sem categoria"}</span>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-slate-300 flex items-center gap-1">
                          <Warehouse className="h-3 w-3 text-slate-500" />
                          {item.location_name}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isOutOfStock ? (
                            <Badge variant="crimson" className="font-mono">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              Esgotado
                            </Badge>
                          ) : isLowStock ? (
                            <Badge variant="amber" className="font-mono">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              {formatQuantity(item.quantity, item.base_uom)}
                            </Badge>
                          ) : (
                            <span className="font-mono tabular-nums text-slate-100 whitespace-nowrap">
                              {formatQuantity(item.quantity, item.base_uom)}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <span className="font-mono tabular-nums text-slate-300 whitespace-nowrap">
                          {formatCurrency(item.unit_cost)}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-right">
                        <span className="font-mono tabular-nums text-slate-100 font-medium whitespace-nowrap">
                          {formatCurrency(item.total_value)}
                        </span>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
        {sortedBalances.length > 0 && (
          <div className="px-5 py-3 border-t border-white/5 bg-slate-950/30">
            <p className="text-xs text-slate-500 text-right">
              Exibindo {sortedBalances.length} SKU{sortedBalances.length !== 1 ? "s" : ""} &middot; Ordenado por maior valor financeiro
            </p>
          </div>
        )}
      </GlassPanel>
    </div>
  )
}