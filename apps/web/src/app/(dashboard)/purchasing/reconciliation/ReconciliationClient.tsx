"use client"

import { useState, useEffect, useMemo } from "react"
import { ShieldCheck, RefreshCcw, TrendingUp, TrendingDown, CheckCircle2, AlertTriangle, AlertCircle, Ban, ArrowRight } from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { PurchaseOrderItem, EnrichedReconResponse } from "@/types/purchase-orders"
import { fetchPOReconciliations } from "@/lib/api-client"

export default function ReconciliationClient({ 
  activePOs 
}: { 
  activePOs: PurchaseOrderItem[]
}) {
  const [selectedPO, setSelectedPO] = useState<string>("")
  const [reconData, setReconData] = useState<EnrichedReconResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [filter, setFilter] = useState<string>("ALL")

  useEffect(() => {
    if (!selectedPO) {
      setReconData([])
      return
    }

    const loadData = async () => {
      setIsLoading(true)
      const data = await fetchPOReconciliations(selectedPO)
      setReconData(data)
      setIsLoading(false)
    }
    loadData()
  }, [selectedPO])

  const filteredData = reconData.filter(item => {
    if (filter === "ALL") return true
    if (filter === "MATCHED") return item.status === "MATCHED"
    if (filter === "DIVERGENCE") return item.status !== "MATCHED" && item.status !== "UNMATCHED"
    return true
  })

  // Calculando Totalizadores
  const totals = useMemo(() => {
    let poTotal = 0
    let receivedTotal = 0
    let invoicedTotal = 0

    reconData.forEach(item => {
      poTotal += (item.ordered_qty || 0) * (item.ordered_price || 0)
      receivedTotal += (item.received_qty || 0) * (item.received_price || 0)
      invoicedTotal += (item.invoiced_qty || 0) * (item.invoiced_price || 0)
    })

    const deltaValue = invoicedTotal - poTotal
    const deltaPercentage = poTotal > 0 ? (deltaValue / poTotal) * 100 : 0
    const hasCriticalDivergence = deltaPercentage > 5 // Mais de 5% a mais do valor orçado

    return { poTotal, receivedTotal, invoicedTotal, deltaValue, deltaPercentage, hasCriticalDivergence }
  }, [reconData])

  const formatCurrency = (val: number | null) => {
    if (val === null) return "-"
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "MATCHED":
        return <Badge className="bg-[#10b981]/20 text-[#10b981] border-[#10b981]/30"><CheckCircle2 className="h-3 w-3 mr-1" /> CONFORME</Badge>
      case "QUANTITY_DISCREPANCY":
        return <Badge className="bg-[#f59e0b]/20 text-[#f59e0b] border-[#f59e0b]/30"><AlertTriangle className="h-3 w-3 mr-1" /> QTD INVÁLIDA</Badge>
      case "PRICE_DISCREPANCY":
        return <Badge className="bg-[#ef4444]/20 text-[#ef4444] border-[#ef4444]/30"><AlertCircle className="h-3 w-3 mr-1" /> VAR. PREÇO</Badge>
      default:
        return <Badge className="bg-slate-700/50 text-slate-400">AGUARDANDO</Badge>
    }
  }

  return (
    <div className="space-y-6 pb-24">
      {/* HEADER PRINCIPAL */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <ShieldCheck className="h-8 w-8 text-[#a855f7]" />
            Painel de Auditoria 3-Way
          </h2>
          <p className="text-slate-400 mt-1">
            Compare o funil de aquisição: Pedido de Compra ➔ Recebimento Físico ➔ Faturamento (NF-e).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* SIDEBAR - POs Ativos */}
        <GlassPanel className="lg:col-span-1 flex flex-col h-full min-h-[400px]">
          <h3 className="text-lg font-bold text-slate-100 mb-4 flex items-center justify-between">
            Pedidos Ativos
            <Badge variant="violet">{activePOs.length}</Badge>
          </h3>
          <div className="flex-1 overflow-y-auto space-y-2 pr-2">
            {activePOs.map(po => (
              <button
                key={po.id}
                onClick={() => setSelectedPO(po.id)}
                className={`w-full text-left p-4 rounded-xl transition-all border ${
                  selectedPO === po.id 
                    ? "bg-[#a855f7]/10 border-[#a855f7]/50 shadow-[0_0_15px_rgba(168,85,247,0.15)]" 
                    : "bg-slate-900/50 border-slate-800 hover:bg-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm text-[#a855f7] font-bold">#{po.id.slice(0, 8)}</span>
                  <Badge variant="default" className="text-[10px]">{po.status}</Badge>
                </div>
                <div className="mt-2 text-sm text-slate-300 flex items-center justify-between">
                  <span>{new Date(po.order_date).toLocaleDateString("pt-BR")}</span>
                </div>
              </button>
            ))}
            {activePOs.length === 0 && (
              <p className="text-sm text-slate-500 text-center py-8">Nenhum pedido ativo encontrado.</p>
            )}
          </div>
        </GlassPanel>

        {/* MAIN RECONCILIATION AREA */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          {!selectedPO ? (
            <GlassPanel className="flex-1 flex flex-col items-center justify-center p-12 text-slate-500 min-h-[400px]">
              <div className="h-24 w-24 rounded-full bg-slate-800/50 flex items-center justify-center mb-6">
                <ShieldCheck className="h-12 w-12 text-slate-600" />
              </div>
              <h3 className="text-xl font-bold text-slate-300 mb-2">Nenhum Pedido Selecionado</h3>
              <p>Selecione um Pedido de Compra na barra lateral para iniciar a auditoria financeira.</p>
            </GlassPanel>
          ) : (
            <>
              {/* DASHBOARD DE TOTALIZADORES */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <GlassPanel className="p-4 border-l-4 border-l-[#00f0ff] flex flex-col justify-center">
                  <span className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">1. Orçado no PO</span>
                  <span className="text-2xl font-bold text-slate-100">{formatCurrency(totals.poTotal)}</span>
                </GlassPanel>
                
                <GlassPanel className="p-4 border-l-4 border-l-[#f59e0b] flex flex-col justify-center">
                  <span className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">2. Recebido Físico</span>
                  <span className="text-2xl font-bold text-slate-100">{formatCurrency(totals.receivedTotal)}</span>
                </GlassPanel>
                
                <GlassPanel className="p-4 border-l-4 border-l-[#a855f7] flex flex-col justify-center">
                  <span className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">3. Faturado na NF-e</span>
                  <span className="text-2xl font-bold text-slate-100">{formatCurrency(totals.invoicedTotal)}</span>
                </GlassPanel>
                
                <GlassPanel className={`p-4 border-l-4 flex flex-col justify-center ${
                  totals.deltaValue > 0 ? 'border-l-red-500 bg-red-500/5' : 
                  totals.deltaValue < 0 ? 'border-l-emerald-500 bg-emerald-500/5' : 
                  'border-l-slate-600'
                }`}>
                  <span className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Impacto Financeiro</span>
                  <div className="flex items-center gap-2">
                    <span className={`text-2xl font-bold ${
                      totals.deltaValue > 0 ? 'text-red-400' : 
                      totals.deltaValue < 0 ? 'text-emerald-400' : 'text-slate-100'
                    }`}>
                      {totals.deltaValue > 0 && '+'}{formatCurrency(totals.deltaValue)}
                    </span>
                  </div>
                </GlassPanel>
              </div>

              {/* TABELA DE RECONCILIAÇÃO DETALHADA */}
              <GlassPanel className="p-0 overflow-hidden flex flex-col shadow-2xl">
                <div className="p-5 border-b border-slate-700/50 bg-slate-800/20 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <button onClick={() => setFilter("ALL")} className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${filter === "ALL" ? "bg-slate-700 text-white shadow-md" : "bg-slate-900/50 text-slate-400 hover:text-slate-200"}`}>Todos</button>
                    <button onClick={() => setFilter("MATCHED")} className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${filter === "MATCHED" ? "bg-[#10b981]/20 text-[#10b981] border border-[#10b981]/30 shadow-md" : "bg-slate-900/50 text-slate-400 hover:text-slate-200"}`}>Conformes</button>
                    <button onClick={() => setFilter("DIVERGENCE")} className={`px-4 py-2 rounded-lg text-sm font-bold transition-colors ${filter === "DIVERGENCE" ? "bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30 shadow-md" : "bg-slate-900/50 text-slate-400 hover:text-slate-200"}`}>Com Divergência</button>
                  </div>
                  
                  {/* Action Buttons based on Divergence */}
                  <div className="flex items-center gap-3">
                    {isLoading && <RefreshCcw className="h-5 w-5 text-slate-500 animate-spin" />}
                    
                    {!isLoading && totals.poTotal > 0 && (
                      totals.hasCriticalDivergence ? (
                        <button className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-lg transition-all flex items-center gap-2">
                          <Ban className="h-4 w-4" />
                          Bloquear Pagamento
                        </button>
                      ) : (
                        <button className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-lg transition-all flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4" />
                          Aprovar c/ Ressalvas
                        </button>
                      )
                    )}
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm whitespace-nowrap min-w-[1000px]">
                    <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-700/80 uppercase text-[10px] tracking-wider font-bold">
                      <tr>
                        <th className="px-5 py-4">SKU / Insumo</th>
                        <th className="px-5 py-4 text-center border-l border-slate-700/30 bg-[#00f0ff]/5">1. Pedido Aprovado (PO)</th>
                        <th className="px-5 py-4 text-center border-l border-slate-700/30 bg-[#f59e0b]/5">2. Recebimento Físico</th>
                        <th className="px-5 py-4 text-center border-l border-slate-700/30 bg-[#a855f7]/5">3. Nota Fiscal Faturada</th>
                        <th className="px-5 py-4 text-right border-l border-slate-700/30">Auditoria Automática</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40 text-slate-300">
                      {filteredData.map(row => {
                        const hasQtyIssue = row.received_qty !== null && row.received_qty !== row.ordered_qty;
                        const hasPriceIssue = row.invoiced_price !== null && row.invoiced_price !== row.ordered_price;
                        
                        const qtyDelta = row.received_qty !== null ? row.received_qty - row.ordered_qty : 0;
                        const priceDelta = row.invoiced_price !== null ? row.invoiced_price - row.ordered_price : 0;

                        return (
                          <tr key={row.id} className="hover:bg-slate-800/40 transition-colors group">
                            <td className="px-5 py-4">
                              <div className="font-bold text-slate-100 text-base">{row.sku_name}</div>
                              <div className="text-xs text-slate-500 uppercase">{row.uom_symbol}</div>
                            </td>
                            
                            <td className="px-5 py-4 border-l border-slate-700/30 bg-[#00f0ff]/5 text-center">
                              <div className="font-mono text-lg text-white">{row.ordered_qty}</div>
                              <div className="text-xs text-[#00f0ff]/70 font-mono mt-1">{formatCurrency(row.ordered_price)} / un</div>
                            </td>
                            
                            <td className={`px-5 py-4 border-l border-slate-700/30 bg-[#f59e0b]/5 text-center relative ${hasQtyIssue ? 'bg-[#f59e0b]/10' : ''}`}>
                              <ArrowRight className="absolute -left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-600 hidden lg:block" />
                              <div className="flex flex-col items-center justify-center gap-1">
                                <div className="flex items-center gap-2">
                                  <span className={`font-mono text-lg ${hasQtyIssue ? 'text-white' : 'text-slate-300'}`}>{row.received_qty !== null ? row.received_qty : "-"}</span>
                                  {hasQtyIssue && (
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded-sm font-bold ${qtyDelta < 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                                      {qtyDelta > 0 ? '+' : ''}{qtyDelta}
                                    </span>
                                  )}
                                </div>
                                <div className="text-xs text-[#f59e0b]/70 font-mono">{formatCurrency(row.received_price)} / un</div>
                              </div>
                            </td>
                            
                            <td className={`px-5 py-4 border-l border-slate-700/30 bg-[#a855f7]/5 text-center relative ${hasPriceIssue ? 'bg-[#ef4444]/10' : ''}`}>
                              <ArrowRight className="absolute -left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-600 hidden lg:block" />
                              <div className="flex flex-col items-center justify-center gap-1">
                                <span className={`font-mono text-lg ${hasPriceIssue ? 'text-white' : 'text-slate-300'}`}>{row.invoiced_qty !== null ? row.invoiced_qty : "-"}</span>
                                <div className="flex items-center gap-2">
                                  <span className={`text-xs font-mono ${hasPriceIssue ? 'text-white' : 'text-[#a855f7]/70'}`}>{formatCurrency(row.invoiced_price)} / un</span>
                                  {hasPriceIssue && (
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded-sm font-bold ${priceDelta > 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                                      {priceDelta > 0 && '+'}{formatCurrency(priceDelta)}
                                    </span>
                                  )}
                                </div>
                              </div>
                            </td>

                            <td className="px-5 py-4 border-l border-slate-700/30 text-right">
                              {getStatusBadge(row.status)}
                            </td>
                          </tr>
                        )
                      })}
                      {filteredData.length === 0 && !isLoading && (
                        <tr>
                          <td colSpan={5} className="px-5 py-12 text-center text-slate-500">
                            <ShieldCheck className="h-10 w-10 mx-auto mb-3 opacity-20" />
                            Nenhum registro encontrado para este filtro.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </GlassPanel>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
