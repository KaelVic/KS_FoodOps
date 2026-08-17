import { Suspense } from "react"
import {
  fetchMenuItemsServer,
  fetchMenuCategoriesServer,
  fetchRecipesServer,
} from "@/lib/api-server"
import { MenuItemsClient } from "./MenuItemsClient"
import { Loader2 } from "lucide-react"

export const dynamic = "force-dynamic"
export const revalidate = 0

export default async function MenuItemsPage() {
  const [items, categories, recipes] = await Promise.all([
    fetchMenuItemsServer(),
    fetchMenuCategoriesServer(),
    fetchRecipesServer(),
  ])

  return (
    <div className="flex-1 space-y-6 p-4 md:p-8 pt-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400 bg-clip-text text-transparent">
            Cardápio & Itens de Venda
          </h2>
          <p className="text-muted-foreground text-sm mt-1">
            Gestão do catálogo de pratos, vinculação com Fichas Técnicas (custo dinâmico), metas de CMV e precificação.
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
        <MenuItemsClient
          initialItems={items}
          categories={categories}
          recipes={recipes}
        />
      </Suspense>
    </div>
  )
}
