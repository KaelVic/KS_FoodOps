"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { ShoppingCart, ArrowLeft, Truck, FileCheck, CheckCircle, AlertTriangle } from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { PurchaseOrderDetail, EnrichedReconResponse } from "@/types/purchase-orders"
import { CatalogSkusAndUoms } from "@/types/recipes"
import { fetchPOReconciliations, receivePurchaseOrder, invoicePurchaseOrder } from "@/lib/api-client"

export default function PODetailClient({ 
  initialDetail, 
  catalog 
}: { 
  initialDetail: PurchaseOrderDetail
  catalog: CatalogSkusAndUoms
}) {
  const router = useRouter()
  const [po] = useState(initialDetail)
  const [reconData, setReconData] = useState<EnrichedReconResponse[]>([])
  const [activeTab, setActiveTab] = useState<"ORDER" | "RECEIVE" | "INVOICE" | "RECON">("ORDER")
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Quick inputs for mock receipt/invoice
  const [receiptQty, setReceiptQty] = useState<Record<string, string>>({})
  const [invoiceQty, setInvoiceQty] = useState<Record<string, string>>({})
  const [invoicePrice, setInvoicePrice] = useState<Record<string, string>>({})
  const [invoiceNumber, setInvoiceNumber] = useState("")

  useEffect(() => {
    fetchPOReconciliations(po.id).then((res: EnrichedReconResponse[]) => setReconData(res))
    
    // Auto-fill inputs
    const req: Record<string, string> = {}
    const pri: Record<string, string> = {}
    po.lines.forEach(line => {
      req[line.id] = line.ordered_quantity.toString()
      pri[line.id] = line.unit_price.toString()
    })
    setReceiptQty(req)
    setInvoiceQty(req)
    setInvoicePrice(pri)
  }, [po])

  const getSkuName = (sku_id: string) => {
    return catalog.skus.find(s => s.id === sku_id)?.name || "SKU Desconhecido"
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const handleReceive = async () => {
    setIsSubmitting(true)
    const lines = po.lines.map(l => ({
      po_line_id: l.id,
      sku_id: l.sku_id,
      quantity: parseFloat(receiptQty[l.id] || "0"),
      unit_price: l.unit_price // keeping original price for receipt
    })).filter(l => l.quantity > 0)

    const ok = await receivePurchaseOrder(po.id, { lines })
    setIsSubmitting(false)
    if (ok) {
      alert("Recebimento Físico registrado com sucesso!")
      router.refresh()
    } else {
      alert("Falha no recebimento físico.")
    }
  }

  const handleInvoice = async () => {
    if (!invoiceNumber) return alert("Preencha o número da NF")
    setIsSubmitting(true)
    
    let total = 0
    const lines = po.lines.map(l => {
      const q = parseFloat(invoiceQty[l.id] || "0")
      const p = parseFloat(invoicePrice[l.id] || "0")
      total += q * p
      return {
        po_line_id: l.id,
        sku_id: l.sku_id,
        invoiced_quantity: q,
        unit_price: p
      }
    }).filter(l => l.invoiced_quantity > 0)

    const ok = await invoicePurchaseOrder(po.id, {
      invoice_number: invoiceNumber,
      issue_date: new Date().toISOString(),
      due_date: null,
      total_amount: total,
      lines
    })
    setIsSubmitting(false)
    if (ok) {
      alert("Fatura Financeira registrada com sucesso!")
      router.refresh()
    } else {
      alert("Falha no registro da fatura.")
    }
  }

  const renderReconBadge = (status: string) => {
    if (status === "MATCHED") return <Badge variant="emerald"><CheckCircle className="h-3 w-3 mr-1"/> MATCHED</Badge>
    if (status === "UNMATCHED") return <Badge variant="default">PENDENTE</Badge>
    return <Badge variant="crimson"><AlertTriangle className="h-3 w-3 mr-1"/> {status}</Badge>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <button 
            onClick={() => router.push("/purchase-orders")}
            className="text-sm text-slate-400 hover:text-white flex items-center gap-1 mb-2 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Voltar
          </button>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <ShoppingCart className="h-8 w-8 text-[#00f0ff]" />
            Pedido {po.id.split("-")[0]}
          </h2>
        </div>
      </div>

      <div className="flex gap-2 bg-slate-900/50 p-1 rounded-xl w-fit border border-slate-800">
        <button onClick={() => setActiveTab("ORDER")} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === "ORDER" ? "bg-slate-800 text-white shadow-lg" : "text-slate-400 hover:text-white"}`}>Pedido Original</button>
        <button onClick={() => setActiveTab("RECEIVE")} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === "RECEIVE" ? "bg-slate-800 text-[#00f0ff] shadow-lg" : "text-slate-400 hover:text-white"}`}>Recebimento Físico</button>
        <button onClick={() => setActiveTab("INVOICE")} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === "INVOICE" ? "bg-slate-800 text-[#a855f7] shadow-lg" : "text-slate-400 hover:text-white"}`}>Fatura Financeira</button>
        <button onClick={() => setActiveTab("RECON")} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === "RECON" ? "bg-slate-800 text-[#f59e0b] shadow-lg" : "text-slate-400 hover:text-white"}`}>3-Way Match</button>
      </div>

      {activeTab === "ORDER" && (
        <GlassPanel className="p-0 overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
              <tr>
                <th className="px-6 py-4 font-semibold">SKU</th>
                <th className="px-6 py-4 font-semibold text-right">Qtd Solicitada</th>
                <th className="px-6 py-4 font-semibold text-right">Preço Unitário</th>
                <th className="px-6 py-4 font-semibold text-right">Total Solicitado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-slate-300">
              {po.lines.map((l) => (
                <tr key={l.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-medium">{getSkuName(l.sku_id)}</td>
                  <td className="px-6 py-4 text-right font-mono">{l.ordered_quantity}</td>
                  <td className="px-6 py-4 text-right">{formatCurrency(l.unit_price)}</td>
                  <td className="px-6 py-4 text-right text-slate-100 font-bold">{formatCurrency(l.ordered_quantity * l.unit_price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </GlassPanel>
      )}

      {activeTab === "RECEIVE" && (
        <GlassPanel className="p-5 flex flex-col space-y-4">
          <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2 mb-2">
            <Truck className="h-5 w-5 text-[#00f0ff]" />
            Lançar Recebimento Físico (Afeta Estoque)
          </h3>
          <div className="overflow-x-auto border border-slate-700 rounded-xl">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 font-semibold">SKU</th>
                  <th className="px-6 py-4 font-semibold text-right">Qtd Pedida</th>
                  <th className="px-6 py-4 font-semibold text-right">Qtd Recebida (Chegada Física)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50 text-slate-300">
                {po.lines.map((l) => (
                  <tr key={l.id}>
                    <td className="px-6 py-4 font-medium">{getSkuName(l.sku_id)}</td>
                    <td className="px-6 py-4 text-right font-mono text-slate-500">{l.ordered_quantity}</td>
                    <td className="px-6 py-4 text-right">
                      <input
                        type="number"
                        value={receiptQty[l.id] || ""}
                        onChange={(e) => setReceiptQty(p => ({...p, [l.id]: e.target.value}))}
                        className="w-32 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-right focus:border-[#00f0ff] outline-none"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button onClick={handleReceive} disabled={isSubmitting} className="self-end bg-[#00f0ff] text-slate-950 px-6 py-2 rounded-xl font-bold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)]">
            {isSubmitting ? "Lançando..." : "Registrar Goods Receipt"}
          </button>
        </GlassPanel>
      )}

      {activeTab === "INVOICE" && (
        <GlassPanel className="p-5 flex flex-col space-y-4">
          <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2 mb-2">
            <FileCheck className="h-5 w-5 text-[#a855f7]" />
            Lançar Fatura Financeira (NFe)
          </h3>
          <div className="flex gap-4 mb-2">
            <input 
              type="text" 
              placeholder="Número da Fatura" 
              value={invoiceNumber} 
              onChange={e => setInvoiceNumber(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 focus:border-[#a855f7] outline-none"
            />
          </div>
          <div className="overflow-x-auto border border-slate-700 rounded-xl">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 font-semibold">SKU</th>
                  <th className="px-6 py-4 font-semibold text-right">Qtd Faturada</th>
                  <th className="px-6 py-4 font-semibold text-right">Preço Faturado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50 text-slate-300">
                {po.lines.map((l) => (
                  <tr key={l.id}>
                    <td className="px-6 py-4 font-medium">{getSkuName(l.sku_id)}</td>
                    <td className="px-6 py-4 text-right">
                      <input
                        type="number"
                        value={invoiceQty[l.id] || ""}
                        onChange={(e) => setInvoiceQty(p => ({...p, [l.id]: e.target.value}))}
                        className="w-32 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-right focus:border-[#a855f7] outline-none"
                      />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <input
                        type="number"
                        step="0.01"
                        value={invoicePrice[l.id] || ""}
                        onChange={(e) => setInvoicePrice(p => ({...p, [l.id]: e.target.value}))}
                        className="w-32 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-100 text-right focus:border-[#a855f7] outline-none"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button onClick={handleInvoice} disabled={isSubmitting} className="self-end bg-[#a855f7] text-slate-100 px-6 py-2 rounded-xl font-bold shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:shadow-[0_0_25px_rgba(168,85,247,0.5)]">
            {isSubmitting ? "Registrando..." : "Registrar Fatura (Supplier Invoice)"}
          </button>
        </GlassPanel>
      )}

      {activeTab === "RECON" && (
        <GlassPanel className="p-0 overflow-x-auto border-[#f59e0b]/30">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
              <tr>
                <th className="px-6 py-4 font-semibold">SKU (Linha PO)</th>
                <th className="px-6 py-4 font-semibold">Status Reconciliação</th>
                <th className="px-6 py-4 font-semibold text-right">Qtd Solicitada (PO)</th>
                <th className="px-6 py-4 font-semibold text-right">Preço Orig (PO)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-slate-300">
              {po.lines.map((l) => {
                const recon = reconData.find((r: EnrichedReconResponse) => r.po_line_id === l.id)
                return (
                  <tr key={l.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-medium">{getSkuName(l.sku_id)}</td>
                    <td className="px-6 py-4">
                      {recon ? renderReconBadge(recon.status) : <Badge variant="default">Aguardando Lançamentos</Badge>}
                    </td>
                    <td className="px-6 py-4 text-right font-mono">{l.ordered_quantity}</td>
                    <td className="px-6 py-4 text-right">{formatCurrency(l.unit_price)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </GlassPanel>
      )}
    </div>
  )
}
