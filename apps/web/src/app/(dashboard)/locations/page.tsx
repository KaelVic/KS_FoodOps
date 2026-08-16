import { Metadata } from "next"
import { fetchLocationsServer } from "@/lib/api-server"

export const metadata: Metadata = {
  title: "Locais de Estoque | KS FoodOps",
  description: "Gestão de Almoxarifados e Locais de Estoque",
}

export default async function LocationsPage() {
  const locations = await fetchLocationsServer()

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Locais de Estoque</h1>
      </div>
      <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-md p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-white/10 text-xs uppercase text-zinc-400">
              <tr>
                <th className="px-4 py-3">Nome do Local</th>
                <th className="px-4 py-3">ID Unidade de Negócio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {locations.map((loc) => (
                <tr key={loc.id} className="hover:bg-white/5">
                  <td className="px-4 py-3 font-medium text-zinc-100">{loc.name}</td>
                  <td className="px-4 py-3 text-zinc-400 font-mono text-xs">{loc.business_unit_id}</td>
                </tr>
              ))}
              {locations.length === 0 && (
                <tr>
                  <td colSpan={2} className="px-4 py-8 text-center text-zinc-500">Nenhum local cadastrado.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
