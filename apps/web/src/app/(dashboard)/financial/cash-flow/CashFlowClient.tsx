"use client"

import React, { useState } from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import {
  CalendarDays,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  Landmark,
  FileSpreadsheet,
  Upload,
  Calendar,
  Filter,
  CheckCircle2,
  X,
  Clock,
  Layers
} from "lucide-react"
import {
  CashFlowProjection,
  BankAccount
} from "@/types/financial"
import {
  fetchCashFlowClient,
  uploadBankStatementOFX
} from "@/lib/api-client"

interface CashFlowClientProps {
  initialCashFlow: CashFlowProjection | null
  bankAccounts: BankAccount[]
}

export default function CashFlowClient({
  initialCashFlow,
  bankAccounts
}: CashFlowClientProps) {
  const [cashFlow, setCashFlow] = useState<CashFlowProjection | null>(initialCashFlow)
  const [startDate, setStartDate] = useState<string>(new Date().toISOString().split("T")[0])
  const [endDate, setEndDate] = useState<string>(() => {
    const d = new Date()
    d.setDate(d.getDate() + 30)
    return d.toISOString().split("T")[0]
  })
  const [isLoading, setIsLoading] = useState<boolean>(false)

  // OFX Modal State
  const [isOfxModalOpen, setIsOfxModalOpen] = useState<boolean>(false)
  const [ofxBankAccountId, setOfxBankAccountId] = useState<string>(bankAccounts[0]?.id || "")
  const [ofxContent, setOfxContent] = useState<string>("")
  const [isUploadingOfx, setIsUploadingOfx] = useState<boolean>(false)
  const [toastMessage, setToastMessage] = useState<{ type: "success" | "error"; text: string } | null>(null)

  const showToast = (type: "success" | "error", text: string) => {
    setToastMessage({ type, text })
    setTimeout(() => setToastMessage(null), 4000)
  }

  const handleFilter = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setIsLoading(true)
    try {
      const data = await fetchCashFlowClient(
        new Date(startDate).toISOString(),
        new Date(endDate).toISOString()
      )
      setCashFlow(data)
    } catch (err) {
      showToast("error", "Erro ao filtrar fluxo de caixa.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      setOfxContent(text)
    }
    reader.readAsText(file)
  }

  const handleUploadOfxSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ofxContent.trim()) {
      showToast("error", "Selecione ou cole o conteúdo do arquivo OFX.")
      return
    }

    setIsUploadingOfx(true)
    try {
      const res = await uploadBankStatementOFX({
        bank_account_id: ofxBankAccountId,
        ofx_content: ofxContent
      })
      showToast("success", `Extrato importado com sucesso! ${res?.imported_count || 0} lançamentos adicionados (${res?.skipped_count || 0} duplicados ignorados).`)
      setIsOfxModalOpen(false)
      setOfxContent("")
      await handleFilter()
    } catch (err: any) {
      showToast("error", err.message || "Erro ao importar OFX.")
    } finally {
      setIsUploadingOfx(false)
    }
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "-"
    const [year, month, day] = dateStr.split("-")
    return `${day}/${month}/${year}`
  }

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`p-4 rounded-xl text-sm font-medium flex items-center justify-between shadow-2xl transition-all ${
          toastMessage.type === "success" ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40" : "bg-rose-500/20 text-rose-300 border border-rose-500/40"
        }`}>
          <span>{toastMessage.text}</span>
          <button onClick={() => setToastMessage(null)}><X className="h-4 w-4" /></button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <CalendarDays className="h-7 w-7 text-cyan-400" />
              Fluxo de Caixa Projetado
            </h1>
            <Badge variant="cyan">Previsto vs Realizado</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Projeção diária cruzando Contas a Pagar e Recebíveis de Cartões/Delivery para gestão antecipada de capital de giro.
          </p>
        </div>

        <button
          onClick={() => setIsOfxModalOpen(true)}
          className="bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all shadow-[0_0_15px_rgba(6,182,212,0.15)]"
        >
          <Upload className="h-4 w-4" />
          Importar Extrato OFX
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Saldo Inicial */}
        <GlassPanel accent="cyan" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Saldo Inicial</span>
            <Landmark className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {formatCurrency(cashFlow?.initial_balance || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Disponível em bancos e caixas</p>
          </div>
        </GlassPanel>

        {/* Card 2: Entradas no Período */}
        <GlassPanel accent="emerald" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Entradas Período</span>
            <ArrowUpRight className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-emerald-400 tracking-tight">
              +{formatCurrency(cashFlow?.total_inflows_period || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Recebíveis & Repasses</p>
          </div>
        </GlassPanel>

        {/* Card 3: Saídas no Período */}
        <GlassPanel accent="crimson" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">Saídas Período</span>
            <ArrowDownRight className="h-4 w-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-rose-400 tracking-tight">
              -{formatCurrency(cashFlow?.total_outflows_period || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Contas & Boletos a Pagar</p>
          </div>
        </GlassPanel>

        {/* Card 4: Saldo Final Projetado */}
        <GlassPanel accent="violet" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">Saldo Final Projetado</span>
            <TrendingUp className="h-4 w-4 text-violet-400" />
          </div>
          <div className="mt-3">
            <div className={`text-2xl font-bold tracking-tight ${
              (cashFlow?.final_projected_balance || 0) >= 0 ? "text-violet-300" : "text-rose-400"
            }`}>
              {formatCurrency(cashFlow?.final_projected_balance || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Resultado acumulado final</p>
          </div>
        </GlassPanel>

        {/* Card 5: Pior Saldo Projetado */}
        <GlassPanel accent="amber" className="p-4 flex flex-col justify-between border-amber-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Menor Ponto de Caixa</span>
            <AlertTriangle className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <div className={`text-2xl font-bold tracking-tight ${
              (cashFlow?.lowest_projected_balance || 0) < 0 ? "text-rose-400" : "text-amber-300"
            }`}>
              {formatCurrency(cashFlow?.lowest_projected_balance || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {(cashFlow?.lowest_projected_balance || 0) < 0 ? "⚠️ Atenção: Caixa Negativo" : "Caixa seguro no período"}
            </p>
          </div>
        </GlassPanel>
      </div>

      {/* Date Filters Bar */}
      <GlassPanel className="p-4">
        <form onSubmit={handleFilter} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-slate-400">De:</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold text-slate-400">Até:</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-4 py-1.5 rounded-xl text-xs font-bold transition-all shadow-[0_0_12px_rgba(6,182,212,0.3)]"
            >
              {isLoading ? "Filtrando..." : "Aplicar Período"}
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const now = new Date()
                setStartDate(now.toISOString().split("T")[0])
                const next30 = new Date()
                next30.setDate(now.getDate() + 30)
                setEndDate(next30.toISOString().split("T")[0])
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
            >
              Próximos 30 Dias
            </button>
            <button
              type="button"
              onClick={() => {
                const now = new Date()
                setStartDate(now.toISOString().split("T")[0])
                const next60 = new Date()
                next60.setDate(now.getDate() + 60)
                setEndDate(next60.toISOString().split("T")[0])
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
            >
              60 Dias
            </button>
          </div>
        </form>
      </GlassPanel>

      {/* Daily Cash Flow Table */}
      <GlassPanel className="overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Calendar className="h-4 w-4 text-cyan-400" />
            Extrato Diário Projetado ({cashFlow?.days?.length || 0} dias)
          </h2>
          <span className="text-xs text-slate-400">Valores em Reais (BRL)</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-900/60 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Data</th>
                <th className="py-3 px-4 text-right text-emerald-400">Entradas Previstas</th>
                <th className="py-3 px-4 text-right text-emerald-300">Entradas Realizadas</th>
                <th className="py-3 px-4 text-right font-bold text-emerald-400">Total Entradas</th>
                <th className="py-3 px-4 text-right text-rose-400">Saídas Previstas</th>
                <th className="py-3 px-4 text-right text-rose-300">Saídas Realizadas</th>
                <th className="py-3 px-4 text-right font-bold text-rose-400">Total Saídas</th>
                <th className="py-3 px-4 text-right font-bold">Resultado do Dia</th>
                <th className="py-3 px-4 text-right font-bold text-white">Saldo Acumulado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {cashFlow?.days?.map((day) => {
                const isNegative = day.accumulated_balance < 0
                return (
                  <tr
                    key={day.date}
                    className={`transition-colors ${
                      isNegative
                        ? "bg-rose-500/10 hover:bg-rose-500/15"
                        : "hover:bg-slate-800/30"
                    }`}
                  >
                    {/* Data */}
                    <td className="py-3 px-4 font-mono text-xs font-semibold">
                      <div className="flex items-center gap-1.5">
                        {isNegative && <AlertTriangle className="h-3.5 w-3.5 text-rose-400 shrink-0" />}
                        <span className={isNegative ? "text-rose-300 font-bold" : "text-white"}>
                          {formatDate(day.date)}
                        </span>
                      </div>
                    </td>

                    {/* Entradas Previstas */}
                    <td className="py-3 px-4 text-right font-mono text-xs text-slate-400">
                      {day.inflows_expected > 0 ? formatCurrency(day.inflows_expected) : "-"}
                    </td>

                    {/* Entradas Realizadas */}
                    <td className="py-3 px-4 text-right font-mono text-xs text-emerald-400/80">
                      {day.inflows_realized > 0 ? formatCurrency(day.inflows_realized) : "-"}
                    </td>

                    {/* Total Entradas */}
                    <td className="py-3 px-4 text-right font-mono text-xs font-bold text-emerald-400">
                      {day.total_inflows > 0 ? `+${formatCurrency(day.total_inflows)}` : "-"}
                    </td>

                    {/* Saídas Previstas */}
                    <td className="py-3 px-4 text-right font-mono text-xs text-slate-400">
                      {day.outflows_expected > 0 ? formatCurrency(day.outflows_expected) : "-"}
                    </td>

                    {/* Saídas Realizadas */}
                    <td className="py-3 px-4 text-right font-mono text-xs text-rose-400/80">
                      {day.outflows_realized > 0 ? formatCurrency(day.outflows_realized) : "-"}
                    </td>

                    {/* Total Saídas */}
                    <td className="py-3 px-4 text-right font-mono text-xs font-bold text-rose-400">
                      {day.total_outflows > 0 ? `-${formatCurrency(day.total_outflows)}` : "-"}
                    </td>

                    {/* Resultado do Dia */}
                    <td className={`py-3 px-4 text-right font-mono text-xs font-bold ${
                      day.net_day > 0 ? "text-emerald-400" : day.net_day < 0 ? "text-rose-400" : "text-slate-500"
                    }`}>
                      {day.net_day !== 0 ? formatCurrency(day.net_day) : "R$ 0,00"}
                    </td>

                    {/* Saldo Acumulado */}
                    <td className={`py-3 px-4 text-right font-mono text-sm font-bold ${
                      day.accumulated_balance < 0
                        ? "text-rose-400 font-black"
                        : "text-white"
                    }`}>
                      {formatCurrency(day.accumulated_balance)}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </GlassPanel>

      {/* Modal: Importar Extrato Bancário OFX */}
      {isOfxModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Upload className="h-5 w-5 text-cyan-400" />
                  Importar Extrato OFX
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Suporta arquivos .ofx emitidos por Itaú, Bradesco, Santander, Banco do Brasil, Inter, Stone, Cora, etc.
                </p>
              </div>
              <button onClick={() => setIsOfxModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleUploadOfxSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Conta Bancária de Destino</label>
                <select
                  required
                  value={ofxBankAccountId}
                  onChange={(e) => setOfxBankAccountId(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                >
                  {bankAccounts.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name} ({formatCurrency(acc.current_balance)})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Arquivo OFX</label>
                <input
                  type="file"
                  accept=".ofx,.txt"
                  onChange={handleFileUpload}
                  className="w-full mt-1 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-cyan-500/20 file:text-cyan-300 hover:file:bg-cyan-500/30 text-xs text-slate-400"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Ou Cole o Conteúdo do Extrato</label>
                <textarea
                  rows={6}
                  value={ofxContent}
                  onChange={(e) => setOfxContent(e.target.value)}
                  placeholder="Cole o conteúdo XML/SGML do arquivo OFX aqui..."
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsOfxModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-400 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isUploadingOfx}
                  className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-sm transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)]"
                >
                  {isUploadingOfx ? "Importando..." : "Processar Extrato"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
