"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { 
  TrendingUp, DollarSign, PieChart, AlertTriangle, 
  CheckCircle2, Sparkles, UtensilsCrossed, Users, 
  HelpCircle, ChevronRight, BarChart3 
} from "lucide-react"
import { TeamNavigation } from "../TeamClient"
import { fetchPrimeCostClient } from "@/lib/api-client"

interface PrimeCostClientProps {
  initialData: any | null
}

export function PrimeCostClient({ initialData }: PrimeCostClientProps) {
  const [data, setData] = React.useState<any | null>(initialData)
  const [startDate, setStartDate] = React.useState("")
  const [endDate, setEndDate] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(false)

  const handleFilter = async () => {
    setIsLoading(true)
    try {
      const res = await fetchPrimeCostClient(startDate || undefined, endDate || undefined)
      setData(res)
    } finally {
      setIsLoading(false)
    }
  }

  const getHealthBadge = (status: string) => {
    switch (status) {
      case "EXCELLENT":
        return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"><Sparkles className="w-3.5 h-3.5" /> Excelente (Alta Rentabilidade)</span>
      case "HEALTHY":
        return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-[#00f0ff]/10 text-[#00f0ff] border border-[#00f0ff]/30"><CheckCircle2 className="w-3.5 h-3.5" /> Saudável (Meta 55-65%)</span>
      case "WARNING":
        return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30"><AlertTriangle className="w-3.5 h-3.5" /> Atenção (Margem Apertada 65-68%)</span>
      case "CRITICAL":
        return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30"><AlertTriangle className="w-3.5 h-3.5" /> Crítico (&gt; 68% da Receita)</span>
      default:
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300">Indeterminado</span>
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono tracking-widest text-[#00f0ff] uppercase bg-[#00f0ff]/10 px-2 py-0.5 rounded border border-[#00f0ff]/20">
              PRIME COST CONSOLIDATION
            </span>
            <span className="text-[11px] font-mono tracking-widest text-purple-400 uppercase bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
              CMV REAL + CMO REAL
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-[#00f0ff]" />
            Prime Cost & Custo de Mão de Obra (CMO)
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            O indicador supremo de rentabilidade em Food-Service: soma do Custo de Mercadorias (CMV) + Custo de Pessoal (CMO) sobre a Receita Líquida.
          </p>
        </div>
      </div>

      <TeamNavigation />

      {/* Date Filter */}
      <div className="flex flex-wrap items-center gap-4 p-4 rounded-xl bg-slate-900/40 border border-slate-800/80">
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-400">Data Inicial:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#00f0ff]"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-400">Data Final:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#00f0ff]"
          />
        </div>
        <button
          onClick={handleFilter}
          disabled={isLoading}
          className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all"
        >
          {isLoading ? "Filtrando..." : "Aplicar Filtro"}
        </button>
      </div>

      {data && (
        <div className="space-y-6">
          {/* Main Prime Cost Hero Banner */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-slate-950 border border-[#00f0ff]/30 shadow-2xl relative overflow-hidden">
            <div className="absolute right-0 top-0 w-96 h-96 bg-[#00f0ff]/5 rounded-full blur-3xl pointer-events-none" />
            
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 relative z-10">
              <div>
                <span className="text-xs font-mono uppercase tracking-widest text-[#00f0ff]">
                  INDICADOR MESTRE DO RESTAURANTE
                </span>
                <h2 className="text-3xl md:text-4xl font-extrabold text-slate-100 mt-1 flex items-center gap-3">
                  Prime Cost Real: <span className="text-[#00f0ff]">{data.prime_cost_percentage}%</span>
                </h2>
                <div className="mt-3 flex items-center gap-2">
                  {getHealthBadge(data.health_status)}
                  <span className="text-xs text-slate-400">Meta Ideal Food-Service: 55% a 65%</span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1">
                <span className="text-[11px] font-mono text-slate-400">VALOR TOTAL CONSOLIDADO</span>
                <p className="text-2xl font-bold text-slate-100">
                  R$ {Number(data.prime_cost_amount).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </p>
                <span className="text-[10px] text-slate-500 font-mono">CMV (R$ {Number(data.food_cost_cmv).toFixed(2)}) + CMO (R$ {Number(data.total_labor_cost_cmo).toFixed(2)})</span>
              </div>
            </div>

            {/* Visual Bar Gauge */}
            <div className="mt-6 space-y-2">
              <div className="flex justify-between text-xs font-mono text-slate-400">
                <span>0%</span>
                <span className="text-emerald-400">55% (Excelente)</span>
                <span className="text-[#00f0ff]">65% (Meta)</span>
                <span className="text-rose-400">100%</span>
              </div>
              <div className="h-4 w-full bg-slate-950 rounded-full overflow-hidden flex border border-slate-800">
                <div
                  style={{ width: `${Math.min(100, Number(data.cmv_percentage))}%` }}
                  className="bg-amber-500 h-full relative group"
                  title={`CMV: ${data.cmv_percentage}%`}
                />
                <div
                  style={{ width: `${Math.min(100 - Number(data.cmv_percentage), Number(data.cmo_percentage))}%` }}
                  className="bg-blue-500 h-full relative group"
                  title={`CMO: ${data.cmo_percentage}%`}
                />
              </div>
              <div className="flex items-center gap-4 text-xs mt-2">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-3 h-3 rounded bg-amber-500" />
                  CMV / Insumos: <strong>{data.cmv_percentage}%</strong>
                </span>
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-3 h-3 rounded bg-blue-500" />
                  CMO / Pessoal: <strong>{data.cmo_percentage}%</strong>
                </span>
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="w-3 h-3 rounded bg-emerald-500" />
                  Margem Bruta Restante: <strong>{(100 - Number(data.prime_cost_percentage)).toFixed(2)}%</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Cards Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-emerald-400">RECEITA LÍQUIDA OPERACIONAL</span>
                <DollarSign className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-2xl font-bold text-slate-100 mt-2">
                R$ {Number(data.net_revenue).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">Base de cálculo dos percentuais da DRE</p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-amber-400">CMV REAL (FOOD COST)</span>
                <UtensilsCrossed className="w-4 h-4 text-amber-400" />
              </div>
              <p className="text-2xl font-bold text-amber-300 mt-2">
                R$ {Number(data.food_cost_cmv).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
              <p className="text-[11px] text-slate-400 mt-1 font-bold">
                {data.cmv_percentage}% da Receita Líquida
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-blue-400">CMO REAL (LABOR COST)</span>
                <Users className="w-4 h-4 text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-blue-300 mt-2">
                R$ {Number(data.total_labor_cost_cmo).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
              <p className="text-[11px] text-slate-400 mt-1 font-bold">
                {data.cmo_percentage}% da Receita Líquida (com 35% encargos)
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
