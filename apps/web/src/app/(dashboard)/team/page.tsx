import { Metadata } from "next"
import { fetchEmployeesServer } from "@/lib/api-server"
import { TeamClient } from "./TeamClient"

export const metadata: Metadata = {
  title: "Equipe & RH Operacional | KS FoodOps",
  description: "Gestão de Colaboradores, Escalas, Ponto Digital e Gorjetas",
}

export const dynamic = "force-dynamic"

export default async function TeamPage() {
  const employees = await fetchEmployeesServer()

  return (
    <div className="p-6 md:p-8">
      <TeamClient initialEmployees={employees} />
    </div>
  )
}

