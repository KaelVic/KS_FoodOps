"use client"

import React, { useState } from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import {
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Percent,
  Wallet,
  Plus,
  ArrowDownRight,
  Filter,
  Building2,
  CreditCard,
  Smartphone,
  Store,
  DollarSign,
  ChevronDown,
  ChevronUp,
  X
} from "lucide-react"
import {
  ReceivableInvoice,
  ReceivablesDashboardMetrics,
  PaymentAcquirer,
  BankAccount,
  FinancialCategory,
  CostCenter,
  ReceivableInstallment,
  CreateReceivableInvoicePayload
} from "@/types/financial"
import {
  createReceivableInvoice,
  settleReceivableInstallment,
  cancelReceivableInvoice,
  fetchReceivableInvoicesClient
} from "@/lib/api-client"

interface ReceivablesClientProps {
  initialDashboard: ReceivablesDashboardMetrics | null
  initialInvoices: ReceivableInvoice[]
  acquirers: PaymentAcquirer[]
  bankAccounts: BankAccount[]
  categories: FinancialCategory[]
  costCenters: CostCenter[]
}

export default function ReceivablesClient({
  initialDashboard,
  initialInvoices,
  acquirers,
  bankAccounts,
  categories,
  costCenters
}: ReceivablesClientProps) {
  const [invoices, setInvoices] = useState<ReceivableInvoice[]>(initialInvoices)
  const [dashboard, setDashboard] = useState<ReceivablesDashboardMetrics | null>(initialDashboard)
  const [statusFilter, setStatusFilter] = useState<string>("ALL")
  const [channelFilter, setChannelFilter] = useState<string>("ALL")
  const [expandedInvoiceId, setExpandedInvoiceId] = useState<string | null>(null)

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false)
  const [isSettleModalOpen, setIsSettleModalOpen] = useState<boolean>(false)
  const [selectedInstallment, setSelectedInstallment] = useState<ReceivableInstallment | null>(null)
  const [selectedInvoice, setSelectedInvoice] = useState<ReceivableInvoice | null>(null)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [toastMessage, setToastMessage] = useState<{ type: "success" | "error"; text: string } | null>(null)

  // Create Form State
  const [customerName, setCustomerName] = useState<string>("Consumidor Final (PDV)")
  const [customerTaxId, setCustomerTaxId] = useState<string>("")
  const [channel, setChannel] = useState<"POS" | "DELIVERY_IFOOD" | "DELIVERY_OWN" | "CORPORATE_INVOICE">("POS")
  const [selectedAcquirerId, setSelectedAcquirerId] = useState<string>(acquirers[0]?.id || "")
  const [paymentMethod, setPaymentMethod] = useState<string>("CREDIT_CARD")
  const [cardBrand, setCardBrand] = useState<string>("MASTERCARD")
  const [description, setDescription] = useState<string>("Faturamento de Vendas")
  const [grossAmount, setGrossAmount] = useState<string>("")
  const [feePercentage, setFeePercentage] = useState<string>("")
  const [documentNumber, setDocumentNumber] = useState<string>("")
  const [dueDate, setDueDate] = useState<string>(new Date().toISOString().split("T")[0])

  // Settlement Form State
  const [settleBankAccountId, setSettleBankAccountId] = useState<string>(bankAccounts[0]?.id || "")
  const [settleGrossAmount, setSettleGrossAmount] = useState<string>("")
  const [settleFeeDeducted, setSettleFeeDeducted] = useState<string>("")
  const [settleNetReceived, setSettleNetReceived] = useState<string>("")
  const [settleBankRef, setSettleBankRef] = useState<string>("")
  const [settleNotes, setSettleNotes] = useState<string>("")

  const showToast = (type: "success" | "error", text: string) => {
    setToastMessage({ type, text })
    setTimeout(() => setToastMessage(null), 4000)
  }

  const reloadData = async () => {
    try {
      const updated = await fetchReceivableInvoicesClient(
        statusFilter === "ALL" ? undefined : statusFilter,
        channelFilter === "ALL" ? undefined : channelFilter
      )
      setInvoices(updated)
    } catch (err) {
      console.error(err)
    }
  }

  const handleStatusFilterChange = async (status: string) => {
    setStatusFilter(status)
    const updated = await fetchReceivableInvoicesClient(
      status === "ALL" ? undefined : status,
      channelFilter === "ALL" ? undefined : channelFilter
    )
    setInvoices(updated)
  }

  const handleChannelFilterChange = async (ch: string) => {
    setChannelFilter(ch)
    const updated = await fetchReceivableInvoicesClient(
      statusFilter === "ALL" ? undefined : statusFilter,
      ch === "ALL" ? undefined : ch
    )
    setInvoices(updated)
  }

  // Handle acquirer selection to auto-fill fee percentage
  const handleAcquirerChange = (acqId: string) => {
    setSelectedAcquirerId(acqId)
    const acq = acquirers.find(a => a.id === acqId)
    if (acq) {
      if (paymentMethod === "DEBIT_CARD") setFeePercentage(String(acq.debit_fee_percentage))
      else if (paymentMethod === "CREDIT_CARD") setFeePercentage(String(acq.credit_1x_fee_percentage))
      else if (paymentMethod === "MEAL_VOUCHER") setFeePercentage(String(acq.voucher_fee_percentage))
      else if (paymentMethod === "DELIVERY_ONLINE" || channel === "DELIVERY_IFOOD") setFeePercentage(String(acq.delivery_fee_percentage))
      else if (paymentMethod === "PIX") setFeePercentage(String(acq.pix_fee_percentage))
    }
  }

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!grossAmount || parseFloat(grossAmount) <= 0) {
      showToast("error", "Informe um valor bruto válido.")
      return
    }

    setIsSubmitting(true)
    try {
      const payload: CreateReceivableInvoicePayload = {
        customer_name: customerName,
        customer_tax_id: customerTaxId || null,
        channel: channel,
        acquirer_id: selectedAcquirerId || null,
        payment_method: paymentMethod,
        card_brand: cardBrand || null,
        description: description,
        document_number: documentNumber || null,
        gross_amount: parseFloat(grossAmount),
        fee_percentage: feePercentage ? parseFloat(feePercentage) : null,
        due_date: new Date(dueDate).toISOString()
      }

      await createReceivableInvoice(payload)
      showToast("success", "Título a receber registrado com sucesso!")
      setIsCreateModalOpen(false)
      setGrossAmount("")
      setDocumentNumber("")
      await reloadData()
    } catch (err: any) {
      showToast("error", err.message || "Erro ao registrar título.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleOpenSettle = (inst: ReceivableInstallment, inv: ReceivableInvoice) => {
    setSelectedInstallment(inst)
    setSelectedInvoice(inv)
    setSettleGrossAmount(String(inst.gross_amount))
    setSettleFeeDeducted(String(inst.fee_amount))
    setSettleNetReceived(String(inst.net_amount))
    setSettleBankAccountId(bankAccounts[0]?.id || "")
    setSettleBankRef("")
    setSettleNotes("")
    setIsSettleModalOpen(true)
  }

  const handleSettleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedInstallment) return

    setIsSubmitting(true)
    try {
      await settleReceivableInstallment(selectedInstallment.id, {
        bank_account_id: settleBankAccountId,
        gross_amount: parseFloat(settleGrossAmount),
        fee_deducted: parseFloat(settleFeeDeducted),
        net_received_amount: parseFloat(settleNetReceived),
        bank_transaction_ref: settleBankRef || null,
        notes: settleNotes || null
      })

      showToast("success", "Repasse bancário confirmado e creditado na conta com sucesso!")
      setIsSettleModalOpen(false)
      await reloadData()
    } catch (err: any) {
      showToast("error", err.message || "Erro ao liquidar recebível.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCancelInvoice = async (invoiceId: string) => {
    if (!confirm("Tem certeza que deseja cancelar este título a receber?")) return
    try {
      const ok = await cancelReceivableInvoice(invoiceId, "Cancelado manualmente pelo usuário")
      if (ok) {
        showToast("success", "Título cancelado com sucesso.")
        await reloadData()
      }
    } catch (err) {
      showToast("error", "Erro ao cancelar título.")
    }
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const formatDate = (iso: string) => {
    if (!iso) return "-"
    const d = new Date(iso)
    return d.toLocaleDateString("pt-BR")
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

      {/* Header & Main Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <TrendingUp className="h-7 w-7 text-emerald-400" />
              Contas a Receber & Conciliação (AR)
            </h1>
            <Badge variant="emerald">ERP Food-Service</Badge>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Gestão de faturamento, recebíveis de cartões, repasses iFood/Delivery e controle das taxas de maquininhas (MDR).
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-4 py-2.5 rounded-xl text-sm flex items-center gap-2 transition-all shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:scale-[1.02]"
        >
          <Plus className="h-4 w-4 stroke-[3]" />
          Novo Título a Receber
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Previsto Hoje */}
        <GlassPanel accent="cyan" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Previsto Hoje</span>
            <Clock className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {formatCurrency(dashboard?.total_expected_today || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {dashboard?.count_expected_today || 0} lançamentos previstos
            </p>
          </div>
        </GlassPanel>

        {/* Card 2: Repasses da Semana */}
        <GlassPanel accent="violet" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">Repasses 7 Dias</span>
            <ArrowDownRight className="h-4 w-4 text-violet-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {formatCurrency(dashboard?.total_next_7_days || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Próximos repasses agendados</p>
          </div>
        </GlassPanel>

        {/* Card 3: Recebido no Mês */}
        <GlassPanel accent="emerald" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Recebido no Mês</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-emerald-400 tracking-tight">
              {formatCurrency(dashboard?.total_received_month || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Liquidado em conta corrente</p>
          </div>
        </GlassPanel>

        {/* Card 4: Taxas Retidas pelas Maquininhas */}
        <GlassPanel accent="amber" className="p-4 flex flex-col justify-between border-amber-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Taxas MDR Retidas</span>
            <Percent className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-amber-300 tracking-tight">
              {formatCurrency(dashboard?.total_fees_deducted_month || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Custo maquininhas & delivery</p>
          </div>
        </GlassPanel>

        {/* Card 5: Saldo em Contas */}
        <GlassPanel accent="cyan" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Saldo em Banco/Caixas</span>
            <Wallet className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-white tracking-tight">
              {formatCurrency(dashboard?.total_bank_balance || 0)}
            </div>
            <p className="text-xs text-slate-400 mt-1">Saldo consolidado disponível</p>
          </div>
        </GlassPanel>
      </div>

      {/* Filters Bar */}
      <GlassPanel className="p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Status Filter */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
          <span className="text-xs font-semibold text-slate-400 mr-2 flex items-center gap-1">
            <Filter className="h-3.5 w-3.5" /> Status:
          </span>
          {[
            { key: "ALL", label: "Todos" },
            { key: "PENDING", label: "Pendentes" },
            { key: "PARTIALLY_RECEIVED", label: "Parciais" },
            { key: "RECEIVED", label: "Recebidos" },
            { key: "OVERDUE", label: "Atrasados" }
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => handleStatusFilterChange(f.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                statusFilter === f.key
                  ? "bg-emerald-500 text-slate-950 shadow-[0_0_12px_rgba(16,185,129,0.4)] font-bold"
                  : "bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Channel Filter */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0">
          <span className="text-xs font-semibold text-slate-400 mr-2 flex items-center gap-1">
            <Store className="h-3.5 w-3.5" /> Canal:
          </span>
          {[
            { key: "ALL", label: "Todos Canais" },
            { key: "POS", label: "PDV / Salão" },
            { key: "DELIVERY_IFOOD", label: "iFood" },
            { key: "DELIVERY_OWN", label: "Delivery Próprio" },
            { key: "CORPORATE_INVOICE", label: "Faturado / Eventos" }
          ].map((c) => (
            <button
              key={c.key}
              onClick={() => handleChannelFilterChange(c.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                channelFilter === c.key
                  ? "bg-cyan-500 text-slate-950 shadow-[0_0_12px_rgba(6,182,212,0.4)] font-bold"
                  : "bg-slate-800/60 text-slate-300 hover:bg-slate-700/60"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </GlassPanel>

      {/* Receivables Table */}
      <GlassPanel className="overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-400" />
            Títulos & Lançamentos a Receber ({invoices.length})
          </h2>
        </div>

        {invoices.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <TrendingUp className="h-10 w-10 text-slate-600 mx-auto mb-3 opacity-50" />
            <p className="text-base font-medium text-slate-300">Nenhum título a receber encontrado</p>
            <p className="text-xs text-slate-500 mt-1">Cadastre novos lançamentos ou integre as vendas do PDV e iFood.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900/60 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Canal / Origem</th>
                  <th className="py-3.5 px-4">Descrição & Cliente</th>
                  <th className="py-3.5 px-4">Previsão / Vencimento</th>
                  <th className="py-3.5 px-4 text-right">Valor Bruto</th>
                  <th className="py-3.5 px-4 text-right">Taxa MDR</th>
                  <th className="py-3.5 px-4 text-right font-bold text-white">Líquido a Receber</th>
                  <th className="py-3.5 px-4 text-center">Status</th>
                  <th className="py-3.5 px-4 text-center">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {invoices.map((inv) => {
                  const isExpanded = expandedInvoiceId === inv.id
                  return (
                    <React.Fragment key={inv.id}>
                      <tr className="hover:bg-slate-800/30 transition-colors">
                        {/* Canal */}
                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-2">
                            {inv.channel === "DELIVERY_IFOOD" ? (
                              <Badge variant="crimson" className="flex items-center gap-1">
                                <Smartphone className="h-3 w-3" /> iFood
                              </Badge>
                            ) : inv.channel === "CORPORATE_INVOICE" ? (
                              <Badge variant="violet" className="flex items-center gap-1">
                                <Building2 className="h-3 w-3" /> Faturado
                              </Badge>
                            ) : (
                              <Badge variant="cyan" className="flex items-center gap-1">
                                <Store className="h-3 w-3" /> PDV Salão
                              </Badge>
                            )}
                          </div>
                        </td>

                        {/* Descrição & Cliente */}
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-white">{inv.description}</div>
                          <div className="text-xs text-slate-400">{inv.customer_name} {inv.document_number ? `• Doc: ${inv.document_number}` : ""}</div>
                        </td>

                        {/* Previsão */}
                        <td className="py-3.5 px-4 text-slate-300 text-xs">
                          <div className="font-medium text-white">{formatDate(inv.due_date)}</div>
                          <div className="text-[11px] text-slate-500">Emissão: {formatDate(inv.issue_date)}</div>
                        </td>

                        {/* Valor Bruto */}
                        <td className="py-3.5 px-4 text-right font-mono text-slate-400">
                          {formatCurrency(inv.gross_amount)}
                        </td>

                        {/* Taxa MDR */}
                        <td className="py-3.5 px-4 text-right font-mono text-amber-400 text-xs">
                          -{formatCurrency(inv.deductions_amount)}
                        </td>

                        {/* Líquido a Receber */}
                        <td className="py-3.5 px-4 text-right font-mono font-bold text-emerald-400">
                          {formatCurrency(inv.net_amount)}
                        </td>

                        {/* Status */}
                        <td className="py-3.5 px-4 text-center">
                          {(() => {
                            switch (inv.status) {
                              case "RECEIVED": return <Badge variant="emerald">Recebido</Badge>
                              case "PARTIALLY_RECEIVED": return <Badge variant="amber">Parcial</Badge>
                              case "CANCELLED": return <Badge variant="crimson">Cancelado</Badge>
                              default: return <Badge variant="cyan">Pendente</Badge>
                            }
                          })()}
                        </td>

                        {/* Ações */}
                        <td className="py-3.5 px-4 text-center">
                          <div className="flex items-center justify-center gap-1.5">
                            <button
                              onClick={() => setExpandedInvoiceId(isExpanded ? null : inv.id)}
                              className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                              title="Ver Lançamentos e Taxas"
                            >
                              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            </button>
                            {inv.status !== "RECEIVED" && inv.status !== "CANCELLED" && (
                              <button
                                onClick={() => handleCancelInvoice(inv.id)}
                                className="p-1.5 hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 rounded-lg transition-colors text-xs"
                                title="Cancelar Título"
                              >
                                <X className="h-3.5 w-3.5" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>

                      {/* Expanded Installments & Card Transactions */}
                      {isExpanded && (
                        <tr className="bg-slate-950/60">
                          <td colSpan={8} className="p-4">
                            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3">
                              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                                <CreditCard className="h-3.5 w-3.5 text-cyan-400" />
                                Detalhamento dos Lançamentos & Adquirentes
                              </h3>

                              <div className="space-y-2">
                                {inv.installments.map((inst) => {
                                  const isOverdue = new Date(inst.expected_settlement_date) < new Date() && inst.status === "PENDING"
                                  return (
                                    <div
                                      key={inst.id}
                                      className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 gap-3"
                                    >
                                      <div className="flex items-center gap-3">
                                        <div className="h-8 w-8 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-xs text-white">
                                          {inst.installment_number}/{inst.total_installments}
                                        </div>
                                        <div>
                                          <div className="text-sm font-semibold text-white flex items-center gap-2">
                                            <span>{inst.payment_method.replace("_", " ")}</span>
                                            {inst.card_brand && <Badge variant="default">{inst.card_brand}</Badge>}
                                            {inst.acquirer_name && (
                                              <span className="text-xs text-cyan-400 font-normal">({inst.acquirer_name})</span>
                                            )}
                                          </div>
                                          <div className="text-xs text-slate-400">
                                            Repasse Previsto: <span className="font-semibold text-slate-200">{formatDate(inst.expected_settlement_date)}</span>
                                            {inst.nsu ? ` • NSU: ${inst.nsu}` : ""}
                                          </div>
                                        </div>
                                      </div>

                                      <div className="flex items-center justify-between sm:justify-end gap-4">
                                        <div className="text-right">
                                          <div className="text-xs text-slate-400">
                                            Bruto: <span className="font-mono">{formatCurrency(inst.gross_amount)}</span> | Taxa ({inst.fee_percentage}%): <span className="font-mono text-amber-400">-{formatCurrency(inst.fee_amount)}</span>
                                          </div>
                                          <div className="text-sm font-bold font-mono text-emerald-400">
                                            Líquido: {formatCurrency(inst.net_amount)}
                                          </div>
                                        </div>

                                        {inst.status === "RECEIVED" ? (
                                          <Badge variant="emerald" className="flex items-center gap-1">
                                            <CheckCircle2 className="h-3 w-3" /> Creditado
                                          </Badge>
                                        ) : (
                                          <div className="flex items-center gap-2">
                                            {isOverdue && <Badge variant="crimson">Atrasado</Badge>}
                                            <button
                                              onClick={() => handleOpenSettle(inst, inv)}
                                              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-[0_0_10px_rgba(16,185,129,0.3)] flex items-center gap-1"
                                            >
                                              <DollarSign className="h-3.5 w-3.5 stroke-[3]" />
                                              Baixar / Repasse
                                            </button>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </GlassPanel>

      {/* Modal: Novo Título a Receber */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
                Registrar Título a Receber
              </h2>
              <button onClick={() => setIsCreateModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateInvoice} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Canal de Venda</label>
                  <select
                    value={channel}
                    onChange={(e: any) => setChannel(e.target.value)}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="POS">PDV / Balcão / Salão</option>
                    <option value="DELIVERY_IFOOD">iFood Marketplace</option>
                    <option value="DELIVERY_OWN">Delivery Próprio (WhatsApp/Site)</option>
                    <option value="CORPORATE_INVOICE">Faturamento Corporativo / Evento</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300">Cliente / Descritivo</label>
                  <input
                    type="text"
                    required
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="Ex: Consumidor Final ou Empresa ABC"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Adquirente / Maquininha</label>
                  <select
                    value={selectedAcquirerId}
                    onChange={(e) => handleAcquirerChange(e.target.value)}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="">Sem Adquirente (Direto)</option>
                    {acquirers.map((acq) => (
                      <option key={acq.id} value={acq.id}>
                        {acq.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300">Forma de Pagamento</label>
                  <select
                    value={paymentMethod}
                    onChange={(e) => {
                      setPaymentMethod(e.target.value)
                      handleAcquirerChange(selectedAcquirerId)
                    }}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="CREDIT_CARD">Cartão de Crédito (1x)</option>
                    <option value="DEBIT_CARD">Cartão de Débito</option>
                    <option value="MEAL_VOUCHER">Voucher Refeição / Alimentação (VR/VA)</option>
                    <option value="PIX">PIX Direto</option>
                    <option value="DELIVERY_ONLINE">Pagamento Online Delivery</option>
                    <option value="CASH">Dinheiro / Espécie</option>
                    <option value="BOLETO">Boleto Bancário</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Valor Bruto (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={grossAmount}
                    onChange={(e) => setGrossAmount(e.target.value)}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300">Taxa MDR (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={feePercentage}
                    onChange={(e) => setFeePercentage(e.target.value)}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                    placeholder="Ex: 2.79"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300">Data de Vencimento / Repasse</label>
                  <input
                    type="date"
                    required
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Descrição / Referência</label>
                <input
                  type="text"
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-400 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-sm transition-all"
                >
                  {isSubmitting ? "Gravando..." : "Salvar Título"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Confirmar Baixa / Repasse Bancário */}
      {isSettleModalOpen && selectedInstallment && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-emerald-400" />
                  Confirmar Repasse / Baixa
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">{selectedInvoice?.description}</p>
              </div>
              <button onClick={() => setIsSettleModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSettleSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300">Conta Bancária / Caixa de Destino</label>
                <select
                  required
                  value={settleBankAccountId}
                  onChange={(e) => setSettleBankAccountId(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  {bankAccounts.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name} ({formatCurrency(acc.current_balance)})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300">Valor Bruto (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={settleGrossAmount}
                    onChange={(e) => {
                      setSettleGrossAmount(e.target.value)
                      const gross = parseFloat(e.target.value) || 0
                      const fee = parseFloat(settleFeeDeducted) || 0
                      setSettleNetReceived(String((gross - fee).toFixed(2)))
                    }}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300">Taxa Retida (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={settleFeeDeducted}
                    onChange={(e) => {
                      setSettleFeeDeducted(e.target.value)
                      const gross = parseFloat(settleGrossAmount) || 0
                      const fee = parseFloat(e.target.value) || 0
                      setSettleNetReceived(String((gross - fee).toFixed(2)))
                    }}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-amber-300 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-300">Líquido Depositado (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={settleNetReceived}
                    onChange={(e) => setSettleNetReceived(e.target.value)}
                    className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-emerald-400 font-bold focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300">Identificador / Extrato Bancário</label>
                <input
                  type="text"
                  value={settleBankRef}
                  onChange={(e) => setSettleBankRef(e.target.value)}
                  className="w-full mt-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                  placeholder="Ex: DEP-STONE-9988 ou REPASSE-IFOOD"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsSettleModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-semibold text-slate-400 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold px-5 py-2.5 rounded-xl text-sm transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                >
                  {isSubmitting ? "Processando..." : "Confirmar Recebimento"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
