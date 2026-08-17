import { Metadata } from "next"
import { 
  fetchPayablesDashboardServer, 
  fetchPayableBillsServer, 
  fetchSuppliersServer, 
  fetchFinancialCategoriesServer, 
  fetchCostCentersServer, 
  fetchBankAccountsServer 
} from "@/lib/api-server"
import PayablesClient from "./PayablesClient"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Contas a Pagar (ERP) | KS FoodOps",
  description: "Gestão financeira de despesas, vencimentos, boletos, PIX e liquidação de fornecedores.",
}

export default async function PayablesPage() {
  const [dashboard, bills, suppliers, categories, costCenters, bankAccounts] = await Promise.all([
    fetchPayablesDashboardServer(),
    fetchPayableBillsServer(),
    fetchSuppliersServer(),
    fetchFinancialCategoriesServer(),
    fetchCostCentersServer(),
    fetchBankAccountsServer()
  ])

  return (
    <div className="h-full flex flex-col space-y-6">
      <PayablesClient
        initialDashboard={dashboard}
        initialBills={bills}
        suppliers={suppliers}
        categories={categories}
        costCenters={costCenters}
        bankAccounts={bankAccounts}
      />
    </div>
  )
}
