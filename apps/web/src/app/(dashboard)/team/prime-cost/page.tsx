import { Metadata } from "next"
import { fetchPrimeCostServer } from "@/lib/api-server"
import { PrimeCostClient } from "./PrimeCostClient"

export const metadata: Metadata = {
  title: "Prime Cost (CMV + CMO) | KS FoodOps",
  description: "Apuração Consolidada de Custo de Mercadorias e Mão de Obra",
}

export const dynamic = "force-dynamic"

export default async function PrimeCostPage() {
  const primeCostData = await fetchPrimeCostServer()

  return (
    <div className="p-6 md:p-8">
      <PrimeCostClient initialData={primeCostData} />
    </div>
  )
}
