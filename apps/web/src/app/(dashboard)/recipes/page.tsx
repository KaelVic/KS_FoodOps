import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { ChefHat, PackageSearch, DollarSign, ChefHat as ChefHatIcon, Package, Calculator } from "lucide-react"
import { fetchRecipesServer, fetchCatalogSkusAndUomsServer } from "@/lib/api-server"
import RecipesClient from "./RecipesClient"

export const dynamic = "force-dynamic"

async function getDashboardData() {
  const [recipes, catalog] = await Promise.all([
    fetchRecipesServer(),
    fetchCatalogSkusAndUomsServer(),
  ])

  const totalFichas = recipes.length
  const avgPortionCost = recipes.length > 0
    ? recipes.reduce((sum, r) => sum + (r.portion_cost || 0), 0) / recipes.length
    : 0
  const totalPreparados = recipes.filter(r => r.type === "PREPARED_ITEM").length

  return {
    recipes,
    catalog,
    metrics: {
      totalFichas,
      avgPortionCost,
      totalPreparados,
    },
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export default async function RecipesPage() {
  const { recipes, catalog, metrics } = await getDashboardData()

  const menuItems = recipes.filter(r => r.type === "MENU_ITEM").length
  const preparedItems = recipes.filter(r => r.type === "PREPARED_ITEM").length

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <ChefHatIcon className="h-8 w-8 text-[#00f0ff]" />
            Fichas Técnicas & Engenharia de Menu
          </h2>
          <p className="text-slate-400 mt-1">
            Cadastro de receitas, cálculo de porção, custo CMV e engenharia de menu.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassPanel accent="cyan" className="p-5 flex flex-col justify-between">
          <div className="flex items-center gap-3 mb-2">
            <PackageSearch className="h-5 w-5 text-[#00f0ff]" />
            <span className="text-slate-400 text-sm font-medium">Total de Fichas</span>
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{metrics.totalFichas}</span>
            <span className="text-xs text-slate-500">cadastradas</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="emerald" className="p-5 flex flex-col justify-between">
          <div className="flex items-center gap-3 mb-2">
            <ChefHat className="h-5 w-5 text-[#34d399]" />
            <span className="text-slate-400 text-sm font-medium">Pratos de Menu</span>
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{menuItems}</span>
            <span className="text-xs text-slate-500">venda direta</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="amber" className="p-5 flex flex-col justify-between">
          <div className="flex items-center gap-3 mb-2">
            <Calculator className="h-5 w-5 text-[#f59e0b]" />
            <span className="text-slate-400 text-sm font-medium">Bases / Sub-receitas</span>
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{metrics.totalPreparados}</span>
            <span className="text-xs text-slate-500">pré-preparos</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="violet" className="p-5 flex flex-col justify-between">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="h-5 w-5 text-[#a855f7]" />
            <span className="text-slate-400 text-sm font-medium">Custo Médio (Porção)</span>
          </div>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">
              {formatCurrency(metrics.avgPortionCost)}
            </span>
            <span className="text-xs text-slate-500">geral</span>
          </div>
        </GlassPanel>
      </div>

      <RecipesClient
        initialRecipes={recipes}
        initialCatalog={catalog}
      />
    </div>
  )
}