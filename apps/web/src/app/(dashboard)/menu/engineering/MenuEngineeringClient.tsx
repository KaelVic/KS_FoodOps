"use client"

import React, { useState } from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import {
  MenuEngineeringResponse,
  MenuCategory,
  BCGItem,
  BCGClassification,
  SimulatePricingResponse,
} from "@/types/menu"
import {
  fetchMenuEngineeringClient,
  simulateItemPricingClient,
} from "@/lib/api-client"
import {
  Star,
  Zap,
  HelpCircle,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  PieChart,
  Calculator,
  RefreshCw,
  Search,
  ArrowUpRight,
  ArrowDownRight,
  Sparkles,
  X,
  Sliders,
  Filter,
} from "lucide-react"

interface MenuEngineeringClientProps {
  initialData: MenuEngineeringResponse | null
  categories: MenuCategory[]
}

export function MenuEngineeringClient({
  initialData,
  categories,
}: MenuEngineeringClientProps) {
  const [data, setData] = useState<MenuEngineeringResponse | null>(initialData)
  const [loading, setLoading] = useState(false)

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL")
  const [startDate, setStartDate] = useState<string>("")
  const [endDate, setEndDate] = useState<string>("")
  const [searchQuery, setSearchQuery] = useState("")
  const [activeTab, setActiveTab] = useState<"ALL" | BCGClassification>("ALL")

  // Simulator Modal State
  const [simItem, setSimItem] = useState<BCGItem | null>(null)
  const [simTargetCmv, setSimTargetCmv] = useState<string>("30.0")
  const [simNewPrice, setSimNewPrice] = useState<string>("")
  const [simResult, setSimResult] = useState<SimulatePricingResponse | null>(null)
  const [simLoading, setSimLoading] = useState(false)

  const handleFilter = async () => {
    setLoading(true)
    try {
      const res = await fetchMenuEngineeringClient(
        startDate || undefined,
        endDate || undefined,
        selectedCategory === "ALL" ? undefined : selectedCategory
      )
      setData(res)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const openSimulator = async (item: BCGItem) => {
    setSimItem(item)
    setSimTargetCmv("30.0")
    setSimNewPrice(item.sale_price.toFixed(2))
    setSimLoading(true)
    try {
      const res = await simulateItemPricingClient(item.item_id, {
        target_cmv_pct: 30.0,
      })
      setSimResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setSimLoading(false)
    }
  }

  const handleSimulateChange = async (targetCmvVal?: string, newPriceVal?: string) => {
    if (!simItem) return
    const targetCmv = targetCmvVal !== undefined ? parseFloat(targetCmvVal) : parseFloat(simTargetCmv)
    const newPrice = newPriceVal !== undefined && newPriceVal !== "" ? parseFloat(newPriceVal) : undefined

    setSimLoading(true)
    try {
      const res = await simulateItemPricingClient(simItem.item_id, {
        target_cmv_pct: !isNaN(targetCmv) ? targetCmv : undefined,
        new_price: newPrice !== undefined && !isNaN(newPrice) ? newPrice : undefined,
      })
      setSimResult(res)
    } catch (err) {
      console.error(err)
    } finally {
      setSimLoading(false)
    }
  }

  const summary = data?.summary || {
    total_revenue: 0,
    total_cost: 0,
    total_margin: 0,
    average_cmv_pct: 0,
    total_units_sold: 0,
    total_items_analyzed: 0,
    cutoff_volume: 0,
    cutoff_margin: 0,
  }

  const distribution = data?.bcg_distribution || {
    stars: 0,
    plowhorses: 0,
    puzzles: 0,
    dogs: 0,
  }

  const items = data?.items || []
  const filteredItems = items.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.pos_code && item.pos_code.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesTab = activeTab === "ALL" || item.classification === activeTab
    return matchesSearch && matchesTab
  })

  // BCG Quadrants
  const starItems = items.filter((i) => i.classification === "STAR")
  const plowhorseItems = items.filter((i) => i.classification === "PLOWHORSE")
  const puzzleItems = items.filter((i) => i.classification === "PUZZLE")
  const dogItems = items.filter((i) => i.classification === "DOG")

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <GlassPanel className="p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex flex-col gap-1">
            <span className="text-xs text-slate-400 font-medium">De</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="h-9 px-3 rounded-lg border border-slate-700 bg-slate-900/80 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs text-slate-400 font-medium">Até</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="h-9 px-3 rounded-lg border border-slate-700 bg-slate-900/80 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            />
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs text-slate-400 font-medium">Categoria</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="h-9 px-3 rounded-lg border border-slate-700 bg-slate-900/80 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            >
              <option value="ALL">Todas as Categorias</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1 justify-end pt-5">
            <button
              onClick={handleFilter}
              disabled={loading}
              className="h-9 px-4 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 text-xs font-medium flex items-center transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
              Atualizar Análise
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-400 bg-slate-900/60 px-3.5 py-2 rounded-lg border border-slate-800">
          <span>
            Cutoff Volume: <strong className="text-amber-400 font-mono">{summary.cutoff_volume.toFixed(1)} un</strong>
          </span>
          <span className="text-slate-600">•</span>
          <span>
            Cutoff Margem: <strong className="text-emerald-400 font-mono">R$ {summary.cutoff_margin.toFixed(2)}</strong>
          </span>
        </div>
      </GlassPanel>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassPanel className="p-5">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
            <span>Faturamento Analisado</span>
            <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
              <DollarSign className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            R$ {summary.total_revenue.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Volume total: {summary.total_units_sold.toLocaleString("pt-BR")} itens vendidos
          </p>
        </GlassPanel>

        <GlassPanel className="p-5">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
            <span>Margem de Contribuição</span>
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-blue-400">
            R$ {summary.total_margin.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {summary.total_revenue > 0
              ? `${((summary.total_margin / summary.total_revenue) * 100).toFixed(1)}% do faturamento`
              : "0%"}
          </p>
        </GlassPanel>

        <GlassPanel className="p-5">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
            <span>CMV Médio do Menu</span>
            <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400">
              <PieChart className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-amber-400">
            {summary.average_cmv_pct.toFixed(1)}%
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Custo Total: R$ {summary.total_cost.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
          </p>
        </GlassPanel>

        <GlassPanel className="p-5">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
            <span>Distribuição BCG</span>
            <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
              <Sparkles className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm font-semibold mt-1">
            <span className="text-amber-400">⭐ {distribution.stars}</span>
            <span className="text-slate-600">•</span>
            <span className="text-blue-400">🐴 {distribution.plowhorses}</span>
            <span className="text-slate-600">•</span>
            <span className="text-purple-400">❓ {distribution.puzzles}</span>
            <span className="text-slate-600">•</span>
            <span className="text-rose-400">🐶 {distribution.dogs}</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Total: {summary.total_items_analyzed} pratos analisados
          </p>
        </GlassPanel>
      </div>

      {/* BCG 2x2 Matrix Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Sliders className="h-5 w-5 text-amber-400" />
            Matriz BCG de Engenharia de Menu (2x2)
          </h3>
          <span className="text-xs text-slate-400">Classificação Kasavana & Smith (Volume x Margem)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Quadrant 1: STARS (Alta Margem + Alto Volume) */}
          <div className="rounded-xl border border-amber-500/30 bg-gradient-to-br from-amber-950/20 via-slate-900/60 to-slate-950 p-4">
            <div className="flex items-center justify-between pb-3 border-b border-amber-500/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-amber-500/20 text-amber-400 rounded-lg">
                  <Star className="h-5 w-5 fill-amber-400" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-amber-400">Estrelas (Stars)</h4>
                  <p className="text-2xs text-slate-400">
                    Alta Margem & Alto Volume ({starItems.length} pratos)
                  </p>
                </div>
              </div>
              <Badge variant="amber" className="text-xs">
                Proteger & Destacar
              </Badge>
            </div>
            <div className="pt-3 space-y-2 max-h-72 overflow-y-auto pr-1">
              {starItems.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-6 text-center">Nenhum prato nesta categoria</p>
              ) : (
                starItems.map((item) => (
                  <div
                    key={item.item_id}
                    className="p-2.5 rounded-lg bg-slate-900/80 border border-amber-500/20 flex items-center justify-between hover:border-amber-500/50 transition-colors"
                  >
                    <div>
                      <div className="font-semibold text-sm text-slate-200">{item.name}</div>
                      <div className="text-2xs text-slate-400 flex gap-2 mt-0.5">
                        <span>{item.units_sold} vendas</span>
                        <span>•</span>
                        <span>Preço: R$ {item.sale_price.toFixed(2)}</span>
                        <span>•</span>
                        <span className="text-amber-400 font-medium">Margem: R$ {item.unit_margin.toFixed(2)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => openSimulator(item)}
                      className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 text-2xs font-medium flex items-center transition-colors"
                    >
                      <Calculator className="h-3 w-3 mr-1" />
                      Simular
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Quadrant 2: PUZZLES (Alta Margem + Baixo Volume) */}
          <div className="rounded-xl border border-purple-500/30 bg-gradient-to-br from-purple-950/20 via-slate-900/60 to-slate-950 p-4">
            <div className="flex items-center justify-between pb-3 border-b border-purple-500/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg">
                  <HelpCircle className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-purple-400">Quebra-Cabeças (Puzzles)</h4>
                  <p className="text-2xs text-slate-400">
                    Alta Margem & Baixo Volume ({puzzleItems.length} pratos)
                  </p>
                </div>
              </div>
              <Badge variant="violet" className="text-xs">
                Promover & Reposicionar
              </Badge>
            </div>
            <div className="pt-3 space-y-2 max-h-72 overflow-y-auto pr-1">
              {puzzleItems.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-6 text-center">Nenhum prato nesta categoria</p>
              ) : (
                puzzleItems.map((item) => (
                  <div
                    key={item.item_id}
                    className="p-2.5 rounded-lg bg-slate-900/80 border border-purple-500/20 flex items-center justify-between hover:border-purple-500/50 transition-colors"
                  >
                    <div>
                      <div className="font-semibold text-sm text-slate-200">{item.name}</div>
                      <div className="text-2xs text-slate-400 flex gap-2 mt-0.5">
                        <span>{item.units_sold} vendas</span>
                        <span>•</span>
                        <span>Preço: R$ {item.sale_price.toFixed(2)}</span>
                        <span>•</span>
                        <span className="text-purple-400 font-medium">Margem: R$ {item.unit_margin.toFixed(2)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => openSimulator(item)}
                      className="px-2.5 py-1 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 hover:bg-purple-500/20 text-2xs font-medium flex items-center transition-colors"
                    >
                      <Calculator className="h-3 w-3 mr-1" />
                      Simular
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Quadrant 3: PLOWHORSES (Baixa Margem + Alto Volume) */}
          <div className="rounded-xl border border-blue-500/30 bg-gradient-to-br from-blue-950/20 via-slate-900/60 to-slate-950 p-4">
            <div className="flex items-center justify-between pb-3 border-b border-blue-500/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg">
                  <Zap className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-blue-400">Burros de Carga (Plowhorses)</h4>
                  <p className="text-2xs text-slate-400">
                    Baixa Margem & Alto Volume ({plowhorseItems.length} pratos)
                  </p>
                </div>
              </div>
              <Badge variant="cyan" className="text-xs">
                Reajustar Preço / Cortar Custo
              </Badge>
            </div>
            <div className="pt-3 space-y-2 max-h-72 overflow-y-auto pr-1">
              {plowhorseItems.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-6 text-center">Nenhum prato nesta categoria</p>
              ) : (
                plowhorseItems.map((item) => (
                  <div
                    key={item.item_id}
                    className="p-2.5 rounded-lg bg-slate-900/80 border border-blue-500/20 flex items-center justify-between hover:border-blue-500/50 transition-colors"
                  >
                    <div>
                      <div className="font-semibold text-sm text-slate-200">{item.name}</div>
                      <div className="text-2xs text-slate-400 flex gap-2 mt-0.5">
                        <span>{item.units_sold} vendas</span>
                        <span>•</span>
                        <span>CMV: {item.cmv_pct.toFixed(1)}%</span>
                        <span>•</span>
                        <span className="text-blue-400 font-medium">Margem: R$ {item.unit_margin.toFixed(2)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => openSimulator(item)}
                      className="px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 text-2xs font-medium flex items-center transition-colors"
                    >
                      <Calculator className="h-3 w-3 mr-1" />
                      Simular
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Quadrant 4: DOGS (Baixa Margem + Baixo Volume) */}
          <div className="rounded-xl border border-rose-500/30 bg-gradient-to-br from-rose-950/20 via-slate-900/60 to-slate-950 p-4">
            <div className="flex items-center justify-between pb-3 border-b border-rose-500/20">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-rose-500/20 text-rose-400 rounded-lg">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-rose-400">Cães (Dogs)</h4>
                  <p className="text-2xs text-slate-400">
                    Baixa Margem & Baixo Volume ({dogItems.length} pratos)
                  </p>
                </div>
              </div>
              <Badge variant="crimson" className="text-xs">
                Eliminar ou Reformular
              </Badge>
            </div>
            <div className="pt-3 space-y-2 max-h-72 overflow-y-auto pr-1">
              {dogItems.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-6 text-center">Nenhum prato nesta categoria</p>
              ) : (
                dogItems.map((item) => (
                  <div
                    key={item.item_id}
                    className="p-2.5 rounded-lg bg-slate-900/80 border border-rose-500/20 flex items-center justify-between hover:border-rose-500/50 transition-colors"
                  >
                    <div>
                      <div className="font-semibold text-sm text-slate-200">{item.name}</div>
                      <div className="text-2xs text-slate-400 flex gap-2 mt-0.5">
                        <span>{item.units_sold} vendas</span>
                        <span>•</span>
                        <span>CMV: {item.cmv_pct.toFixed(1)}%</span>
                        <span>•</span>
                        <span className="text-rose-400 font-medium">Margem: R$ {item.unit_margin.toFixed(2)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => openSimulator(item)}
                      className="px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 text-2xs font-medium flex items-center transition-colors"
                    >
                      <Calculator className="h-3 w-3 mr-1" />
                      Simular
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Engineering Table */}
      <GlassPanel className="p-0 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h4 className="text-base font-bold text-slate-100">Relatório Completo de Engenharia de Menu</h4>
            <p className="text-xs text-slate-400">
              Métricas detalhadas por prato com recomendação estratégica de ação.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
              <input
                placeholder="Buscar prato ou código POS..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-9 w-64 rounded-lg border border-slate-700 bg-slate-900/80 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800 text-xs">
              <button
                className={`h-7 px-2.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === "ALL" ? "bg-amber-500 text-slate-950 font-bold" : "text-slate-400 hover:text-slate-200"
                }`}
                onClick={() => setActiveTab("ALL")}
              >
                Todos ({items.length})
              </button>
              <button
                className={`h-7 px-2.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === "STAR" ? "bg-amber-500/20 text-amber-300 border border-amber-500/30" : "text-slate-400 hover:text-slate-200"
                }`}
                onClick={() => setActiveTab("STAR")}
              >
                ⭐ Estrelas
              </button>
              <button
                className={`h-7 px-2.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === "PLOWHORSE" ? "bg-blue-500/20 text-blue-300 border border-blue-500/30" : "text-slate-400 hover:text-slate-200"
                }`}
                onClick={() => setActiveTab("PLOWHORSE")}
              >
                🐴 Burros
              </button>
              <button
                className={`h-7 px-2.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === "PUZZLE" ? "bg-purple-500/20 text-purple-300 border border-purple-500/30" : "text-slate-400 hover:text-slate-200"
                }`}
                onClick={() => setActiveTab("PUZZLE")}
              >
                ❓ Quebra-Cabeças
              </button>
              <button
                className={`h-7 px-2.5 rounded-md text-xs font-medium transition-colors ${
                  activeTab === "DOG" ? "bg-rose-500/20 text-rose-300 border border-rose-500/30" : "text-slate-400 hover:text-slate-200"
                }`}
                onClick={() => setActiveTab("DOG")}
              >
                🐶 Cães
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-900/60 border-b border-slate-800 text-slate-400">
              <tr>
                <th className="py-3 px-4 font-medium">Classificação</th>
                <th className="py-3 px-4 font-medium">Prato / Categoria</th>
                <th className="py-3 px-4 font-medium text-right">Vendas (Qtd)</th>
                <th className="py-3 px-4 font-medium text-right">Preço Venda</th>
                <th className="py-3 px-4 font-medium text-right">Custo Ficha</th>
                <th className="py-3 px-4 font-medium text-right">Margem Unit.</th>
                <th className="py-3 px-4 font-medium text-right">CMV %</th>
                <th className="py-3 px-4 font-medium text-right">Faturamento Total</th>
                <th className="py-3 px-4 font-medium text-right">Margem Total</th>
                <th className="py-3 px-4 font-medium">Recomendação Estratégica</th>
                <th className="py-3 px-4 font-medium text-center">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-slate-500 italic">
                    Nenhum item encontrado para os filtros selecionados.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => {
                  const badgeClass = {
                    STAR: "bg-amber-500/20 text-amber-300 border-amber-500/30",
                    PLOWHORSE: "bg-blue-500/20 text-blue-300 border-blue-500/30",
                    PUZZLE: "bg-purple-500/20 text-purple-300 border-purple-500/30",
                    DOG: "bg-rose-500/20 text-rose-300 border-rose-500/30",
                  }[item.classification]

                  const label = {
                    STAR: "⭐ Estrela",
                    PLOWHORSE: "🐴 Burro de Carga",
                    PUZZLE: "❓ Quebra-Cabeça",
                    DOG: "🐶 Cão",
                  }[item.classification]

                  return (
                    <tr key={item.item_id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-semibold border ${badgeClass}`}>
                          {label}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-200">{item.name}</div>
                        <div className="text-2xs text-slate-500">
                          {item.category_name} {item.pos_code ? `• ${item.pos_code}` : ""}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-medium text-slate-200">{item.units_sold}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-300">R$ {item.sale_price.toFixed(2)}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-400">R$ {item.cost_price.toFixed(2)}</td>
                      <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-400">
                        R$ {item.unit_margin.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right font-mono">
                        <span
                          className={`font-semibold ${
                            item.cmv_pct > 35
                              ? "text-rose-400"
                              : item.cmv_pct < 25
                              ? "text-emerald-400"
                              : "text-amber-400"
                          }`}
                        >
                          {item.cmv_pct.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-300">R$ {item.total_revenue.toFixed(2)}</td>
                      <td className="py-3 px-4 text-right font-mono font-semibold text-emerald-400">
                        R$ {item.total_margin.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-400 max-w-xs">{item.recommendation}</td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => openSimulator(item)}
                          className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 text-xs font-medium flex items-center mx-auto transition-colors"
                        >
                          <Calculator className="h-3 w-3 mr-1" />
                          Simular
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </GlassPanel>

      {/* Pricing Simulation Modal */}
      {simItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-amber-500/20 text-amber-400 rounded-lg">
                  <Calculator className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-100">Simulador de Precificação</h3>
                  <p className="text-xs text-slate-400">Recalcule CMV % e margem instantaneamente</p>
                </div>
              </div>
              <button
                onClick={() => setSimItem(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1.5">
              <div className="font-bold text-sm text-slate-200">{simItem.name}</div>
              <div className="grid grid-cols-3 gap-2 text-xs pt-1">
                <div>
                  <span className="text-slate-400">Preço Atual:</span>
                  <div className="font-semibold text-slate-200">R$ {simItem.sale_price.toFixed(2)}</div>
                </div>
                <div>
                  <span className="text-slate-400">Custo Ficha:</span>
                  <div className="font-semibold text-slate-200">R$ {simItem.cost_price.toFixed(2)}</div>
                </div>
                <div>
                  <span className="text-slate-400">CMV Atual:</span>
                  <div className="font-semibold text-amber-400">{simItem.cmv_pct.toFixed(1)}%</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Meta CMV %</label>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    step="0.5"
                    min="10"
                    max="90"
                    value={simTargetCmv}
                    onChange={(e) => {
                      setSimTargetCmv(e.target.value)
                      handleSimulateChange(e.target.value, undefined)
                    }}
                    className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                    placeholder="ex: 28.0"
                  />
                  <span className="text-xs font-semibold text-slate-400">%</span>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Ou Novo Preço (R$)</label>
                <div className="flex items-center gap-1">
                  <span className="text-xs font-semibold text-slate-400">R$</span>
                  <input
                    type="number"
                    step="0.50"
                    value={simNewPrice}
                    onChange={(e) => {
                      setSimNewPrice(e.target.value)
                      handleSimulateChange(undefined, e.target.value)
                    }}
                    className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                    placeholder="ex: 45.00"
                  />
                </div>
              </div>
            </div>

            {/* Simulation Result Box */}
            {simResult && (
              <div className="p-4 bg-gradient-to-br from-amber-500/10 via-slate-950 to-slate-950 rounded-lg border border-amber-500/30 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">
                    Resultado da Simulação
                  </span>
                  <Badge variant="amber" className="text-xs font-mono">
                    {simResult.resulting_cmv_pct.toFixed(1)}% CMV
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400">Preço Sugerido / Simulado:</span>
                    <div className="text-base font-bold text-slate-100 font-mono">
                      R$ {simResult.proposed_price.toFixed(2)}
                    </div>
                    <div className="text-2xs text-slate-400 flex items-center gap-0.5 mt-0.5 font-mono">
                      {simResult.price_delta >= 0 ? (
                        <span className="text-emerald-400 flex items-center">
                          <ArrowUpRight className="h-3 w-3" /> +R$ {simResult.price_delta.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-rose-400 flex items-center">
                          <ArrowDownRight className="h-3 w-3" /> R$ {simResult.price_delta.toFixed(2)}
                        </span>
                      )}
                      <span>vs atual</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-slate-400">Nova Margem Unitária:</span>
                    <div className="text-base font-bold text-emerald-400 font-mono">
                      R$ {simResult.proposed_margin.toFixed(2)}
                    </div>
                    <div className="text-2xs text-slate-400 flex items-center gap-0.5 mt-0.5 font-mono">
                      {simResult.margin_delta >= 0 ? (
                        <span className="text-emerald-400 flex items-center">
                          <ArrowUpRight className="h-3 w-3" /> +R$ {simResult.margin_delta.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-rose-400 flex items-center">
                          <ArrowDownRight className="h-3 w-3" /> R$ {simResult.margin_delta.toFixed(2)}
                        </span>
                      )}
                      <span>por unidade</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSimItem(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
