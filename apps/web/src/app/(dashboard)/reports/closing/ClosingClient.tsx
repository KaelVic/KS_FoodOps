"use client"

import React, { useState } from "react"
import { ConsolidatedReport, LossesAnalysisReport, StockPositionItem } from "@/types/reports"
import { Location } from "@/types/master-data"
import { getExportInventoryCsvUrl, getExportSpedUrl } from "@/lib/api-client"

interface ClosingClientProps {
  initialReport: ConsolidatedReport | null
  initialLosses: LossesAnalysisReport | null
  initialStock: StockPositionItem[]
  locations: Location[]
}

export default function ClosingClient({
  initialReport,
  initialLosses,
  initialStock,
  locations
}: ClosingClientProps) {
  const [selectedLocation, setSelectedLocation] = useState(locations.length > 0 ? locations[0].id : "")
  const [downloading, setDownloading] = useState<string | null>(null)

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val || 0)
  }

  const formatQty = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 3 }).format(val || 0)
  }

  const handleExport = async (type: "csv" | "sped") => {
    setDownloading(type)
    try {
      const endpoint = type === "csv" 
        ? getExportInventoryCsvUrl(selectedLocation)
        : getExportSpedUrl()
      
      const res = await fetch(endpoint, {
        method: "GET",
        credentials: "include",
      })
      
      if (!res.ok) throw new Error("Erro ao gerar exportação")
      
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = type === "csv" ? `inventario_${new Date().toISOString().slice(0,10)}.csv` : `sped_bloco_h_${new Date().toISOString().slice(0,10)}.txt`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (e) {
      alert("Falha ao baixar arquivo. Verifique a conexão com o servidor.")
    } finally {
      setDownloading(null)
    }
  }

  const report = initialReport || {
    total_revenue: 0,
    actual_cmv: 0,
    theoretical_consumption: 0,
    registered_losses: 0,
    unexplained_variance: 0,
    cmv_percentage: 0
  }

  const losses = initialLosses || {
    total_losses_value: 0,
    by_reason: [],
    items: []
  }

  const totalStockValue = initialStock.reduce((acc, item) => acc + Number(item.total_value || 0), 0)

  return (
    <div className="space-y-8 p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-white/10 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight text-white">Fechamento & Relatórios Contábeis</h1>
            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
              Pilar C • Contabilidade
            </span>
          </div>
          <p className="text-sm text-zinc-400 mt-1">
            DRE Operacional, Análise de CMV (Real vs Teórico), Perdas e Exportação para Fiscal/SPED.
          </p>
        </div>

        {/* Quick Export Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleExport("csv")}
            disabled={downloading !== null}
            className="flex items-center gap-2 rounded-xl bg-white/10 hover:bg-white/15 px-4 py-2.5 text-sm font-medium text-white border border-white/10 transition-all shadow-sm active:scale-95 disabled:opacity-50"
          >
            <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {downloading === "csv" ? "Exportando..." : "Exportar Inventário (CSV)"}
          </button>

          <button
            onClick={() => handleExport("sped")}
            disabled={downloading !== null}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2.5 text-sm font-medium text-white transition-all shadow-md shadow-indigo-600/20 active:scale-95 disabled:opacity-50"
          >
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {downloading === "sped" ? "Gerando..." : "SPED Bloco H (.txt)"}
          </button>
        </div>
      </div>

      {/* DRE Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Faturamento */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Faturamento (Vendas)</span>
            <span className="p-2 rounded-lg bg-blue-500/10 text-blue-400">💰</span>
          </div>
          <div className="mt-4">
            <span className="text-2xl font-bold text-white tracking-tight">{formatCurrency(report.total_revenue)}</span>
            <p className="text-xs text-zinc-500 mt-1">Receita bruta do período</p>
          </div>
        </div>

        {/* Card 2: CMV Real */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">CMV Real</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              Number(report.cmv_percentage) > 35 ? "bg-red-500/20 text-red-400" : "bg-emerald-500/20 text-emerald-400"
            }`}>
              {report.cmv_percentage}%
            </span>
          </div>
          <div className="mt-4">
            <span className="text-2xl font-bold text-white tracking-tight">{formatCurrency(report.actual_cmv)}</span>
            <p className="text-xs text-zinc-500 mt-1">EI + Compras - EF</p>
          </div>
        </div>

        {/* Card 3: CMV Teórico */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">CMV Teórico</span>
            <span className="p-2 rounded-lg bg-purple-500/10 text-purple-400">📋</span>
          </div>
          <div className="mt-4">
            <span className="text-2xl font-bold text-zinc-200 tracking-tight">{formatCurrency(report.theoretical_consumption)}</span>
            <p className="text-xs text-zinc-500 mt-1">Consumo via Ficha Técnica</p>
          </div>
        </div>

        {/* Card 4: Perdas */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Perdas Registradas</span>
            <span className="p-2 rounded-lg bg-amber-500/10 text-amber-400">⚠️</span>
          </div>
          <div className="mt-4">
            <span className="text-2xl font-bold text-amber-400 tracking-tight">{formatCurrency(report.registered_losses)}</span>
            <p className="text-xs text-zinc-500 mt-1">Validade & Desperdício</p>
          </div>
        </div>

        {/* Card 5: Divergência */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Divergência Oculta</span>
            <span className="p-2 rounded-lg bg-rose-500/10 text-rose-400">🔍</span>
          </div>
          <div className="mt-4">
            <span className={`text-2xl font-bold tracking-tight ${
              Number(report.unexplained_variance) > 0 ? "text-rose-400" : "text-emerald-400"
            }`}>
              {formatCurrency(report.unexplained_variance)}
            </span>
            <p className="text-xs text-zinc-500 mt-1">Desvio não explicado</p>
          </div>
        </div>
      </div>

      {/* Sections Grid: Losses Analysis & Stock Valuation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Losses Breakdown */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <h2 className="text-lg font-semibold text-white">Análise de Perdas por Motivo</h2>
            <span className="text-xs font-medium text-zinc-400">{losses.by_reason.length} categorias</span>
          </div>

          <div className="space-y-4">
            {losses.by_reason.length === 0 ? (
              <p className="text-sm text-zinc-500 text-center py-6">Nenhuma perda registrada no período.</p>
            ) : (
              losses.by_reason.map((r, idx) => {
                const pct = losses.total_losses_value > 0 ? (r.total_value / losses.total_losses_value) * 100 : 0
                return (
                  <div key={idx} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-zinc-200">{r.reason}</span>
                      <span className="text-zinc-400 font-mono">{formatCurrency(r.total_value)} ({pct.toFixed(1)}%)</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
                      <div 
                        className="h-full rounded-full bg-amber-500" 
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Right Column: Inventory Position & Valuation */}
        <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl space-y-6">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Posição de Estoque Valorizada</h2>
              <p className="text-xs text-zinc-400">Total em Ativo Circulante: <strong className="text-emerald-400">{formatCurrency(totalStockValue)}</strong></p>
            </div>
            <span className="text-xs text-zinc-400 font-mono">{initialStock.length} itens</span>
          </div>

          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-white/10 text-xs uppercase text-zinc-400 sticky top-0 bg-zinc-900/90 backdrop-blur-sm">
                <tr>
                  <th className="px-4 py-3">Insumo</th>
                  <th className="px-4 py-3">Categoria</th>
                  <th className="px-4 py-3 text-right">Qtd</th>
                  <th className="px-4 py-3 text-right">Custo Médio</th>
                  <th className="px-4 py-3 text-right">Valor Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {initialStock.map((it) => (
                  <tr key={it.sku_id} className="hover:bg-white/5 transition-colors">
                    <td className="px-4 py-3 font-medium text-zinc-100">{it.sku_name}</td>
                    <td className="px-4 py-3 text-zinc-400 text-xs">{it.category_name}</td>
                    <td className="px-4 py-3 text-right font-mono text-zinc-300">
                      {formatQty(it.total_quantity)} {it.uom_symbol}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-zinc-400">
                      {formatCurrency(it.unit_cost)}
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-medium text-emerald-400">
                      {formatCurrency(it.total_value)}
                    </td>
                  </tr>
                ))}
                {initialStock.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-zinc-500">
                      Nenhum saldo de estoque registrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
