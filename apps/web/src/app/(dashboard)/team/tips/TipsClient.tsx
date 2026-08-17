"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { 
  DollarSign, Calculator, Sparkles, CheckCircle2, AlertCircle, 
  Users, Percent, ShieldCheck, Scale, FileText, Download 
} from "lucide-react"
import { TeamNavigation } from "../TeamClient"
import { calculateTipsClient } from "@/lib/api-client"

export function TipsClient() {
  const router = useRouter()
  const [referencePeriod, setReferencePeriod] = React.useState("2026-08")
  const [totalCollected, setTotalCollected] = React.useState("8500.00")
  const [retentionPercentage, setRetentionPercentage] = React.useState("10.00")
  
  const [isCalculating, setIsCalculating] = React.useState(false)
  const [result, setResult] = React.useState<any | null>(null)
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null)

  const handleCalculate = async (save: boolean = false) => {
    setIsCalculating(true)
    setErrorMsg(null)
    setSuccessMsg(null)

    try {
      const startOfMonth = `${referencePeriod}-01T00:00:00Z`
      const endOfMonth = `${referencePeriod}-31T23:59:59Z`

      const res = await calculateTipsClient({
        reference_period: referencePeriod,
        period_start: startOfMonth,
        period_end: endOfMonth,
        total_tips_collected: parseFloat(totalCollected) || 0,
        house_retention_percentage: parseFloat(retentionPercentage) || 0,
        save
      })

      setResult(res)
      if (save) {
        setSuccessMsg(`Rateio homologado com sucesso! ${res.total_beneficiaries} colaboradores receberão o repasse de R$ ${Number(res.net_tips_pool).toFixed(2)}.`)
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Erro ao calcular rateio.")
    } finally {
      setIsCalculating(false)
    }
  }

  // Calculate automatically on first mount
  React.useEffect(() => {
    handleCalculate(false)
  }, [])

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono tracking-widest text-[#00f0ff] uppercase bg-[#00f0ff]/10 px-2 py-0.5 rounded border border-[#00f0ff]/20">
              LEI DA GORJETA 13.419/2017
            </span>
            <span className="text-[11px] font-mono tracking-widest text-emerald-400 uppercase bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              COMPLIANCE & RATEIO
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 flex items-center gap-3">
            <DollarSign className="w-8 h-8 text-[#00f0ff]" />
            Rateio & Distribuição de Taxa de Serviço / Gorjetas
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Distribuição proporcional e transparente da taxa de serviço (10%/12%/13%) ponderada por horas trabalhadas e pontos por função.
          </p>
        </div>
      </div>

      <TeamNavigation />

      {/* Calculator Form */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Calculator className="w-4 h-4 text-[#00f0ff]" />
          Parâmetros do Período de Apuração
        </h2>

        {errorMsg && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400" />
            {errorMsg}
          </div>
        )}

        {successMsg && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2 font-bold">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            {successMsg}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Mês de Referência</label>
            <input
              type="month"
              value={referencePeriod}
              onChange={(e) => setReferencePeriod(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Total Arrecadado no PDV (R$)</label>
            <input
              type="number"
              step="0.01"
              value={totalCollected}
              onChange={(e) => setTotalCollected(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Retenção da Casa (Encargos %)</label>
            <input
              type="number"
              step="0.1"
              value={retentionPercentage}
              onChange={(e) => setRetentionPercentage(e.target.value)}
              placeholder="Ex: 10.00"
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => handleCalculate(false)}
            disabled={isCalculating}
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all inline-flex items-center gap-2"
          >
            <Calculator className="w-4 h-4 text-[#00f0ff]" />
            Simular Rateio
          </button>

          <button
            type="button"
            onClick={() => handleCalculate(true)}
            disabled={isCalculating}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-bold text-xs shadow-lg shadow-[#00f0ff]/20 hover:opacity-95 transition-all inline-flex items-center gap-2 disabled:opacity-50"
          >
            <CheckCircle2 className="w-4 h-4" />
            {isCalculating ? "Processando..." : "Homologar & Distribuir Gorjetas"}
          </button>
        </div>
      </div>

      {/* Results KPIs */}
      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <span className="text-[11px] font-mono text-slate-400">TOTAL ARRECADADO</span>
              <p className="text-2xl font-bold text-slate-100 mt-1">
                R$ {Number(result.total_tips_collected).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
              <span className="text-[10px] text-slate-400">Vendas do PDV & Salão</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <span className="text-[11px] font-mono text-amber-400">RETENÇÃO DA CASA ({result.house_retention_percentage}%)</span>
              <p className="text-2xl font-bold text-amber-300 mt-1">
                R$ {Number(result.house_retained_amount).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
              <span className="text-[10px] text-slate-400">Encargos trabalhistas / quebras</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <span className="text-[11px] font-mono text-emerald-400">FUNDO LÍQUIDO A REPASSAR</span>
              <p className="text-2xl font-bold text-emerald-300 mt-1">
                R$ {Number(result.net_tips_pool).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
              <span className="text-[10px] text-emerald-500 font-bold">100% Rateado entre a equipe</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <span className="text-[11px] font-mono text-blue-400">BENEFICIÁRIOS</span>
              <p className="text-2xl font-bold text-blue-300 mt-1">
                {result.total_beneficiaries} Colaboradores
              </p>
              <span className="text-[10px] text-slate-400">
                Fator total: {Number(result.total_points_pool).toFixed(1)} pts·h
              </span>
            </div>
          </div>

          {/* Breakdown Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
              <h3 className="text-xs font-mono uppercase text-slate-300">
                Detalhamento Individual do Repasse por Colaborador
              </h3>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/40 font-mono text-slate-400 uppercase">
                    <th className="p-4">Colaborador</th>
                    <th className="p-4">Função / Praça</th>
                    <th className="p-4">Horas Trabalhadas</th>
                    <th className="p-4">Pontos Função</th>
                    <th className="p-4">Fator de Ponderação</th>
                    <th className="p-4 text-right font-bold text-emerald-400">Repasse Líquido (R$)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {result.items?.map((item: any) => (
                    <tr key={item.employee_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-4 font-bold text-slate-100">{item.employee_name}</td>
                      <td className="p-4 text-slate-300">{item.role_title} ({item.department})</td>
                      <td className="p-4 font-mono text-slate-300">
                        {Number(item.hours_worked).toFixed(1)}h
                      </td>
                      <td className="p-4 font-mono text-[#00f0ff] font-bold">
                        {Number(item.points).toFixed(1)} pts
                      </td>
                      <td className="p-4 font-mono text-slate-400">
                        {Number(item.calculated_share).toFixed(1)}
                      </td>
                      <td className="p-4 font-mono text-right font-bold text-emerald-400 text-sm">
                        R$ {Number(item.allocated_tip_amount).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
