import { Suspense } from "react"
import {
  fetchReceivablesDashboardServer,
  fetchReceivableInvoicesServer,
  fetchPaymentAcquirersServer,
  fetchBankAccountsServer,
  fetchFinancialCategoriesServer,
  fetchCostCentersServer
} from "@/lib/api-server"
import ReceivablesClient from "./ReceivablesClient"

export const dynamic = "force-dynamic"

export default async function ReceivablesPage() {
  const [
    dashboardMetrics,
    initialInvoices,
    acquirers,
    bankAccounts,
    categories,
    costCenters
  ] = await Promise.all([
    fetchReceivablesDashboardServer(),
    fetchReceivableInvoicesServer(),
    fetchPaymentAcquirersServer(),
    fetchBankAccountsServer(),
    fetchFinancialCategoriesServer(),
    fetchCostCentersServer()
  ])

  return (
    <div className="space-y-6">
      <Suspense fallback={<div className="text-muted-foreground">Carregando Contas a Receber...</div>}>
        <ReceivablesClient
          initialDashboard={dashboardMetrics}
          initialInvoices={initialInvoices}
          acquirers={acquirers}
          bankAccounts={bankAccounts}
          categories={categories}
          costCenters={costCenters}
        />
      </Suspense>
    </div>
  )
}
