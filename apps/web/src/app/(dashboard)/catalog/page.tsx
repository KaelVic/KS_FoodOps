import { Metadata } from "next"
import { fetchSkusServer } from "@/lib/api-server"

export const metadata: Metadata = {
  title: "Catálogo de Insumos | KS FoodOps",
  description: "Gestão de SKUs e Insumos",
}

export default async function CatalogPage() {
  const skus = await fetchSkusServer()

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Catálogo de Insumos</h1>
      </div>
      <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-md p-6">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-white/10 text-xs uppercase text-zinc-400">
              <tr>
                <th className="px-4 py-3">Nome do Item</th>
                <th className="px-4 py-3">Categoria</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {skus.map((sku) => (
                <tr key={sku.id} className="hover:bg-white/5">
                  <td className="px-4 py-3 font-medium text-zinc-100">{sku.name}</td>
                  <td className="px-4 py-3 text-zinc-400">{sku.category_id || "Sem categoria"}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${sku.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-zinc-500/10 text-zinc-400"}`}>
                      {sku.is_active ? "Ativo" : "Inativo"}
                    </span>
                  </td>
                </tr>
              ))}
              {skus.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-8 text-center text-zinc-500">Nenhum insumo cadastrado.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
