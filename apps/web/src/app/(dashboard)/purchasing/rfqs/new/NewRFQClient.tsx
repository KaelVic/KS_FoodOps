"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { 
  ArrowLeft, Plus, Trash2, Scale, Building2, Calendar, 
  DollarSign, Check, Sparkles, Send, Users, Package
} from "lucide-react"
import { createRFQClient } from "@/lib/api-client"

interface NewRFQClientProps {
  locations: any[]
  suppliers: any[]
  catalog: {
    skus: any[]
    uoms: any[]
  }
}

export function NewRFQClient({ locations, suppliers, catalog }: NewRFQClientProps) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const [title, setTitle] = React.useState("")
  const [locationId, setLocationId] = React.useState(locations[0]?.id || "")
  const [deadline, setDeadline] = React.useState("")
  const [notes, setNotes] = React.useState("")

  const [items, setItems] = React.useState<Array<{ sku_id: string; quantity: string; target_price: string }>>([
    { sku_id: "", quantity: "", target_price: "" }
  ])

  const [selectedSuppliers, setSelectedSuppliers] = React.useState<string[]>([])

  const handleAddItem = () => {
    setItems([...items, { sku_id: "", quantity: "", target_price: "" }])
  }

  const handleRemoveItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index))
    }
  }

  const handleItemChange = (index: number, field: string, value: string) => {
    const updated = [...items]
    updated[index] = { ...updated[index], [field]: value }
    setItems(updated)
  }

  const toggleSupplier = (supplierId: string) => {
    if (selectedSuppliers.includes(supplierId)) {
      setSelectedSuppliers(selectedSuppliers.filter(id => id !== supplierId))
    } else {
      setSelectedSuppliers([...selectedSuppliers, supplierId])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!title.trim()) {
      setError("Informe o título da cotação.")
      return
    }

    const validItems = items.filter(i => i.sku_id && parseFloat(i.quantity) > 0)
    if (validItems.length === 0) {
      setError("Adicione pelo menos um item válido com quantidade.")
      return
    }

    setIsSubmitting(true)
    try {
      const payload = {
        title,
        location_id: locationId || null,
        deadline: deadline ? new Date(deadline).toISOString() : null,
        notes: notes || null,
        items: validItems.map(i => ({
          sku_id: i.sku_id,
          quantity: parseFloat(i.quantity),
          target_price: i.target_price ? parseFloat(i.target_price) : null
        })),
        supplier_ids: selectedSuppliers.length > 0 ? selectedSuppliers : null
      }

      const res = await createRFQClient(payload)
      router.push(`/purchasing/rfqs/${res.id}`)
      router.refresh()
    } catch (err: any) {
      setError(err.message || "Erro ao criar cotação.")
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-20">
      {/* Back Button & Header */}
      <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
        <Link
          href="/purchasing/rfqs"
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Scale className="w-5 h-5 text-[#00f0ff]" />
            Nova Cotação Eletrônica B2B (RFQ)
          </h1>
          <p className="text-xs text-slate-400">
            Defina os insumos, metas de custo e selecione fornecedores para tomada de preços.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Building2 className="w-4 h-4 text-[#00f0ff]" />
            1. Dados Gerais da Cotação
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Título / Descrição da Cotação *
              </label>
              <input
                type="text"
                required
                placeholder="Ex: Cotação Semanal de Carnes e Hortifruti - Semana 34"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#00f0ff]"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Unidade / Filial Destino
              </label>
              <select
                value={locationId}
                onChange={(e) => setLocationId(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-[#00f0ff]"
              >
                <option value="">Matriz / Todas as Unidades</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Prazo Limite de Envio das Propostas
              </label>
              <input
                type="date"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-slate-800 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-[#00f0ff]"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Observações / Condições de Entrega
              </label>
              <textarea
                rows={2}
                placeholder="Ex: Entregas permitidas de segunda a quarta das 07h às 10h. Pagamento faturado 28 DDL."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3.5 py-2 bg-slate-950/80 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#00f0ff]"
              />
            </div>
          </div>
        </div>

        {/* Items to Quote */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Package className="w-4 h-4 text-[#00f0ff]" />
              2. Itens Solicitados para Cotação
            </h2>
            <button
              type="button"
              onClick={handleAddItem}
              className="px-3 py-1.5 bg-[#00f0ff]/10 hover:bg-[#00f0ff]/20 text-[#00f0ff] text-xs font-semibold rounded-lg border border-[#00f0ff]/30 transition-all inline-flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" /> Adicionar Item
            </button>
          </div>

          <div className="space-y-3">
            {items.map((item, idx) => (
              <div
                key={idx}
                className="grid grid-cols-1 md:grid-cols-12 gap-3 p-3.5 rounded-lg bg-slate-950/50 border border-slate-800/80 items-end"
              >
                <div className="md:col-span-6">
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">
                    SKU / Insumo *
                  </label>
                  <select
                    required
                    value={item.sku_id}
                    onChange={(e) => handleItemChange(idx, "sku_id", e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  >
                    <option value="">Selecione o Insumo do Cardápio...</option>
                    {catalog.skus.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="md:col-span-3">
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">
                    Qtd Solicitada *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="0.00"
                    value={item.quantity}
                    onChange={(e) => handleItemChange(idx, "quantity", e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">
                    Preço Alvo (R$)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Opcional"
                    value={item.target_price}
                    onChange={(e) => handleItemChange(idx, "target_price", e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>

                <div className="md:col-span-1 flex justify-end">
                  <button
                    type="button"
                    disabled={items.length === 1}
                    onClick={() => handleRemoveItem(idx)}
                    className="p-2 text-slate-500 hover:text-rose-400 disabled:opacity-30 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Invited Suppliers */}
        <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                <Users className="w-4 h-4 text-[#00f0ff]" />
                3. Fornecedores Homologados para Cotação ({selectedSuppliers.length} selecionados)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Selecione quais parceiros receberão esta solicitação de tomada de preços.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {suppliers.map((supp) => {
              const isSelected = selectedSuppliers.includes(supp.id)
              return (
                <div
                  key={supp.id}
                  onClick={() => toggleSupplier(supp.id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
                    isSelected
                      ? "bg-[#00f0ff]/10 border-[#00f0ff]/50 text-slate-100 shadow-[0_0_12px_rgba(0,240,255,0.15)]"
                      : "bg-slate-950/40 border-slate-800/80 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <div className="overflow-hidden">
                    <p className="text-xs font-bold truncate">{supp.name}</p>
                    {supp.tax_id && (
                      <p className="text-[10px] font-mono text-slate-500">{supp.tax_id}</p>
                    )}
                  </div>
                  <div
                    className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 transition-all ${
                      isSelected
                        ? "bg-[#00f0ff] text-slate-950 font-bold"
                        : "border border-slate-700 bg-slate-900"
                    }`}
                  >
                    {isSelected && <Check className="w-3.5 h-3.5" />}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Submit Bar */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Link
            href="/purchasing/rfqs"
            className="px-4 py-2.5 rounded-lg border border-slate-800 text-slate-400 hover:text-slate-200 text-sm font-medium transition-colors"
          >
            Cancelar
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-bold text-sm shadow-lg shadow-[#00f0ff]/20 hover:opacity-95 transition-all inline-flex items-center gap-2 disabled:opacity-50"
          >
            {isSubmitting ? (
              <span>Criando cotação...</span>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Disparar Cotação B2B</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
