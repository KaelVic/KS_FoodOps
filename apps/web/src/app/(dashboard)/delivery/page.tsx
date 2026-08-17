import React from "react"
import { fetchDeliveryKanbanServer } from "@/lib/api-server"
import { fetchMenuItemsServer } from "@/lib/api-server"
import { DeliveryClient } from "./DeliveryClient"

export const dynamic = "force-dynamic"

export default async function DeliveryPage() {
  const [kanban, menuItems] = await Promise.all([
    fetchDeliveryKanbanServer(),
    fetchMenuItemsServer(),
  ])

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          🛵 Delivery Hub Multi-Canal
        </h1>
        <p className="text-sm text-slate-400">
          Central operacional de pedidos de entrega (iFood, Rappi, Cardápio Digital QR Code, WhatsApp e Telefone).
        </p>
      </div>

      <DeliveryClient
        initialKanban={kanban}
        menuItems={menuItems}
      />
    </div>
  )
}
