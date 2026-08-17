import { Metadata } from "next"
import { fetchTimeClockServer, fetchEmployeesServer, fetchLocationsServer } from "@/lib/api-server"
import { TimeClockClient } from "./TimeClockClient"

export const metadata: Metadata = {
  title: "Ponto Digital | KS FoodOps",
  description: "Controle de Ponto e Jornadas de Restaurante",
}

export const dynamic = "force-dynamic"

export default async function TimeClockPage() {
  const [entries, employees, locations] = await Promise.all([
    fetchTimeClockServer(),
    fetchEmployeesServer(),
    fetchLocationsServer()
  ])

  return (
    <div className="p-6 md:p-8">
      <TimeClockClient
        initialEntries={entries}
        employees={employees}
        locations={locations}
      />
    </div>
  )
}
