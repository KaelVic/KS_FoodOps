import { Suspense } from "react"
import { fetchMenuEngineeringServer, fetchMenuCategoriesServer } from "@/lib/api-server"
import { MenuEngineeringClient } from "./MenuEngineeringClient"
import { Loader2 } from "lucide-react"

export const dynamic = "force-dynamic"
export const revalidate = 0

export default async function MenuEngineeringPage() {
  const [initialData, categories] = await Promise.all([
    fetchMenuEngineeringServer(),
    fetchMenuCategoriesServer(),
  ])

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400 bg-clip-text text-transparent">
            Engenharia de Menu (Matriz BCG)
          </h2>
          <p className="text-muted-foreground text-sm mt-1">
            Análise de lucratividade e popularidade do cardápio (Kasavana & Smith) — Estrelas, Burros de Carga, Quebra-Cabeças e Cães com precificação inteligente.
          </p>
        </div>
      </div>

      <Suspense
        fallback={
          <div className="flex h-96 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
          </div>
        }
      >
        <MenuEngineeringClient initialData={initialData} categories={categories} />
      </Suspense>
    </div>
  )
}
