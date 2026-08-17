"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Plus, ArrowRight, ShoppingCart, X, Trash2 } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { PurchaseOrderItem, CreatePOPayload } from "@/types/purchase-orders"
import { createPurchaseOrder } from "@/lib/api-client"
import { Location, Supplier } from "@/types/master-data"
import { CatalogSkusAndUoms } from "@/types/recipes"

interface PurchaseOrdersClientProps {
  initialOrders: PurchaseOrderItem[]
  locations: Location[]
  suppliers: Supplier[]
  catalog: CatalogSkusAndUoms
}

export default function PurchaseOrdersClient({ 
  initialOrders,
  locations,
  suppliers,
  catalog
}: PurchaseOrdersClientProps) {
  const router = useRouter()
  const [orders, setOrders] = useState(initialOrders)
  
  // Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form State
  const [locationId, setLocationId] = useState("")
  const [supplierId, setSupplierId] = useState("")
  const [lines, setLines] = useState<{sku_id: string, ordered_quantity: number, unit_price: number}[]>([])

  const handleAddLine = () => {
    setLines([...lines, { sku_id: "", ordered_quantity: 0, unit_price: 0 }])
  }

  const handleUpdateLine = (index: number, field: string, value: any) => {
    const newLines = [...lines]
    newLines[index] = { ...newLines[index], [field]: value }
    setLines(newLines)
  }

  const handleRemoveLine = (index: number) => {
    setLines(lines.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!locationId || !supplierId || lines.length === 0) {
      alert("Preencha todos os campos e adicione ao menos um item.")
      return
    }

    setIsSubmitting(true)
    const payload: CreatePOPayload = {
      location_id: locationId,
      supplier_id: supplierId,
      expected_delivery_date: null,
      lines: lines.filter(l => l.sku_id && l.ordered_quantity > 0)
    }

    const order = await createPurchaseOrder(payload)
    setIsSubmitting(false)
    
    if (order) {
      setIsCreateOpen(false)
      setLocationId("")
      setSupplierId("")
      setLines([])
      router.refresh()
      router.push(`/purchase-orders/${order.id}`)
    } else {
      alert("Erro ao criar PO.")
    }
  }

  const getStatusBadge = (status: string) => {
    switch(status) {
      case "DRAFT": return <Badge variant="default">Rascunho</Badge>
      case "PARTIAL_RECEIPT": return <Badge variant="amber">Recebimento Parcial</Badge>
      case "FULLY_RECEIVED": return <Badge variant="emerald">Recebido</Badge>
      default: return <Badge variant="violet">{status}</Badge>
    }
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const totalPoValue = lines.reduce((acc, curr) => acc + (curr.ordered_quantity * curr.unit_price), 0)

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          onClick={() => setIsCreateOpen(true)}
          className="bg-[#00f0ff] text-slate-950 px-4 py-2 rounded-xl font-semibold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all flex items-center justify-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Novo Pedido de Compra
        </button>
      </div>

      <GlassPanel className="p-0 overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
            <tr>
              <th className="px-6 py-4 font-semibold">ID do Pedido</th>
              <th className="px-6 py-4 font-semibold">Status</th>
              <th className="px-6 py-4 font-semibold">Criado em</th>
              <th className="px-6 py-4 font-semibold text-right">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 text-slate-300">
            {orders.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                  Nenhum pedido de compra encontrado.
                </td>
              </tr>
            ) : (
              orders.map((o) => (
                <tr key={o.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-mono text-slate-400">
                    {o.id.split("-")[0]}...
                  </td>
                  <td className="px-6 py-4">
                    {getStatusBadge(o.status)}
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {new Date(o.created_at).toLocaleString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => router.push(`/purchase-orders/${o.id}`)}
                      className="text-[#00f0ff] hover:text-cyan-300 transition-colors flex items-center justify-end gap-1 w-full"
                    >
                      Detalhes 3-Way
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </GlassPanel>

      {/* Create PO Modal */}
      <AnimatePresence>
        {isCreateOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 20, opacity: 0 }}
              className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl"
            >
              <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-800/30">
                <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <ShoppingCart className="h-5 w-5 text-[#00f0ff]" />
                  Novo Pedido de Compra
                </h3>
                <button
                  onClick={() => setIsCreateOpen(false)}
                  className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                <form id="create-po-form" onSubmit={handleSubmit} className="space-y-8">
                  {/* Basic Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-300">Local de Estoque</label>
                      <select
                        required
                        value={locationId}
                        onChange={(e) => setLocationId(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 focus:border-[#00f0ff] outline-none transition-all"
                      >
                        <option value="">Selecione o local de entrega...</option>
                        {locations.map(loc => (
                          <option key={loc.id} value={loc.id}>{loc.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-300">Fornecedor</label>
                      <select
                        required
                        value={supplierId}
                        onChange={(e) => setSupplierId(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 focus:border-[#00f0ff] outline-none transition-all"
                      >
                        <option value="">Selecione o fornecedor...</option>
                        {suppliers.map(sup => (
                          <option key={sup.id} value={sup.id}>{sup.name} {sup.tax_id ? `(${sup.tax_id})` : ""}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Line Items */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Itens do Pedido</h4>
                      <button
                        type="button"
                        onClick={handleAddLine}
                        className="text-sm text-[#00f0ff] hover:text-cyan-300 font-medium flex items-center gap-1"
                      >
                        <Plus className="h-4 w-4" /> Adicionar Item
                      </button>
                    </div>
                    
                    <div className="border border-slate-700 rounded-xl overflow-hidden">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
                          <tr>
                            <th className="p-3">SKU (Insumo)</th>
                            <th className="p-3 text-right">Qtd</th>
                            <th className="p-3 text-right">Preço Unitário</th>
                            <th className="p-3 text-right">Total Linha</th>
                            <th className="p-3"></th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {lines.length === 0 && (
                            <tr>
                              <td colSpan={5} className="p-6 text-center text-slate-500">
                                Nenhum item adicionado ao pedido.
                              </td>
                            </tr>
                          )}
                          {lines.map((line, idx) => (
                            <tr key={idx} className="bg-slate-950/50">
                              <td className="p-3">
                                <select
                                  required
                                  value={line.sku_id}
                                  onChange={(e) => handleUpdateLine(idx, "sku_id", e.target.value)}
                                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                  <option value="">Selecionar SKU...</option>
                                  {catalog.skus.map(s => (
                                    <option key={s.id} value={s.id}>{s.name}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="p-3">
                                <input
                                  required
                                  type="number" step="0.01" min="0"
                                  value={line.ordered_quantity || ""}
                                  onChange={(e) => handleUpdateLine(idx, "ordered_quantity", parseFloat(e.target.value))}
                                  className="w-full text-right bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                  placeholder="0.00"
                                />
                              </td>
                              <td className="p-3">
                                <input
                                  required
                                  type="number" step="0.01" min="0"
                                  value={line.unit_price || ""}
                                  onChange={(e) => handleUpdateLine(idx, "unit_price", parseFloat(e.target.value))}
                                  className="w-full text-right bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                  placeholder="R$ 0,00"
                                />
                              </td>
                              <td className="p-3 text-right font-medium text-emerald-400">
                                {formatCurrency((line.ordered_quantity || 0) * (line.unit_price || 0))}
                              </td>
                              <td className="p-3 text-right">
                                <button
                                  type="button"
                                  onClick={() => handleRemoveLine(idx)}
                                  className="text-slate-500 hover:text-red-400 p-1 transition-colors"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </form>
              </div>

              <div className="p-6 border-t border-slate-800 bg-slate-900 flex items-center justify-between">
                <div className="text-slate-400 text-sm">
                  Valor Total do Pedido: <span className="text-[#34d399] font-bold text-lg">{formatCurrency(totalPoValue)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(false)}
                    className="px-4 py-2 rounded-xl text-slate-300 font-medium hover:bg-slate-800 transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    form="create-po-form"
                    disabled={isSubmitting || lines.length === 0}
                    className="bg-[#00f0ff] text-slate-950 px-6 py-2 rounded-xl font-bold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? "Emitindo..." : "Emitir Pedido"}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
