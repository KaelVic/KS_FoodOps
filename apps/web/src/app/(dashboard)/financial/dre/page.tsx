import { Suspense } from "react"
import { fetchFinancialDREServer } from "@/lib/api-server"
import FinancialDREClient from "./FinancialDREClient"

export const dynamic = "force-dynamic"

export default async function FinancialDREPage() {
  const initialDRE = await fetchFinancialDREServer(undefined, undefined, "COMPETENCE")

  return (
    <div className="space-y-6">
      <Suspense fallback={<div className="text-muted-foreground">Carregando DRE Financeira...</div>}>
        <FinancialDREClient initialDRE={initialDRE} />
      </Suspense>
    </div>
  )
}
