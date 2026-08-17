"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Landmark, Plus, Wallet, CreditCard, Banknote, X, Check } from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { BankAccount } from "@/types/financial"
import { createBankAccount } from "@/lib/api-client"

interface BankAccountsClientProps {
  initialAccounts: BankAccount[]
}

export default function BankAccountsClient({ initialAccounts }: BankAccountsClientProps) {
  const router = useRouter()
  const [accounts, setAccounts] = useState<BankAccount[]>(initialAccounts)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [form, setForm] = useState({
    name: "",
    account_type: "CHECKING",
    bank_code: "",
    agency_number: "",
    account_number: "",
    pix_key: "",
    initial_balance: "0.00"
  })

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val || 0)
  }

  const totalBalance = accounts.reduce((acc, curr) => acc + Number(curr.current_balance || 0), 0)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name) return

    setIsSubmitting(true)
    const created = await createBankAccount({
      name: form.name,
      account_type: form.account_type,
      bank_code: form.bank_code || undefined,
      agency_number: form.agency_number || undefined,
      account_number: form.account_number || undefined,
      pix_key: form.pix_key || undefined,
      initial_balance: parseFloat(form.initial_balance) || 0
    })
    setIsSubmitting(false)

    if (created) {
      setIsCreateOpen(false)
      setForm({
        name: "",
        account_type: "CHECKING",
        bank_code: "",
        agency_number: "",
        account_number: "",
        pix_key: "",
        initial_balance: "0.00"
      })
      router.refresh()
    } else {
      alert("Erro ao criar conta bancária.")
    }
  }

  const getAccountIcon = (type: string) => {
    switch (type) {
      case "CASH": return <Banknote className="h-6 w-6 text-amber-400" />
      case "SAVINGS": return <Wallet className="h-6 w-6 text-purple-400" />
      case "DIGITAL_WALLET": return <CreditCard className="h-6 w-6 text-emerald-400" />
      default: return <Landmark className="h-6 w-6 text-[#00f0ff]" />
    }
  }

  const getAccountBadge = (type: string) => {
    switch (type) {
      case "CASH": return <Badge variant="amber">Caixa Físico</Badge>
      case "SAVINGS": return <Badge variant="violet">Poupança / Reserva</Badge>
      case "DIGITAL_WALLET": return <Badge variant="emerald">Carteira Digital</Badge>
      default: return <Badge variant="cyan">Conta Corrente</Badge>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
              <Landmark className="h-8 w-8 text-[#00f0ff]" />
              Contas Bancárias & Caixas
            </h2>
            <span className="rounded-full bg-[#00f0ff]/10 px-3 py-1 text-xs font-semibold text-[#00f0ff] border border-[#00f0ff]/30">
              Pilar 1 • Tesouraria
            </span>
          </div>
          <p className="text-slate-400 mt-1">
            Gestão de saldos de contas bancárias, gavetas de caixa e liquidações do restaurante.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="bg-[#00f0ff] hover:bg-[#00f0ff]/90 text-slate-950 px-5 py-2.5 rounded-xl font-bold shadow-[0_0_20px_rgba(0,240,255,0.3)] hover:shadow-[0_0_30px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Nova Conta / Caixa
        </button>
      </div>

      {/* Overview Balance Banner */}
      <GlassPanel accent="cyan" className="p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Saldo Total Consolidado (Disponível)
            </span>
            <div className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight mt-1 tabular-nums">
              {formatCurrency(totalBalance)}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Soma de todas as contas ativas do restaurante
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-400 font-mono bg-slate-950/60 px-4 py-2 rounded-xl border border-slate-800">
            <span>{accounts.length} Contas / Caixas Ativos</span>
          </div>
        </div>
      </GlassPanel>

      {/* Bank Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map((acc) => (
          <GlassPanel key={acc.id} className="p-6 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-all">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700">
                  {getAccountIcon(acc.account_type)}
                </div>
                <div>
                  <h3 className="font-bold text-slate-100 text-base">{acc.name}</h3>
                  <div className="mt-1">{getAccountBadge(acc.account_type)}</div>
                </div>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs text-slate-400">
              {acc.agency_number && acc.account_number && (
                <div className="flex justify-between">
                  <span>Ag / Conta:</span>
                  <span className="font-mono text-slate-200">{acc.agency_number} / {acc.account_number}</span>
                </div>
              )}
              {acc.pix_key && (
                <div className="flex justify-between">
                  <span>Chave PIX:</span>
                  <span className="font-mono text-purple-300 truncate max-w-[180px]">{acc.pix_key}</span>
                </div>
              )}
            </div>

            {/* Balance */}
            <div className="pt-3 border-t border-slate-800 flex items-baseline justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase">Saldo Atual</span>
              <span className="text-xl font-bold text-emerald-400 tabular-nums">
                {formatCurrency(acc.current_balance)}
              </span>
            </div>
          </GlassPanel>
        ))}
      </div>

      {/* Modal: Nova Conta */}
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
              className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-800/40">
                <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <Landmark className="h-5 w-5 text-[#00f0ff]" />
                  Nova Conta ou Caixa
                </h3>
                <button
                  onClick={() => setIsCreateOpen(false)}
                  className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Nome da Conta / Caixa *</label>
                  <input
                    type="text"
                    required
                    placeholder="ex: Banco Itaú - Principal ou Caixa Gaveta"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Tipo</label>
                    <select
                      value={form.account_type}
                      onChange={(e) => setForm({ ...form, account_type: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none"
                    >
                      <option value="CHECKING">Conta Corrente</option>
                      <option value="CASH">Caixa Físico / Gaveta</option>
                      <option value="SAVINGS">Poupança / Reserva</option>
                      <option value="DIGITAL_WALLET">Carteira Digital</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Saldo Inicial (R$)</label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={form.initial_balance}
                      onChange={(e) => setForm({ ...form, initial_balance: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:border-[#00f0ff] outline-none font-mono"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-400 uppercase">Cód. Banco</label>
                    <input
                      type="text"
                      placeholder="ex: 341"
                      value={form.bank_code}
                      onChange={(e) => setForm({ ...form, bank_code: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-400 uppercase">Agência</label>
                    <input
                      type="text"
                      placeholder="ex: 1234"
                      value={form.agency_number}
                      onChange={(e) => setForm({ ...form, agency_number: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-xs font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[11px] font-semibold text-slate-400 uppercase">Conta</label>
                    <input
                      type="text"
                      placeholder="ex: 56789-0"
                      value={form.account_number}
                      onChange={(e) => setForm({ ...form, account_number: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-xs font-mono"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Chave PIX (Opcional)</label>
                  <input
                    type="text"
                    placeholder="CNPJ, E-mail, Telefone ou Chave Aleatória"
                    value={form.pix_key}
                    onChange={(e) => setForm({ ...form, pix_key: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 text-xs focus:border-[#00f0ff] outline-none font-mono"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(false)}
                    className="px-4 py-2 text-slate-400 hover:text-white text-sm"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-[#00f0ff] hover:bg-[#00f0ff]/90 text-slate-950 px-6 py-2.5 rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(0,240,255,0.3)] disabled:opacity-50 text-sm"
                  >
                    {isSubmitting ? "Criando..." : "Criar Conta"}
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
