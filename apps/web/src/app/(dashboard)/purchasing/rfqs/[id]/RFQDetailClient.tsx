"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { motion, AnimatePresence } from "framer-motion"
import { 
  ArrowLeft, Scale, Building2, Calendar, CheckCircle2, Clock, 
  AlertCircle, DollarSign, Sparkles, Truck, FileText, Send, 
  ShoppingBag, Check, Plus, Users, ArrowUpRight, Award, ShieldCheck
} from "lucide-react"
import { 
  submitRFQProposalClient, 
  awardRFQClient, 
  addRFQSuppliersClient,
  fetchRFQComparisonClient 
} from "@/lib/api-client"

interface RFQDetailClientProps {
  rfq: any
  initialComparison: any
  allSuppliers: any[]
}

export function RFQDetailClient({ rfq: initialRfq, initialComparison, allSuppliers }: RFQDetailClientProps) {
  const router = useRouter()
  const [rfq, setRfq] = React.useState(initialRfq)
  const [comparison, setComparison] = React.useState(initialComparison)
  const [activeTab, setActiveTab] = React.useState<"matrix" | "proposals" | "items">("matrix")

  // Modal Proposal State
  const [selectedSupplierForProposal, setSelectedSupplierForProposal] = React.useState<string>(
    rfq.suppliers[0]?.supplier_id || ""
  )
  const [freightCost, setFreightCost] = React.useState("0.00")
  const [deliveryDays, setDeliveryDays] = React.useState("2")
  const [paymentTerms, setPaymentTerms] = React.useState("30 DDL")
  const [minOrderValue, setMinOrderValue] = React.useState("0.00")
  const [proposalNotes, setProposalNotes] = React.useState("")
  const [proposalPrices, setProposalPrices] = React.useState<{ [key: string]: string }>({})

  const [isSubmittingProposal, setIsSubmittingProposal] = React.useState(false)
  const [isAwarding, setIsAwarding] = React.useState(false)
  const [awardSuccess, setAwardSuccess] = React.useState<any | null>(null)
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)

  // Quick refresh comparison
  const reloadComparison = async () => {
    try {
      const comp = await fetchRFQComparisonClient(rfq.id)
      if (comp) setComparison(comp)
    } catch (err) {
      console.error(err)
    }
  }

  const handlePriceChange = (rfqItemId: string, price: string) => {
    setProposalPrices(prev => ({ ...prev, [rfqItemId]: price }))
  }

  const handleSubmitProposal = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedSupplierForProposal) {
      alert("Selecione um fornecedor.")
      return
    }

    setIsSubmittingProposal(true)
    setErrorMsg(null)

    try {
      const itemPrices = Object.entries(proposalPrices)
        .filter(([_, price]) => price && parseFloat(price) > 0)
        .map(([rfqItemId, price]) => ({
          rfq_item_id: rfqItemId,
          unit_price: parseFloat(price)
        }))

      if (itemPrices.length === 0) {
        throw new Error("Preencha ao menos um preço unitário para os itens.")
      }

      await submitRFQProposalClient(rfq.id, {
        supplier_id: selectedSupplierForProposal,
        freight_cost: parseFloat(freightCost) || 0,
        delivery_days: deliveryDays || "0",
        payment_terms: paymentTerms || null,
        min_order_value: parseFloat(minOrderValue) || 0,
        notes: proposalNotes || null,
        item_prices: itemPrices
      })

      await reloadComparison()
      setActiveTab("matrix")
      router.refresh()
    } catch (err: any) {
      setErrorMsg(err.message || "Erro ao salvar proposta.")
    } finally {
      setIsSubmittingProposal(false)
    }
  }

  const handleAward = async (awardType: "SPLIT" | "SINGLE_SUPPLIER", supplierId?: string) => {
    if (!confirm(`Confirma a homologação da cotação com a geração automática dos Pedidos de Compra (${awardType === 'SPLIT' ? 'Compra Mista Otimizada' : 'Fornecedor Vencedor Único'})?`)) {
      return
    }

    setIsAwarding(true)
    setErrorMsg(null)
    try {
      const res = await awardRFQClient(rfq.id, {
        award_type: awardType,
        selected_supplier_id: supplierId || null
      })
      setAwardSuccess(res)
      setRfq((prev: any) => ({ ...prev, status: "AWARDED" }))
      await reloadComparison()
    } catch (err: any) {
      setErrorMsg(err.message || "Erro ao homologar cotação.")
    } finally {
      setIsAwarding(false)
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-20">
      {/* Back & Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-start gap-4">
          <Link
            href="/purchasing/rfqs"
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-all mt-1"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-[#00f0ff] font-bold bg-[#00f0ff]/10 px-2 py-0.5 rounded border border-[#00f0ff]/20">
                {rfq.rfq_number}
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                rfq.status === "AWARDED"
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                  : rfq.status === "EVALUATING"
                  ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                  : "bg-blue-500/10 text-blue-400 border-blue-500/30"
              }`}>
                {rfq.status}
              </span>
              {rfq.deadline && (
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" /> Prazo: {new Date(rfq.deadline).toLocaleDateString("pt-BR")}
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-slate-100">{rfq.title}</h1>
            {rfq.notes && (
              <p className="text-xs text-slate-400 mt-1 max-w-2xl">{rfq.notes}</p>
            )}
          </div>
        </div>

        {/* Action Header Button */}
        {rfq.status !== "AWARDED" && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab("proposals")}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all inline-flex items-center gap-2"
            >
              <DollarSign className="w-3.5 h-3.5 text-[#00f0ff]" />
              Lançar Preços de Fornecedor
            </button>
            <button
              disabled={isAwarding || !comparison || comparison.suppliers?.length === 0}
              onClick={() => handleAward("SPLIT")}
              className="px-4 py-2 bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 text-xs font-bold rounded-lg shadow-lg shadow-[#00f0ff]/20 hover:opacity-95 transition-all inline-flex items-center gap-2 disabled:opacity-50"
            >
              <Award className="w-3.5 h-3.5" />
              {isAwarding ? "Gerando POs..." : "Aprovar Compra Otimizada"}
            </button>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          {errorMsg}
        </div>
      )}

      {awardSuccess && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex flex-col gap-2"
        >
          <div className="flex items-center gap-2 font-bold text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
            Cotação Homologada com Sucesso!
          </div>
          <p className="text-xs text-slate-300">
            {awardSuccess.message} Foram gerados os pedidos com os fornecedores vencedores.
          </p>
          <div className="flex items-center gap-3 mt-1">
            <Link
              href="/purchase-orders"
              className="px-3.5 py-1.5 bg-emerald-500 text-slate-950 text-xs font-bold rounded-lg hover:bg-emerald-400 transition-colors inline-flex items-center gap-1.5"
            >
              Ver Pedidos de Compra (POs) <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </motion.div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800">
        <button
          onClick={() => setActiveTab("matrix")}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === "matrix"
              ? "border-[#00f0ff] text-[#00f0ff]"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Scale className="w-4 h-4" />
          Quadro Comparativo de Preços (Matrix)
        </button>
        <button
          onClick={() => setActiveTab("proposals")}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === "proposals"
              ? "border-[#00f0ff] text-[#00f0ff]"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <DollarSign className="w-4 h-4" />
          Lançamento de Propostas ({comparison?.suppliers?.length || 0})
        </button>
        <button
          onClick={() => setActiveTab("items")}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 flex items-center gap-2 ${
            activeTab === "items"
              ? "border-[#00f0ff] text-[#00f0ff]"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="w-4 h-4" />
          Itens Solicitados & Convites ({rfq.items?.length || 0})
        </button>
      </div>

      {/* TAB 1: COMPARISON MATRIX */}
      {activeTab === "matrix" && (
        <div className="space-y-6">
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <span className="text-[11px] font-mono text-slate-400">TOTAL ESTIMADO (SPLIT)</span>
              <p className="text-2xl font-bold text-slate-100 mt-1">
                R$ {Number(comparison?.split_order_total || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
              <span className="text-[10px] text-emerald-400 font-medium">Menor custo combinando fornecedores</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <span className="text-[11px] font-mono text-emerald-400">ECONOMIA ESTIMADA</span>
              <p className="text-2xl font-bold text-emerald-300 mt-1">
                R$ {Number(comparison?.potential_savings || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </p>
              <span className="text-[10px] text-slate-400">Comparado ao preço alvo/histórico</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <span className="text-[11px] font-mono text-blue-400">MELHOR FORNECEDOR GLOBAL</span>
              <p className="text-xl font-bold text-blue-300 mt-1 truncate">
                {comparison?.global_rankings?.[0]?.supplier_name || "Nenhum"}
              </p>
              <span className="text-[10px] text-slate-400">
                Total c/ frete: R$ {Number(comparison?.best_global_total || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl">
              <span className="text-[11px] font-mono text-amber-400">PROPOSTAS RECEBIDAS</span>
              <p className="text-2xl font-bold text-amber-300 mt-1">
                {comparison?.suppliers?.length || 0} / {rfq.suppliers?.length || 0}
              </p>
              <span className="text-[10px] text-slate-400">Fornecedores participando</span>
            </div>
          </div>

          {/* Matrix Table */}
          {comparison?.suppliers?.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 flex flex-col items-center justify-center">
              <Scale className="w-12 h-12 text-slate-600 mb-3" />
              <h3 className="text-base font-semibold text-slate-300">Nenhuma proposta cadastrada ainda</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Lance as cotações de preços recebidas por e-mail ou telefone para gerar o comparativo automatizado.
              </p>
              <button
                onClick={() => setActiveTab("proposals")}
                className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all inline-flex items-center gap-2"
              >
                <Plus className="w-3.5 h-3.5" /> Lançar Preços de Fornecedores
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/80">
                    <th className="p-4 font-mono text-slate-400 uppercase">Item / Insumo</th>
                    <th className="p-4 font-mono text-slate-400 uppercase">Qtd</th>
                    <th className="p-4 font-mono text-slate-400 uppercase">Preço Alvo</th>
                    {comparison?.suppliers?.map((s: any) => (
                      <th key={s.supplier_id} className="p-4 font-bold text-slate-200 uppercase min-w-[180px]">
                        <div className="flex flex-col">
                          <span>{s.supplier_name}</span>
                          <span className="text-[10px] font-mono text-[#00f0ff] font-normal">
                            Prazo: {s.delivery_days} dias | Frete: R$ {Number(s.freight_cost).toFixed(2)}
                          </span>
                        </div>
                      </th>
                    ))}
                    <th className="p-4 font-mono text-emerald-400 uppercase text-right">Melhor Preço</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {comparison?.items?.map((item: any) => (
                    <tr key={item.rfq_item_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-4 font-medium text-slate-200">
                        {item.sku_name}
                      </td>
                      <td className="p-4 font-mono text-slate-300">
                        {Number(item.quantity).toLocaleString("pt-BR")} {item.uom_symbol}
                      </td>
                      <td className="p-4 font-mono text-slate-400">
                        {item.target_price ? `R$ ${Number(item.target_price).toFixed(2)}` : "-"}
                      </td>

                      {/* Supplier Quotes */}
                      {item.quotes.map((q: any) => {
                        const isBest = q.unit_price !== null && Number(q.unit_price) === Number(item.best_price)
                        return (
                          <td key={q.supplier_id} className="p-4 font-mono">
                            {q.unit_price !== null ? (
                              <div className="space-y-1">
                                <div className="flex items-center gap-1.5">
                                  <span className={`text-sm font-bold ${isBest ? "text-emerald-400" : "text-slate-300"}`}>
                                    R$ {Number(q.unit_price).toFixed(2)}
                                  </span>
                                  {isBest && (
                                    <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                      MENOR
                                    </span>
                                  )}
                                </div>
                                <div className="text-[10px] text-slate-500">
                                  Total: R$ {Number(q.total_price).toFixed(2)}
                                </div>
                                {q.brand_or_spec && (
                                  <div className="text-[10px] text-slate-400 italic">
                                    {q.brand_or_spec}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-slate-600">-</span>
                            )}
                          </td>
                        )
                      })}

                      <td className="p-4 font-mono text-right font-bold text-emerald-400">
                        {item.best_price ? (
                          <div>
                            <div>R$ {Number(item.best_price).toFixed(2)}</div>
                            <div className="text-[10px] text-slate-400 font-normal truncate max-w-[120px] ml-auto">
                              {item.best_supplier_name}
                            </div>
                          </div>
                        ) : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>

                {/* Footer Totals */}
                <tfoot>
                  <tr className="border-t-2 border-slate-800 bg-slate-950/90 font-mono">
                    <td colSpan={3} className="p-4 font-bold text-slate-300">
                      TOTAL FORNECEDOR (C/ FRETE):
                    </td>
                    {comparison?.global_rankings?.map((r: any) => (
                      <td key={r.supplier_id} className="p-4">
                        <div className="text-base font-bold text-slate-100">
                          R$ {Number(r.total_with_freight).toFixed(2)}
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Condição: {r.payment_terms || "À vista"}
                        </div>
                        {rfq.status !== "AWARDED" && (
                          <button
                            onClick={() => handleAward("SINGLE_SUPPLIER", r.supplier_id)}
                            className="mt-2 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[10px] font-bold text-slate-200 border border-slate-700 transition-all w-full text-center block"
                          >
                            Comprar Só Deste
                          </button>
                        )}
                      </td>
                    ))}
                    <td className="p-4 text-right">
                      <div className="text-base font-bold text-emerald-400">
                        R$ {Number(comparison?.split_order_total || 0).toFixed(2)}
                      </div>
                      <div className="text-[10px] text-emerald-500 font-bold">
                        Melhor Combinação
                      </div>
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: PROPOSAL ENTRY */}
      {activeTab === "proposals" && (
        <form onSubmit={handleSubmitProposal} className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-6">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-[#00f0ff]" />
              Registrar / Atualizar Proposta de Fornecedor
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Informe os preços e condições ofertadas pelo parceiro comercial para esta cotação.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Fornecedor *</label>
              <select
                value={selectedSupplierForProposal}
                onChange={(e) => setSelectedSupplierForProposal(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
              >
                {allSuppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Frete (R$)</label>
              <input
                type="number"
                step="0.01"
                value={freightCost}
                onChange={(e) => setFreightCost(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Prazo de Entrega (Dias)</label>
              <input
                type="number"
                value={deliveryDays}
                onChange={(e) => setDeliveryDays(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Condições de Pagamento</label>
              <input
                type="text"
                placeholder="Ex: 28 DDL Boleto, À vista PIX"
                value={paymentTerms}
                onChange={(e) => setPaymentTerms(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
              />
            </div>
          </div>

          {/* Item Prices */}
          <div className="space-y-3 pt-2">
            <h3 className="text-xs font-mono uppercase text-slate-300">Preços Unitários por Item</h3>
            <div className="grid grid-cols-1 gap-2">
              {rfq.items?.map((item: any) => (
                <div key={item.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div>
                    <p className="text-xs font-bold text-slate-100">{item.sku_name}</p>
                    <p className="text-[10px] text-slate-400 font-mono">
                      Qtd Solicitada: {Number(item.quantity).toLocaleString("pt-BR")} {item.uom_symbol}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">R$ / un:</span>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={proposalPrices[item.id] || ""}
                      onChange={(e) => handlePriceChange(item.id, e.target.value)}
                      className="w-32 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs font-mono text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={isSubmittingProposal}
              className="px-5 py-2 rounded-lg bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-bold text-xs shadow-lg shadow-[#00f0ff]/20 hover:opacity-95 transition-all inline-flex items-center gap-2"
            >
              <Send className="w-3.5 h-3.5" />
              {isSubmittingProposal ? "Salvando..." : "Salvar Proposta & Atualizar Matriz"}
            </button>
          </div>
        </form>
      )}

      {/* TAB 3: REQUESTED ITEMS & SUPPLIERS */}
      {activeTab === "items" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Items */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#00f0ff]" />
              Itens da Cotação ({rfq.items?.length || 0})
            </h3>
            <div className="space-y-2">
              {rfq.items?.map((i: any) => (
                <div key={i.id} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <p className="font-bold text-slate-200">{i.sku_name}</p>
                    <p className="text-[10px] text-slate-500 font-mono">
                      Qtd: {Number(i.quantity).toLocaleString("pt-BR")} {i.uom_symbol}
                    </p>
                  </div>
                  {i.target_price && (
                    <span className="font-mono text-slate-400">
                      Alvo: R$ {Number(i.target_price).toFixed(2)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Invited Suppliers */}
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Users className="w-4 h-4 text-[#00f0ff]" />
              Fornecedores Convidados ({rfq.suppliers?.length || 0})
            </h3>
            <div className="space-y-2">
              {rfq.suppliers?.map((s: any) => (
                <div key={s.id} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-200">{s.supplier_name}</span>
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    {s.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
