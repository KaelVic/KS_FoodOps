"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { 
  CreditCard, 
  Plus, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Landmark, 
  Calendar, 
  DollarSign, 
  Copy, 
  Check, 
  X, 
  ChevronDown, 
  ChevronUp,
  Receipt,
  FileText,
  Trash2,
  ExternalLink
} from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { 
  PayableBill, 
  PayableInstallment, 
  PayablesDashboardMetrics, 
  FinancialCategory, 
  CostCenter, 
  BankAccount, 
  CreatePayableBillPayload, 
  SettleInstallmentPayload 
} from "@/types/financial"
import { Supplier } from "@/types/master-data"
import { createPayableBill, settleInstallment, cancelPayableBill } from "@/lib/api-client"

interface PayablesClientProps {
  initialDashboard: PayablesDashboardMetrics | null
  initialBills: PayableBill[]
  suppliers: Supplier[]
  categories: FinancialCategory[]
  costCenters: CostCenter[]
  bankAccounts: BankAccount[]
}

export default function PayablesClient({
  initialDashboard,
  initialBills,
  suppliers,
  categories,
  costCenters,
  bankAccounts
}: PayablesClientProps) {
  const router = useRouter()
  const [bills, setBills] = useState<PayableBill[]>(initialBills)
  const [dashboard, setDashboard] = useState<PayablesDashboardMetrics | null>(initialDashboard)
  const [filterStatus, setFilterStatus] = useState<string>("ALL")
  const [expandedBillId, setExpandedBillId] = useState<string | null>(null)
  const [copiedPixId, setCopiedPixId] = useState<string | null>(null)

  // Modal State: Create Bill
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    supplier_id: suppliers[0]?.id || "",
    category_id: categories[0]?.id || "",
    cost_center_id: costCenters[0]?.id || "",
    document_number: "",
    description: "",
    total_amount: "",
    first_due_date: new Date().toISOString().slice(0, 10),
    installment_count: 1,
    barcode: "",
    pix_code: "",
    notes: ""
  })

  // Modal State: Settle Installment
  const [settleModal, setSettleModal] = useState<{
    isOpen: boolean
    installment: PayableInstallment | null
    bill: PayableBill | null
  }>({
    isOpen: false,
    installment: null,
    bill: null
  })

  const [settleForm, setSettleForm] = useState({
    bank_account_id: bankAccounts[0]?.id || "",
    payment_method: "PIX",
    settlement_date: new Date().toISOString().slice(0, 10),
    interest_amount: "0.00",
    fine_amount: "0.00",
    discount_amount: "0.00",
    transaction_reference: "",
    notes: ""
  })

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val || 0)
  }

  const handleCopyPix = (pixCode: string, id: string) => {
    navigator.clipboard.writeText(pixCode)
    setCopiedPixId(id)
    setTimeout(() => setCopiedPixId(null), 3000)
  }

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.supplier_id || !formData.description || !formData.total_amount) {
      alert("Preencha todos os campos obrigatórios.")
      return
    }

    setIsSubmitting(true)
    const payload: CreatePayableBillPayload = {
      supplier_id: formData.supplier_id,
      category_id: formData.category_id || null,
      cost_center_id: formData.cost_center_id || null,
      document_number: formData.document_number || null,
      description: formData.description,
      total_amount: parseFloat(formData.total_amount),
      first_due_date: new Date(formData.first_due_date).toISOString(),
      installment_count: Number(formData.installment_count) || 1,
      barcode: formData.barcode || null,
      pix_code: formData.pix_code || null,
      notes: formData.notes || null
    }

    const created = await createPayableBill(payload)
    setIsSubmitting(false)

    if (created) {
      setIsCreateOpen(false)
      setFormData({
        supplier_id: suppliers[0]?.id || "",
        category_id: categories[0]?.id || "",
        cost_center_id: costCenters[0]?.id || "",
        document_number: "",
        description: "",
        total_amount: "",
        first_due_date: new Date().toISOString().slice(0, 10),
        installment_count: 1,
        barcode: "",
        pix_code: "",
        notes: ""
      })
      router.refresh()
    } else {
      alert("Erro ao criar conta a pagar. Verifique os dados.")
    }
  }

  const handleOpenSettle = (inst: PayableInstallment, bill: PayableBill) => {
    setSettleModal({
      isOpen: true,
      installment: inst,
      bill: bill
    })
    setSettleForm({
      bank_account_id: bankAccounts[0]?.id || "",
      payment_method: "PIX",
      settlement_date: new Date().toISOString().slice(0, 10),
      interest_amount: "0.00",
      fine_amount: "0.00",
      discount_amount: "0.00",
      transaction_reference: "",
      notes: ""
    })
  }

  const handleSettleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!settleModal.installment) return

    setIsSubmitting(true)
    const payload: SettleInstallmentPayload = {
      bank_account_id: settleForm.bank_account_id,
      payment_method: settleForm.payment_method,
      settlement_date: new Date(settleForm.settlement_date).toISOString(),
      interest_amount: parseFloat(settleForm.interest_amount) || 0,
      fine_amount: parseFloat(settleForm.fine_amount) || 0,
      discount_amount: parseFloat(settleForm.discount_amount) || 0,
      transaction_reference: settleForm.transaction_reference || null,
      notes: settleForm.notes || null
    }

    const res = await settleInstallment(settleModal.installment.id, payload)
    setIsSubmitting(false)

    if (res) {
      setSettleModal({ isOpen: false, installment: null, bill: null })
      router.refresh()
    } else {
      alert("Erro ao liquidar parcela.")
    }
  }

  const handleCancelBill = async (billId: string) => {
    if (!confirm("Tem certeza que deseja cancelar este título a pagar?")) return
    const success = await cancelPayableBill(billId, "Cancelado pelo usuário no painel financeiro")
    if (success) {
      router.refresh()
    } else {
      alert("Não foi possível cancelar o título (pode conter parcelas já pagas).")
    }
  }

  const filteredBills = bills.filter(b => {
    if (filterStatus === "ALL") return true
    return b.status === filterStatus
  })

  // Settle calculations
  const instAmount = settleModal.installment?.amount || 0
  const interest = parseFloat(settleForm.interest_amount) || 0
  const fine = parseFloat(settleForm.fine_amount) || 0
  const discount = parseFloat(settleForm.discount_amount) || 0
  const totalSettlementValue = Math.max(0, instAmount + interest + fine - discount)

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
              <CreditCard className="h-8 w-8 text-[#00f0ff]" />
              Contas a Pagar (ERP)
            </h2>
            <span className="rounded-full bg-[#00f0ff]/10 px-3 py-1 text-xs font-semibold text-[#00f0ff] border border-[#00f0ff]/30">
              Pilar 1 • Financeiro
            </span>
          </div>
          <p className="text-slate-400 mt-1">
            Controle integrado de despesas, boletos bancários, PIX Copia-e-Cola, parcelamentos e baixas de títulos.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="bg-[#00f0ff] hover:bg-[#00f0ff]/90 text-slate-950 px-5 py-2.5 rounded-xl font-bold shadow-[0_0_20px_rgba(0,240,255,0.3)] hover:shadow-[0_0_30px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Novo Título a Pagar
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Vencem Hoje */}
        <GlassPanel accent="cyan" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Vencem Hoje</span>
            <Clock className="h-4 w-4 text-[#00f0ff]" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-100 tabular-nums">
              {formatCurrency(dashboard?.total_due_today || 0)}
            </span>
            <p className="text-xs text-slate-500 mt-0.5">{dashboard?.count_due_today || 0} parcelas hoje</p>
          </div>
        </GlassPanel>

        {/* Card 2: Vencidos / Atrasados */}
        <GlassPanel accent="crimson" className="p-4 flex flex-col justify-between border-rose-500/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">Atrasados / Vencidos</span>
            <AlertCircle className="h-4 w-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-rose-400 tabular-nums">
              {formatCurrency(dashboard?.total_overdue || 0)}
            </span>
            <p className="text-xs text-rose-400/70 mt-0.5">{dashboard?.count_overdue || 0} títulos pendentes</p>
          </div>
        </GlassPanel>

        {/* Card 3: Próximos 7 dias */}
        <GlassPanel accent="amber" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">Próximos 7 Dias</span>
            <Calendar className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-100 tabular-nums">
              {formatCurrency(dashboard?.total_next_7_days || 0)}
            </span>
            <p className="text-xs text-slate-500 mt-0.5">Previsão semanal</p>
          </div>
        </GlassPanel>

        {/* Card 4: Total Pago no Mês */}
        <GlassPanel accent="emerald" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Pago no Mês</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-emerald-400 tabular-nums">
              {formatCurrency(dashboard?.total_paid_month || 0)}
            </span>
            <p className="text-xs text-slate-500 mt-0.5">Liquidado</p>
          </div>
        </GlassPanel>

        {/* Card 5: Saldo em Banco/Caixa */}
        <GlassPanel accent="violet" className="p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">Saldo em Caixa</span>
            <Landmark className="h-4 w-4 text-purple-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-100 tabular-nums">
              {formatCurrency(dashboard?.total_bank_balance || 0)}
            </span>
            <p className="text-xs text-slate-500 mt-0.5">Disponível</p>
          </div>
        </GlassPanel>
      </div>

      {/* Filters & Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/50 p-2 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2">
          {["ALL", "PENDING", "PARTIALLY_PAID", "PAID", "CANCELLED"].map((st) => {
            const labels: Record<string, string> = {
              ALL: "Todos os Títulos",
              PENDING: "Pendentes",
              PARTIALLY_PAID: "Parcialmente Pagos",
              PAID: "Liquidados (Pagos)",
              CANCELLED: "Cancelados"
            }
            return (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  filterStatus === st
                    ? "bg-[#00f0ff] text-slate-950 shadow-[0_0_12px_rgba(0,240,255,0.3)]"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                }`}
              >
                {labels[st]}
              </button>
            )
          })}
        </div>

        <span className="text-xs text-slate-400 font-mono px-3">
          Exibindo {filteredBills.length} de {bills.length} títulos
        </span>
      </div>

      {/* Payables Table */}
      <GlassPanel className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-700">
              <tr>
                <th className="px-6 py-4 font-semibold">Fornecedor / Descrição</th>
                <th className="px-6 py-4 font-semibold">Categoria / C. Custo</th>
                <th className="px-6 py-4 font-semibold">Documento</th>
                <th className="px-6 py-4 font-semibold">1º Vencimento</th>
                <th className="px-6 py-4 font-semibold text-right">Valor Total</th>
                <th className="px-6 py-4 font-semibold text-right">Restante</th>
                <th className="px-6 py-4 font-semibold text-center">Status</th>
                <th className="px-6 py-4 font-semibold text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filteredBills.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-500">
                    Nenhum título a pagar encontrado para este filtro.
                  </td>
                </tr>
              ) : (
                filteredBills.map((bill) => {
                  const isExpanded = expandedBillId === bill.id
                  const getStatusBadge = (status: string) => {
                    switch (status) {
                      case "PAID": return <Badge variant="emerald">Liquidado</Badge>
                      case "PARTIALLY_PAID": return <Badge variant="amber">Parcial</Badge>
                      case "CANCELLED": return <Badge variant="crimson">Cancelado</Badge>
                      default: return <Badge variant="cyan">Pendente</Badge>
                    }
                  }

                  return (
                    <React.Fragment key={bill.id}>
                      <tr className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-slate-100">{bill.supplier_name}</div>
                          <div className="text-xs text-slate-400 mt-0.5">{bill.description}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-slate-200 text-xs font-medium">{bill.category_name || "Sem categoria"}</div>
                          <div className="text-[11px] text-slate-400 mt-0.5">{bill.cost_center_name || "Sem C. Custo"}</div>
                        </td>
                        <td className="px-6 py-4 font-mono text-slate-400">
                          {bill.document_number || "—"}
                        </td>
                        <td className="px-6 py-4 text-slate-300">
                          {new Date(bill.first_due_date).toLocaleDateString("pt-BR")}
                        </td>
                        <td className="px-6 py-4 text-right font-bold text-slate-100 tabular-nums">
                          {formatCurrency(bill.total_amount)}
                        </td>
                        <td className="px-6 py-4 text-right font-bold text-amber-400 tabular-nums">
                          {formatCurrency(bill.remaining_amount)}
                        </td>
                        <td className="px-6 py-4 text-center">
                          {getStatusBadge(bill.status)}
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          <button
                            onClick={() => setExpandedBillId(isExpanded ? null : bill.id)}
                            className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-800 text-[#00f0ff] hover:bg-slate-700 transition-all inline-flex items-center gap-1"
                          >
                            {bill.installments.length} {bill.installments.length === 1 ? "Parcela" : "Parcelas"}
                            {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                          </button>

                          {bill.status !== "PAID" && bill.status !== "CANCELLED" && (
                            <button
                              onClick={() => handleCancelBill(bill.id)}
                              title="Cancelar Título"
                              className="text-slate-500 hover:text-rose-400 p-1.5 transition-colors rounded-lg hover:bg-slate-800"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      </tr>

                      {/* Expandable Installments Section */}
                      {isExpanded && (
                        <tr className="bg-slate-950/70">
                          <td colSpan={8} className="p-4 border-y border-slate-800">
                            <div className="bg-slate-900/90 rounded-xl p-4 border border-slate-800 space-y-3">
                              <h4 className="text-xs font-semibold uppercase tracking-wider text-[#00f0ff] flex items-center gap-2">
                                <Receipt className="h-4 w-4" /> Parcelas e Vencimentos — {bill.supplier_name}
                              </h4>

                              <div className="grid grid-cols-1 gap-2">
                                {bill.installments.map((inst) => {
                                  const isPaid = inst.status === "PAID"
                                  const isOverdue = inst.status === "OVERDUE"

                                  return (
                                    <div 
                                      key={inst.id}
                                      className="flex flex-wrap items-center justify-between gap-4 p-3 rounded-lg bg-slate-950/80 border border-slate-800"
                                    >
                                      <div className="flex items-center gap-3">
                                        <span className="h-6 w-6 rounded-full bg-slate-800 text-[11px] font-bold text-slate-300 flex items-center justify-center font-mono">
                                          {inst.installment_number}/{inst.total_installments}
                                        </span>
                                        <div>
                                          <div className="text-sm font-semibold text-slate-200">
                                            Vencimento: {new Date(inst.due_date).toLocaleDateString("pt-BR")}
                                          </div>
                                          <div className="text-xs font-bold text-emerald-400">
                                            {formatCurrency(inst.amount)}
                                          </div>
                                        </div>
                                      </div>

                                      {/* Barcode & PIX copy buttons */}
                                      <div className="flex items-center gap-2">
                                        {inst.pix_code && (
                                          <button
                                            type="button"
                                            onClick={() => handleCopyPix(inst.pix_code!, inst.id)}
                                            className="px-2.5 py-1 rounded-md bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs font-medium flex items-center gap-1.5 transition-all"
                                          >
                                            {copiedPixId === inst.id ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                                            {copiedPixId === inst.id ? "Copiado!" : "PIX Copia e Cola"}
                                          </button>
                                        )}

                                        {inst.barcode && (
                                          <button
                                            type="button"
                                            onClick={() => handleCopyPix(inst.barcode!, `bar_${inst.id}`)}
                                            className="px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-all"
                                          >
                                            {copiedPixId === `bar_${inst.id}` ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                                            {copiedPixId === `bar_${inst.id}` ? "Copiado!" : "Linha Boleto"}
                                          </button>
                                        )}
                                      </div>

                                      {/* Actions */}
                                      <div className="flex items-center gap-3">
                                        {isPaid ? (
                                          <Badge variant="emerald">
                                            <Check className="h-3 w-3 mr-1" /> Paga
                                          </Badge>
                                        ) : (
                                          <>
                                            {isOverdue && <Badge variant="crimson">Vencida</Badge>}
                                            <button
                                              onClick={() => handleOpenSettle(inst, bill)}
                                              className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-[0_0_10px_rgba(16,185,129,0.3)] flex items-center gap-1"
                                            >
                                              <DollarSign className="h-3.5 w-3.5" />
                                              Liquidar / Pagar
                                            </button>
                                          </>
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
                })
              )}
            </tbody>
          </table>
        </div>
      </GlassPanel>

      {/* MODAL: Novo Título a Pagar */}
      <AnimatePresence>
        {isCreateOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-800/40">
                <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <CreditCard className="h-5 w-5 text-[#00f0ff]" />
                  Novo Título a Pagar
                </h3>
                <button
                  onClick={() => setIsCreateOpen(false)}
                  className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleCreateSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Fornecedor */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Fornecedor *</label>
                    <select
                      required
                      value={formData.supplier_id}
                      onChange={(e) => setFormData({ ...formData, supplier_id: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                    >
                      <option value="">Selecione o Fornecedor...</option>
                      {suppliers.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.name} {s.tax_id ? `(${s.tax_id})` : ""}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Número do Documento / NF */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Nº Documento / NF-e</label>
                    <input
                      type="text"
                      placeholder="ex: NF 1284 ou FAT-889"
                      value={formData.document_number}
                      onChange={(e) => setFormData({ ...formData, document_number: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                    />
                  </div>
                </div>

                {/* Descrição */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Descrição da Despesa *</label>
                  <input
                    type="text"
                    required
                    placeholder="ex: Compra de Carnes e Laticínios da Semana"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Categoria Financeira (Plano de Contas) */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Plano de Contas (Categoria)</label>
                    <select
                      value={formData.category_id}
                      onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                    >
                      <option value="">Selecione a categoria...</option>
                      {categories.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.code ? `${c.code} - ` : ""}{c.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Centro de Custo */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Centro de Custo</label>
                    <select
                      value={formData.cost_center_id}
                      onChange={(e) => setFormData({ ...formData, cost_center_id: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                    >
                      <option value="">Selecione o centro de custo...</option>
                      {costCenters.map((cc) => (
                        <option key={cc.id} value={cc.id}>
                          {cc.code ? `[${cc.code}] ` : ""}{cc.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Valor Total */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Valor Total (R$) *</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      placeholder="0.00"
                      value={formData.total_amount}
                      onChange={(e) => setFormData({ ...formData, total_amount: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none font-mono"
                    />
                  </div>

                  {/* 1º Vencimento */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">1º Vencimento *</label>
                    <input
                      type="date"
                      required
                      value={formData.first_due_date}
                      onChange={(e) => setFormData({ ...formData, first_due_date: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                    />
                  </div>

                  {/* Parcelamento */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Nº de Parcelas</label>
                    <select
                      value={formData.installment_count}
                      onChange={(e) => setFormData({ ...formData, installment_count: parseInt(e.target.value) })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                    >
                      <option value="1">1x (À vista / 30d)</option>
                      <option value="2">2x (30/60d)</option>
                      <option value="3">3x (30/60/90d)</option>
                      <option value="4">4x (30/60/90/120d)</option>
                      <option value="6">6x</option>
                      <option value="12">12x</option>
                    </select>
                  </div>
                </div>

                {/* PIX e Boleto */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Chave / Código PIX Copia e Cola</label>
                    <input
                      type="text"
                      placeholder="00020126580014br.gov.bcb.pix..."
                      value={formData.pix_code}
                      onChange={(e) => setFormData({ ...formData, pix_code: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-xs focus:border-[#00f0ff] outline-none font-mono"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Linha Digitável do Boleto</label>
                    <input
                      type="text"
                      placeholder="34191.79001 01043.510047..."
                      value={formData.barcode}
                      onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-xs focus:border-[#00f0ff] outline-none font-mono"
                    />
                  </div>
                </div>

                {/* Observações */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Observações / Anotações</label>
                  <textarea
                    rows={2}
                    placeholder="Informações adicionais, detalhes de negociação, etc."
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(false)}
                    className="px-4 py-2.5 rounded-xl text-slate-400 hover:text-white font-medium"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-[#00f0ff] hover:bg-[#00f0ff]/90 text-slate-950 px-6 py-2.5 rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(0,240,255,0.3)] disabled:opacity-50"
                  >
                    {isSubmitting ? "Cadastrando..." : "Cadastrar Título"}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* MODAL: Baixa / Liquidação de Parcela */}
      <AnimatePresence>
        {settleModal.isOpen && settleModal.installment && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-800/40">
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                  Liquidar Parcela ({settleModal.installment.installment_number}/{settleModal.installment.total_installments})
                </h3>
                <button
                  onClick={() => setSettleModal({ isOpen: false, installment: null, bill: null })}
                  className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleSettleSubmit} className="p-6 space-y-4">
                <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800">
                  <span className="text-xs text-slate-400 block">Fornecedor / Título</span>
                  <span className="text-sm font-bold text-slate-200 block">{settleModal.bill?.supplier_name}</span>
                  <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-800 text-xs">
                    <span className="text-slate-400">Valor Nominal da Parcela:</span>
                    <span className="font-bold text-slate-100">{formatCurrency(settleModal.installment.amount)}</span>
                  </div>
                </div>

                {/* Conta Bancária Debitada */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Conta de Saída (Débito) *</label>
                  <select
                    required
                    value={settleForm.bank_account_id}
                    onChange={(e) => setSettleForm({ ...settleForm, bank_account_id: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-emerald-400 outline-none"
                  >
                    <option value="">Selecione a conta de saída...</option>
                    {bankAccounts.map((ba) => (
                      <option key={ba.id} value={ba.id}>
                        {ba.name} (Saldo: {formatCurrency(ba.current_balance)})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Forma de Pagamento */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Forma de Pagamento</label>
                    <select
                      value={settleForm.payment_method}
                      onChange={(e) => setSettleForm({ ...settleForm, payment_method: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-emerald-400 outline-none"
                    >
                      <option value="PIX">PIX</option>
                      <option value="BOLETO">Boleto Bancário</option>
                      <option value="TRANSFER">Transferência TED</option>
                      <option value="CREDIT_CARD">Cartão Corporativo</option>
                      <option value="CASH">Dinheiro / Caixa</option>
                    </select>
                  </div>

                  {/* Data do Pagamento */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Data do Pagamento</label>
                    <input
                      type="date"
                      required
                      value={settleForm.settlement_date}
                      onChange={(e) => setSettleForm({ ...settleForm, settlement_date: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-emerald-400 outline-none"
                    />
                  </div>
                </div>

                {/* Juros, Multa, Desconto */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-400 uppercase">Juros (R$)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={settleForm.interest_amount}
                      onChange={(e) => setSettleForm({ ...settleForm, interest_amount: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-400 uppercase">Multa (R$)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={settleForm.fine_amount}
                      onChange={(e) => setSettleForm({ ...settleForm, fine_amount: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-emerald-400 uppercase">Desconto (R$)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={settleForm.discount_amount}
                      onChange={(e) => setSettleForm({ ...settleForm, discount_amount: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-emerald-400 text-xs font-mono"
                    />
                  </div>
                </div>

                {/* Código de Autenticação */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Autenticação Bancária / Hash</label>
                  <input
                    type="text"
                    placeholder="ex: E1234567820260816... ou Comprovante 4492"
                    value={settleForm.transaction_reference}
                    onChange={(e) => setSettleForm({ ...settleForm, transaction_reference: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-slate-100 text-xs focus:border-emerald-400 outline-none font-mono"
                  />
                </div>

                {/* Total Liquidado Footer */}
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-between">
                  <span className="text-xs text-emerald-300 font-semibold uppercase">Total Liquidado:</span>
                  <span className="text-xl font-bold text-emerald-400 tabular-nums">
                    {formatCurrency(totalSettlementValue)}
                  </span>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setSettleModal({ isOpen: false, installment: null, bill: null })}
                    className="px-4 py-2 text-slate-400 hover:text-white text-sm"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-6 py-2.5 rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(16,185,129,0.4)] disabled:opacity-50 text-sm"
                  >
                    {isSubmitting ? "Liquidando..." : "Confirmar Pagamento"}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
