import { Suspense } from "react"
import {
  fetchCashFlowServer,
  fetchBankAccountsServer
} from "@/lib/api-server"
import CashFlowClient from "./CashFlowClient"

export const dynamic = "force-dynamic"

export default async function CashFlowPage() {
  const [initialCashFlow, bankAccounts] = await Promise.all([
    fetchCashFlowServer(),
    fetchBankAccountsServer()
  ])

  return (
    <div className="space-y-6">
      <Suspense fallback={<div className="text-muted-foreground">Carregando Fluxo de Caixa...</div>}>
        <CashFlowClient
          initialCashFlow={initialCashFlow}
          bankAccounts={bankAccounts}
        />
      </Suspense>
    </div>
  )
}
