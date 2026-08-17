import { GlassPanel } from "@/components/ui/glass-panel"
import { ShoppingCart, Truck, AlertTriangle, FileCheck } from "lucide-react"
import { fetchPurchaseOrdersServer, fetchLocationsServer, fetchSuppliersServer, fetchCatalogSkusAndUomsServer } from "@/lib/api-server"
import PurchaseOrdersClient from "./PurchaseOrdersClient"

export const dynamic = "force-dynamic"

export default async function PurchaseOrdersPage() {
  const [orders, locations, suppliers, catalog] = await Promise.all([
    fetchPurchaseOrdersServer(),
    fetchLocationsServer(),
    fetchSuppliersServer(),
    fetchCatalogSkusAndUomsServer()
  ])

  const draftCount = orders.filter((o: any) => o.status === "DRAFT").length
  const partialCount = orders.filter((o: any) => o.status === "PARTIAL_RECEIPT").length
  const fullCount = orders.filter((o: any) => o.status === "FULLY_RECEIVED").length

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <ShoppingCart className="h-8 w-8 text-[#00f0ff]" />
            Pedidos de Compra (PO)
          </h2>
          <p className="text-slate-400 mt-1">
            Gestão do ciclo de vida de compras, recebimento físico e reconciliação financeira (3-Way Match).
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassPanel accent="cyan" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <ShoppingCart className="h-5 w-5 text-[#00f0ff]" />
            <span className="text-slate-400 text-sm font-medium">Pedidos em Rascunho</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{draftCount}</span>
            <span className="text-xs text-slate-500">Aguardando Envio</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="amber" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <Truck className="h-5 w-5 text-[#f59e0b]" />
            <span className="text-slate-400 text-sm font-medium">Recebimento Parcial</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{partialCount}</span>
            <span className="text-xs text-slate-500">Backorder/Pendências</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="violet" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <FileCheck className="h-5 w-5 text-[#a855f7]" />
            <span className="text-slate-400 text-sm font-medium">Recebidos Integralmente</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{fullCount}</span>
            <span className="text-xs text-slate-500">Fechados</span>
          </div>
        </GlassPanel>
      </div>

      <PurchaseOrdersClient 
        initialOrders={orders} 
        locations={locations}
        suppliers={suppliers}
        catalog={catalog}
      />
    </div>
  )
}
