import React from "react"
import { fetchKDSQueueServer } from "@/lib/api-server"
import { KDSClient } from "./KDSClient"

export const dynamic = "force-dynamic"

export default async function KDSPage() {
  const initialItems = await fetchKDSQueueServer()

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          👨‍🍳 KDS — Kitchen Display System (Cozinha & Bar)
        </h1>
        <p className="text-sm text-slate-400">
          Monitor de produção em tempo real com roteamento por estação (Cozinha Quente, Bar, Forno, Sobremesas) e alertas de tempo de preparo (SLA).
        </p>
      </div>

      <KDSClient initialItems={initialItems} />
    </div>
  )
}
