import React from "react"
import { fetchDiningTablesServer } from "@/lib/api-server"
import { fetchMenuItemsServer } from "@/lib/api-server"
import { fetchBankAccountsServer, fetchPaymentAcquirersServer } from "@/lib/api-server"
import { TablesClient } from "./TablesClient"

export const dynamic = "force-dynamic"

export default async function TablesPage() {
  const [tables, menuItems, bankAccounts, acquirers] = await Promise.all([
    fetchDiningTablesServer(),
    fetchMenuItemsServer(),
    fetchBankAccountsServer(),
    fetchPaymentAcquirersServer(),
  ])

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          🍽️ Gestão de Mesas & Comandas (Salão / PDV)
        </h1>
        <p className="text-sm text-slate-400">
          Mapa visual do restaurante em tempo real, lançamento de pedidos por mesa e fechamento integrado com faturamento e estoque.
        </p>
      </div>

      <TablesClient
        initialTables={tables}
        menuItems={menuItems}
        bankAccounts={bankAccounts}
        acquirers={acquirers}
      />
    </div>
  )
}
