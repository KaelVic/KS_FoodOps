import { Metadata } from "next"
import { fetchBankAccountsServer } from "@/lib/api-server"
import BankAccountsClient from "./BankAccountsClient"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Contas Bancárias & Caixas | KS FoodOps ERP",
  description: "Gestão de contas correntes, caixas físicos e carteiras digitais do restaurante.",
}

export default async function BankAccountsPage() {
  const accounts = await fetchBankAccountsServer()

  return (
    <div className="h-full flex flex-col space-y-6">
      <BankAccountsClient initialAccounts={accounts} />
    </div>
  )
}
