"use client"

import { useState } from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import {
  PackageSearch,
  Box,
  DollarSign,
  Activity,
  AlertTriangle,
  Warehouse,
  Package,
  TrendingUp,
  Scale,
  Sparkles,
  CheckCircle2,
  AlertCircle
} from "lucide-react"
import { InventoryBalance, TheoreticalBalance } from "@/types/inventory"

function formatCurrency(value: number | string): string {
  const num = typeof value === "string" ? parseFloat(value) : value
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num || 0)
}

function formatQuantity(value: number | string, uom: string): string {
  const num = typeof value === "string" ? parseFloat(value) : value
  return `${new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: num % 1 !== 0 ? 3 : 0,
    maximumFractionDigits: 3,
  }).format(num || 0)} ${uom}`
}

interface InventoryClientProps {
  initialBalances: InventoryBalance[]
  theoreticalBalances: TheoreticalBalance[]
}

export function InventoryClient({ initialBalances, theoreticalBalances }: InventoryClientProps) {
  const [activeTab, setActiveTab] = useState<"PHYSICAL" | "THEORETICAL">("PHYSICAL")

  const totalSkus = initialBalances.length
  const totalValue = initialBalances.reduce((sum, item) => sum + parseFloat(item.total_value || "0"), 0)

  const totalVarianceValue = theoreticalBalances.reduce((sum, item) => sum + (item.variance_value || 0), 0)
  const itemsWithDiscrepancy = theoreticalBalances.filter(item => Math.abs(item.variance_quantity) > 0.001).length

  const sortedBalances = [...initialBalances].sort((a, b) => 
    parseFloat(b.total_value || "0") - parseFloat(a.total_value || "0")
  )

  const sortedTheoretical = [...theoreticalBalances].sort((a, b) => 
    Math.abs(b.variance_value || 0) - Math.abs(a.variance_value || 0)
  )

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <PackageSearch className="h-8 w-8 text-[#00f0ff]" />
            Estoque & Inventário Perpétuo
          </h2>
          <p className="text-slate-400 mt-1">Radar de insumos, auditoria de estoque teórico e conciliação de CMV.</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/inventory-sessions"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-slate-950 
            bg-gradient-to-r from-[#00f0ff] to-[#a855f7] 
            hover:from-[#00d4e0] hover:to-[#9333ea] 
            active:scale-[0.98] transition-all duration-200 
            shadow-[0_4px_20px_rgba(0,240,255,0.3)] 
            border border-transparent whitespace-nowrap text-sm"
          >
            <PackageSearch className="h-4 w-4" />
            Nova Contagem
          </Link>
        </div>
      </div>

      {/* KPI Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassPanel accent="cyan" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <Box className="h-5 w-5 text-[#00f0ff]" />
            <span className="text-slate-400 text-sm font-medium">SKUs Ativos</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{totalSkus}</span>
            <span className="text-xs text-[#00f0ff] font-medium">no catálogo</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="violet" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="h-5 w-5 text-[#a855f7]" />
            <span className="text-slate-400 text-sm font-medium">Valor em Estoque Físico</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{formatCurrency(totalValue)}</span>
          </div>
        </GlassPanel>

        <GlassPanel accent={totalVarianceValue < 0 ? "crimson" : "emerald"} className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <Scale className={`h-5 w-5 ${totalVarianceValue < 0 ? "text-[#ff0055]" : "text-[#10b981]"}`} />
            <span className="text-slate-400 text-sm font-medium">Divergência Teórica Total</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-bold tabular-nums ${totalVarianceValue < 0 ? "text-[#ff0055]" : "text-[#10b981]"}`}>
              {formatCurrency(totalVarianceValue)}
            </span>
          </div>
        </GlassPanel>

        <GlassPanel accent="amber" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="h-5 w-5 text-[#f59e0b]" />
            <span className="text-slate-400 text-sm font-medium">SKUs com Desvio</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{itemsWithDiscrepancy}</span>
            <span className="text-xs text-[#f59e0b] font-medium">divergentes</span>
          </div>
        </GlassPanel>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/5 pb-2">
        <button
          onClick={() => setActiveTab("PHYSICAL")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "PHYSICAL"
              ? "bg-[#00f0ff]/10 text-[#00f0ff] border border-[#00f0ff]/30 shadow-[0_0_15px_rgba(0,240,255,0.15)]"
              : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
          }`}
        >
          Saldo Físico (Ledger)
        </button>
        <button
          onClick={() => setActiveTab("THEORETICAL")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
            activeTab === "THEORETICAL"
              ? "bg-[#a855f7]/10 text-[#a855f7] border border-[#a855f7]/30 shadow-[0_0_15px_rgba(168,85,247,0.15)]"
              : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
          }`}
        >
          <Sparkles className="h-4 w-4" />
          Estoque Teórico Perpétuo & Desvios
        </button>
      </div>

      {/* Tables */}
      {activeTab === "PHYSICAL" ? (
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
                      <Warehouse className="h-3.5 w-3.5" />
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
                    <td colSpan={6} className="px-5 py-12 text-center text-slate-500">
                      Nenhum item em estoque
                    </td>
                  </tr>
                ) : (
                  sortedBalances.map((item) => {
                    const quantity = parseFloat(item.quantity || "0")
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
        </GlassPanel>
      ) : (
        <GlassPanel accent="violet" className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]">
              <thead>
                <tr className="border-b border-white/5 bg-slate-950/50">
                  <th className="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Insumo (SKU)
                  </th>
                  <th className="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Categoria
                  </th>
                  <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Físico Real
                  </th>
                  <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Consumo Teórico
                  </th>
                  <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Saldo Teórico
                  </th>
                  <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Divergência (Qtd)
                  </th>
                  <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Divergência (R$)
                  </th>
                  <th className="px-5 py-3.5 text-center text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {sortedTheoretical.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-5 py-12 text-center text-slate-500">
                      Nenhum dado de estoque teórico disponível
                    </td>
                  </tr>
                ) : (
                  sortedTheoretical.map((item) => {
                    const isBalanced = item.status === "BALANCED"
                    const isExcess = item.status === "EXCESS"
                    const isShortage = item.status === "SHORTAGE"

                    return (
                      <tr key={item.sku_id} className="hover:bg-white/2.5 transition-colors">
                        <td className="px-5 py-4">
                          <p className="font-medium text-slate-100">{item.sku_name}</p>
                          <p className="text-xs text-slate-500 font-mono">{item.sku_id.slice(0, 8)}...</p>
                        </td>
                        <td className="px-5 py-4">
                          <span className="text-slate-300">{item.category_name}</span>
                        </td>
                        <td className="px-5 py-4 text-right font-mono tabular-nums text-slate-100">
                          {formatQuantity(item.actual_quantity, item.uom_symbol)}
                        </td>
                        <td className="px-5 py-4 text-right font-mono tabular-nums text-slate-400">
                          {formatQuantity(item.theoretical_consumption, item.uom_symbol)}
                        </td>
                        <td className="px-5 py-4 text-right font-mono tabular-nums text-[#00f0ff]">
                          {formatQuantity(item.theoretical_quantity, item.uom_symbol)}
                        </td>
                        <td className="px-5 py-4 text-right font-mono tabular-nums">
                          <span className={item.variance_quantity < 0 ? "text-[#ff0055]" : item.variance_quantity > 0 ? "text-[#10b981]" : "text-slate-300"}>
                            {item.variance_quantity > 0 ? `+${item.variance_quantity}` : item.variance_quantity} {item.uom_symbol}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-right font-mono tabular-nums font-semibold">
                          <span className={item.variance_value < 0 ? "text-[#ff0055]" : item.variance_value > 0 ? "text-[#10b981]" : "text-slate-300"}>
                            {formatCurrency(item.variance_value)}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-center">
                          {isBalanced ? (
                            <Badge variant="emerald" className="font-mono text-xs">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              OK
                            </Badge>
                          ) : isShortage ? (
                            <Badge variant="crimson" className="font-mono text-xs">
                              Falta
                            </Badge>
                          ) : (
                            <Badge variant="amber" className="font-mono text-xs">
                              Sobra
                            </Badge>
                          )}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </GlassPanel>
      )}
    </div>
  )
}
