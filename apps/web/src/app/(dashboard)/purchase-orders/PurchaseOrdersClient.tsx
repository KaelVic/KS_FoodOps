"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Plus, ArrowRight, ShoppingCart } from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { PurchaseOrderItem } from "@/types/purchase-orders"
import { createPurchaseOrder } from "@/lib/api-client"

export default function PurchaseOrdersClient({ initialOrders }: { initialOrders: PurchaseOrderItem[] }) {
  const router = useRouter()
  const [orders, setOrders] = useState(initialOrders)
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  // Hardcoded references for MVP Demo
  const defaultLocationId = "00000000-0000-0000-0000-000000000002"
  const defaultSupplierId = "00000000-0000-0000-0000-000000000010"

  const handleCreateMockPO = async () => {
    setIsSubmitting(true)
    // Create a mock PO to demo the reconciliation
    const order = await createPurchaseOrder({
      location_id: defaultLocationId,
      supplier_id: defaultSupplierId,
      expected_delivery_date: null,
      lines: [
        {
          sku_id: "00000000-0000-0000-0000-000000000020", // Salmão Fresco
          ordered_quantity: 50,
          unit_price: 45.00
        },
        {
          sku_id: "00000000-0000-0000-0000-000000000021", // Arroz Arbório
          ordered_quantity: 20,
          unit_price: 15.50
        }
      ]
    })
    setIsSubmitting(false)
    
    if (order) {
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

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          onClick={handleCreateMockPO}
          disabled={isSubmitting}
          className="bg-[#00f0ff] text-slate-950 px-4 py-2 rounded-xl font-semibold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all flex items-center justify-center gap-2"
        >
          <Plus className="h-5 w-5" />
          {isSubmitting ? "Gerando PO..." : "Novo Pedido de Compra (Mock)"}
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
    </div>
  )
}
