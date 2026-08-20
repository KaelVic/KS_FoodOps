import { Metadata } from "next"
import { fetchInventoryBalancesServer, fetchTheoreticalBalancesServer } from "@/lib/api-server"
import { InventoryClient } from "./InventoryClient"

export const dynamic = "force-dynamic"

export const metadata: Metadata = {
  title: "Estoque & Inventário Perpétuo | KS FoodOps",
  description: "Radar de insumos, auditoria de estoque teórico e conciliação de CMV",
}

export default async function InventoryPage() {
  const [balances, theoreticalBalances] = await Promise.all([
    fetchInventoryBalancesServer(),
    fetchTheoreticalBalancesServer(),
  ])

  return (
    <InventoryClient
      initialBalances={balances}
      theoreticalBalances={theoreticalBalances}
    />
  )
}