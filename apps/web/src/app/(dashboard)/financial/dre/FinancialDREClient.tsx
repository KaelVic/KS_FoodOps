"use client"

import React, { useState } from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import {
  FileSpreadsheet,
  TrendingUp,
  Percent,
  ChefHat,
  Users,
  Flame,
  Layers,
  ArrowRight,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  Sparkles,
  PieChart
} from "lucide-react"
import {
  FinancialDREResponse
} from "@/types/financial"
import {
  fetchFinancialDREClient
} from "@/lib/api-client"

interface FinancialDREClientProps {
  initialDRE: FinancialDREResponse | null
}

export default function FinancialDREClient({
  initialDRE
}: FinancialDREClientProps) {
  const [dre, setDRE] = useState<FinancialDREResponse | null>(initialDRE)
  const [viewType, setViewType] = useState<"COMPETENCE" | "CASH">("COMPETENCE")
  const [startDate, setStartDate] = useState<string>(() => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split("T")[0]
  })
  const [endDate, setEndDate] = useState<string>(() => {
    const now = new Date()
    return new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split("T")[0]
  })
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const handleFilter = async (customViewType?: "COMPETENCE" | "CASH") => {
    const vType = customViewType || viewType
    setIsLoading(true)
    try {
      const data = await fetchFinancialDREClient(
        new Date(startDate).toISOString(),
        new Date(endDate).toISOString(),
        vType
      )
      setDRE(data)
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleViewTypeChange = (newView: "COMPETENCE" | "CASH") => {
    setViewType(newView)
    handleFilter(newView)
  }

  const handleQuickPeriod = (monthsAgo: number) => {
    const now = new Date()
    const targetMonth = now.getMonth() - monthsAgo
    const start = new Date(now.getFullYear(), targetMonth, 1)
    const end = new Date(now.getFullYear(), targetMonth + 1, 0)
    setStartDate(start.toISOString().split("T")[0])
    setEndDate(end.toISOString().split("T")[0])
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const kpis = dre?.kpis

  return (
    <div className="space-y-6">
      {/* Header & Regime Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <FileSpreadsheet className="h-7 w-7 text-violet-400" />
              DRE Financeira Gerencial
            </h1>
            <Badge variant="violet">Food-Service & EBITDA</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Demonstração do Resultado do Exercício com estrutura de CMV Real, Prime Cost e Margem EBITDA Operacional.
          </p>
        </div>

        {/* Competence vs Cash Toggle */}
        <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            onClick={() => handleViewTypeChange("COMPETENCE")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              viewType === "COMPETENCE"
                ? "bg-violet-500 text-white shadow-[0_0_12px_rgba(168,85,247,0.4)]"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Regime de Competência
          </button>
          <button
            onClick={() => handleViewTypeChange("CASH")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              viewType === "CASH"
                ? "bg-cyan-500 text-slate-950 shadow-[0_0_12px_rgba(6,182,212,0.4)]"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Regime de Caixa (Real)
          </button>
        </div>
      </div>

      {/* 4 Restaurant Executive KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Faturamento Líquido */}
        <GlassPanel accent="cyan" className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Receita Líquida</span>
            <TrendingUp className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {formatCurrency(kpis?.net_revenue || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Bruto: {formatCurrency(kpis?.gross_revenue || 0)}
            </p>
          </div>
        </GlassPanel>

        {/* KPI 2: CMV Real */}
        <GlassPanel accent={((kpis?.cmv_pct || 0) <= 32 ? "emerald" : (kpis?.cmv_pct || 0) <= 36 ? "amber" : "crimson")} className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <ChefHat className="h-3.5 w-3.5 text-emerald-400" /> CMV Real
            </span>
            <Badge variant={(kpis?.cmv_pct || 0) <= 32 ? "emerald" : (kpis?.cmv_pct || 0) <= 36 ? "amber" : "crimson"}>
              {(kpis?.cmv_pct || 0).toFixed(1)}% AV
            </Badge>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {formatCurrency(kpis?.cmv_amount || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {(kpis?.cmv_pct || 0) <= 32 ? "✓ Meta Saudável (≤ 32%)" : "⚠️ Acima do ideal para Food-Service"}
            </p>
          </div>
        </GlassPanel>

        {/* KPI 3: Prime Cost (CMV + Mão de Obra) */}
        <GlassPanel accent={(kpis?.prime_cost_pct || 0) <= 60 ? "emerald" : "amber"} className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Users className="h-3.5 w-3.5 text-violet-400" /> Prime Cost (CMV+Folha)
            </span>
            <Badge variant={(kpis?.prime_cost_pct || 0) <= 60 ? "emerald" : "amber"}>
              {(kpis?.prime_cost_pct || 0).toFixed(1)}% AV
            </Badge>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {formatCurrency(kpis?.prime_cost_amount || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {(kpis?.prime_cost_pct || 0) <= 60 ? "✓ Excelente controle operacional (≤ 60%)" : "Atenção com Folha + Insumos"}
            </p>
          </div>
        </GlassPanel>

        {/* KPI 4: EBITDA Operacional */}
        <GlassPanel accent={(kpis?.ebitda_amount || 0) >= 0 ? "violet" : "crimson"} className="p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">Margem EBITDA</span>
            <Badge variant={(kpis?.ebitda_amount || 0) >= 0 ? "violet" : "crimson"}>
              {(kpis?.ebitda_margin_pct || 0).toFixed(1)}%
            </Badge>
          </div>
          <div className="mt-3">
            <div className={`text-2xl font-bold tracking-tight ${
              (kpis?.ebitda_amount || 0) >= 0 ? "text-violet-300" : "text-rose-400"
            }`}>
              {formatCurrency(kpis?.ebitda_amount || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Geração de Caixa Operacional</p>
          </div>
        </GlassPanel>
      </div>

      {/* Date Filter Bar */}
      <GlassPanel className="p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-slate-400">De:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-violet-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-slate-400">Até:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-violet-500"
              />
            </div>

            <button
              onClick={() => handleFilter()}
              disabled={isLoading}
              className="bg-violet-500 hover:bg-violet-400 text-white px-4 py-1.5 rounded-xl text-xs font-bold transition-all shadow-[0_0_12px_rgba(168,85,247,0.3)]"
            >
              {isLoading ? "Calculando..." : "Atualizar DRE"}
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                handleQuickPeriod(0)
                handleFilter()
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
            >
              Mês Atual
            </button>
            <button
              type="button"
              onClick={() => {
                handleQuickPeriod(1)
                handleFilter()
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
            >
              Mês Anterior
            </button>
          </div>
        </div>
      </GlassPanel>

      {/* DRE Waterfall Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassPanel className="lg:col-span-2 overflow-hidden p-0">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <FileSpreadsheet className="h-4 w-4 text-violet-400" />
              Estrutura da DRE em Cascata
            </h2>
            <Badge variant="default">Análise Vertical (AV %)</Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/60 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-5">Conta / Agrupamento</th>
                  <th className="py-3.5 px-5 text-right">Valor (R$)</th>
                  <th className="py-3.5 px-5 text-right font-bold">% AV</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {dre?.lines?.map((line) => {
                  const isMainHeader = line.level === 1
                  return (
                    <tr
                      key={line.code}
                      className={`transition-colors ${
                        line.highlight === "cyan"
                          ? "bg-cyan-500/10 text-cyan-300 font-bold"
                          : line.highlight === "emerald"
                          ? "bg-emerald-500/10 text-emerald-300 font-bold"
                          : line.highlight === "violet"
                          ? "bg-violet-500/10 text-violet-300 font-bold"
                          : line.highlight === "crimson"
                          ? "bg-rose-500/10 text-rose-300 font-bold"
                          : isMainHeader
                          ? "bg-slate-900/40 text-white font-semibold"
                          : "hover:bg-slate-800/20 text-slate-400"
                      }`}
                    >
                      {/* Descrição */}
                      <td className={`py-3 px-5 ${!isMainHeader ? "pl-8 text-xs" : "text-sm"}`}>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs opacity-60">{line.code}</span>
                          <span>{line.name}</span>
                        </div>
                      </td>

                      {/* Valor */}
                      <td className={`py-3 px-5 text-right font-mono ${isMainHeader ? "font-bold text-sm" : "text-xs"}`}>
                        {formatCurrency(line.amount)}
                      </td>

                      {/* % Análise Vertical */}
                      <td className="py-3 px-5 text-right font-mono text-xs font-bold">
                        {line.av_pct.toFixed(1)}%
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </GlassPanel>

        {/* Expenses by Category Breakdown Card */}
        <GlassPanel className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <PieChart className="h-4 w-4 text-cyan-400" />
              Ranking de Despesas
            </h3>
            <span className="text-xs text-slate-400">Por Categoria</span>
          </div>

          <div className="space-y-3">
            {dre?.category_breakdown?.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                Nenhum lançamento no período selecionado.
              </div>
            ) : (
              dre?.category_breakdown?.map((cat) => (
                <div key={cat.name} className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">{cat.name}</span>
                    <span className="font-mono font-bold text-slate-300">{formatCurrency(cat.amount)}</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="uppercase text-[10px] tracking-wider text-slate-500">{cat.type.replace("EXPENSE_", "")}</span>
                    <span className="font-mono font-semibold text-amber-400">{cat.av_pct.toFixed(1)}% da receita</span>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-cyan-500 h-full rounded-full"
                      style={{ width: `${Math.min(cat.av_pct, 100)}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        </GlassPanel>
      </div>
    </div>
  )
}
