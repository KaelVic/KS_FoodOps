import { Metadata } from "next"
import { fetchShiftsServer, fetchEmployeesServer, fetchLocationsServer } from "@/lib/api-server"
import { ShiftsClient } from "./ShiftsClient"

export const metadata: Metadata = {
  title: "Escalas & Turnos | KS FoodOps",
  description: "Planejamento de Jornadas e Escala de Restaurante",
}

export const dynamic = "force-dynamic"

export default async function ShiftsPage() {
  const [shifts, employees, locations] = await Promise.all([
    fetchShiftsServer(),
    fetchEmployeesServer(),
    fetchLocationsServer()
  ])

  return (
    <div className="p-6 md:p-8">
      <ShiftsClient
        initialShifts={shifts}
        employees={employees}
        locations={locations}
      />
    </div>
  )
}
