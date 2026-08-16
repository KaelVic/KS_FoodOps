"use client"

import { useState, useMemo } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Plus, Search, Eye, ChefHat, Package, X, Trash2, ArrowRight } from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"

import {
  RecipeListItem,
  CatalogSkusAndUoms,
  RecipeDetailItem,
  RecipeIngredientInput
} from "@/types/recipes"

import { createRecipe, publishRecipeVersion, fetchRecipeDetail } from "@/lib/api-client"
import { RecipeCostSimulator } from "@/components/recipes/RecipeCostSimulator"
import { RecipeKitchenSheet } from "@/components/recipes/RecipeKitchenSheet"

interface RecipesClientProps {
  initialRecipes: RecipeListItem[]
  initialCatalog: CatalogSkusAndUoms
}

export default function RecipesClient({ initialRecipes, initialCatalog }: RecipesClientProps) {
  const router = useRouter()
  
  const [recipes, setRecipes] = useState<RecipeListItem[]>(initialRecipes)
  const [activeTab, setActiveTab] = useState<"ALL" | "MENU_ITEM" | "PREPARED_ITEM">("ALL")
  const [searchTerm, setSearchTerm] = useState("")
  
  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [detailRecipe, setDetailRecipe] = useState<RecipeDetailItem | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [showKitchenSheet, setShowKitchenSheet] = useState(false)

  // Create Form State
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formName, setFormName] = useState("")
  const [formType, setFormType] = useState<"MENU_ITEM" | "PREPARED_ITEM">("MENU_ITEM")
  const [formPosCode, setFormPosCode] = useState("")
  
  const [formYield, setFormYield] = useState<number>(1)
  const [formYieldUom, setFormYieldUom] = useState<string>("")
  const [formPortionSize, setFormPortionSize] = useState<number>(1)
  const [formPortionUom, setFormPortionUom] = useState<string>("")
  
  const [ingredients, setIngredients] = useState<RecipeIngredientInput[]>([])

  const filteredRecipes = useMemo(() => {
    let result = recipes
    if (activeTab !== "ALL") {
      result = result.filter(r => r.type === activeTab)
    }
    if (searchTerm.trim()) {
      const lower = searchTerm.toLowerCase()
      result = result.filter(r => 
        r.name.toLowerCase().includes(lower) || 
        (r.pos_code && r.pos_code.toLowerCase().includes(lower))
      )
    }
    return result
  }, [recipes, activeTab, searchTerm])

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const handleOpenDetail = async (id: string) => {
    setIsLoadingDetail(true)
    const detail = await fetchRecipeDetail(id)
    if (detail) {
      setDetailRecipe(detail)
    }
    setIsLoadingDetail(false)
  }

  const handleAddIngredient = () => {
    setIngredients([...ingredients, { sku_id: "", quantity: 0, uom_id: "", loss_percentage: 0 }])
  }

  const handleUpdateIngredient = (index: number, field: keyof RecipeIngredientInput, value: any) => {
    const newIngs = [...ingredients]
    newIngs[index] = { ...newIngs[index], [field]: value }
    setIngredients(newIngs)
  }

  const handleRemoveIngredient = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index))
  }

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    try {
      const created = await createRecipe({
        name: formName,
        type: formType,
        pos_code: formPosCode || undefined
      })
      if (created) {
        await publishRecipeVersion(created.id, {
          yield_quantity: formYield,
          yield_uom_id: formYieldUom,
          portion_size: formPortionSize,
          portion_uom_id: formPortionUom,
          ingredients: ingredients.filter(i => i.sku_id && i.uom_id && i.quantity > 0)
        })
        
        // Optimistic refresh
        router.refresh()
        setIsCreateOpen(false)
        resetForm()
      }
    } catch (err) {
      console.error(err)
      alert("Erro ao criar ficha técnica")
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetForm = () => {
    setFormName("")
    setFormPosCode("")
    setFormType("MENU_ITEM")
    setFormYield(1)
    setFormYieldUom("")
    setFormPortionSize(1)
    setFormPortionUom("")
    setIngredients([])
  }

  // Calculate reactive portion cost
  const reactivePortionCost = useMemo(() => {
    // This is just an estimate based on selected SKUs if we had the SKU costs locally. 
    // Since we don't have catalog costs in initialCatalog right now, we just mock 0 or a placeholder.
    return 0
  }, [ingredients])

  return (
    <div className="space-y-6">
      {/* Tabs & Actions */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div className="flex bg-slate-800/50 p-1 rounded-xl border border-slate-700 w-fit">
          <button
            onClick={() => setActiveTab("ALL")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "ALL" ? "bg-slate-700 text-white shadow" : "text-slate-400 hover:text-slate-300"
            }`}
          >
            Todos
          </button>
          <button
            onClick={() => setActiveTab("MENU_ITEM")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "MENU_ITEM" ? "bg-slate-700 text-white shadow" : "text-slate-400 hover:text-slate-300"
            }`}
          >
            Pratos (Menu)
          </button>
          <button
            onClick={() => setActiveTab("PREPARED_ITEM")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === "PREPARED_ITEM" ? "bg-slate-700 text-white shadow" : "text-slate-400 hover:text-slate-300"
            }`}
          >
            Pré-preparos
          </button>
        </div>

        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900/50 border border-slate-700 rounded-xl pl-10 pr-4 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 transition-all"
            placeholder="Buscar receita por nome ou PDV..."
          />
        </div>

        <button
          onClick={() => { resetForm(); setIsCreateOpen(true); }}
          className="bg-[#00f0ff] text-slate-950 px-4 py-2 rounded-xl font-semibold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all flex items-center justify-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Nova Ficha Técnica
        </button>
      </div>

      {/* Data Grid / Table */}
      <GlassPanel className="p-0 overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
            <tr>
              <th className="px-6 py-4 font-semibold">Nome</th>
              <th className="px-6 py-4 font-semibold">Tipo</th>
              <th className="px-6 py-4 font-semibold">Código PDV</th>
              <th className="px-6 py-4 font-semibold text-center">Versão</th>
              <th className="px-6 py-4 font-semibold text-center">Qtd. Ingr.</th>
              <th className="px-6 py-4 font-semibold text-right">Custo Porção</th>
              <th className="px-6 py-4 font-semibold text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 text-slate-300">
            {filteredRecipes.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                  Nenhuma ficha técnica encontrada.
                </td>
              </tr>
            ) : (
              filteredRecipes.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-medium text-slate-100 flex items-center gap-3">
                    {r.type === "MENU_ITEM" ? (
                      <ChefHat className="h-4 w-4 text-[#a855f7]" />
                    ) : (
                      <Package className="h-4 w-4 text-[#f59e0b]" />
                    )}
                    {r.name}
                  </td>
                  <td className="px-6 py-4">
                    {r.type === "MENU_ITEM" ? (
                      <Badge variant="violet">Prato Principal</Badge>
                    ) : (
                      <Badge variant="amber">Pré-preparo</Badge>
                    )}
                  </td>
                  <td className="px-6 py-4 font-mono text-slate-400">{r.pos_code || "-"}</td>
                  <td className="px-6 py-4 text-center">
                    {r.version_number ? (
                      <Badge variant="cyan">v{r.version_number}</Badge>
                    ) : (
                      <span className="text-slate-500 text-xs">Sem versão</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">{r.ingredients_count}</td>
                  <td className="px-6 py-4 text-right font-medium text-[#34d399]">
                    {formatCurrency(r.portion_cost)}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleOpenDetail(r.id)}
                      disabled={isLoadingDetail}
                      className="text-slate-400 hover:text-[#00f0ff] transition-colors p-2"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </GlassPanel>

      {/* Details Modal */}
      <AnimatePresence>
        {detailRecipe && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl"
            >
              <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-800/30">
                <div>
                  <h3 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
                    {detailRecipe.name}
                    {detailRecipe.version_number && (
                      <Badge variant="cyan">v{detailRecipe.version_number}</Badge>
                    )}
                  </h3>
                  <div className="flex items-center gap-2 mt-2 text-sm text-slate-400">
                    <span className="font-mono">{detailRecipe.pos_code || "Sem PDV"}</span>
                    <span>&bull;</span>
                    <span>{detailRecipe.type === "MENU_ITEM" ? "Prato Principal" : "Pré-preparo"}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowKitchenSheet(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg transition-colors border border-slate-700"
                  >
                    <ChefHat className="h-4 w-4" />
                    Ficha de Cozinha
                  </button>
                  <button
                    onClick={() => setDetailRecipe(null)}
                    className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="p-6 overflow-y-auto flex-1 grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Ingredients & Cost Share */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="grid grid-cols-3 gap-4">
                    <GlassPanel className="p-4" accent="cyan">
                      <p className="text-xs text-slate-400 mb-1">Rendimento</p>
                      <p className="font-bold text-xl text-slate-100">{detailRecipe.yield_quantity}</p>
                    </GlassPanel>
                    <GlassPanel className="p-4" accent="violet">
                      <p className="text-xs text-slate-400 mb-1">Porção</p>
                      <p className="font-bold text-xl text-slate-100">{detailRecipe.portion_size}</p>
                    </GlassPanel>
                    <GlassPanel className="p-4 flex flex-col justify-center">
                      <p className="text-xs text-slate-400 mb-1">Ingredientes</p>
                      <p className="font-bold text-xl text-slate-100">{detailRecipe.ingredients?.length || 0}</p>
                    </GlassPanel>
                  </div>

                  <div>
                    <h4 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
                      <Package className="h-5 w-5 text-emerald-400" />
                      Decomposição Analítica
                    </h4>
                    <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-800/20">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-slate-800/50 text-slate-400">
                          <tr>
                            <th className="p-4">Ingrediente</th>
                            <th className="p-4 text-right">Qtd</th>
                            <th className="p-4 text-right">Perda</th>
                            <th className="p-4 text-right">Custo Un.</th>
                            <th className="p-4 text-right text-slate-200">Custo Total</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                          {detailRecipe.ingredients?.map((ing, idx) => (
                            <tr key={idx} className="hover:bg-slate-800/30">
                              <td className="p-4 text-slate-300 font-medium truncate max-w-[150px]">{ing.sku_name}</td>
                              <td className="p-4 text-right font-mono text-slate-400">{ing.quantity} <span className="text-xs">{ing.uom_symbol}</span></td>
                              <td className="p-4 text-right text-slate-400">{ing.loss_percentage}%</td>
                              <td className="p-4 text-right text-slate-400">{formatCurrency(ing.unit_cost)}</td>
                              <td className="p-4 text-right font-medium text-emerald-400">{formatCurrency(ing.total_cost)}</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot className="bg-slate-800/30 border-t border-slate-700">
                          <tr>
                            <td colSpan={4} className="p-4 text-right font-medium text-slate-300">Custo Total do Lote:</td>
                            <td className="p-4 text-right font-bold text-emerald-400">
                              {formatCurrency(detailRecipe.ingredients?.reduce((sum, ing) => sum + ing.total_cost, 0) || 0)}
                            </td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  </div>
                  
                  {/* Cost Share Visualizer */}
                  {detailRecipe.ingredients && detailRecipe.ingredients.length > 0 && (
                    <div className="bg-slate-800/30 p-5 rounded-xl border border-slate-700/50">
                      <h4 className="text-sm font-semibold text-slate-300 mb-4">Impacto de Custo por Ingrediente</h4>
                      <div className="flex h-4 rounded-full overflow-hidden bg-slate-900 mb-3">
                        {(() => {
                           const totalBatchCost = detailRecipe.ingredients.reduce((sum, ing) => sum + ing.total_cost, 0)
                           const colors = ["bg-cyan-500", "bg-violet-500", "bg-emerald-500", "bg-rose-500", "bg-amber-500", "bg-blue-500"]
                           return detailRecipe.ingredients
                             .sort((a,b) => b.total_cost - a.total_cost)
                             .map((ing, idx) => {
                               const pct = totalBatchCost > 0 ? (ing.total_cost / totalBatchCost) * 100 : 0
                               return (
                                 <div 
                                   key={idx} 
                                   style={{ width: `${pct}%` }} 
                                   className={`${colors[idx % colors.length]} hover:brightness-110 transition-all cursor-crosshair`}
                                   title={`${ing.sku_name}: ${pct.toFixed(1)}%`}
                                 />
                               )
                             })
                        })()}
                      </div>
                      <div className="flex flex-wrap gap-3">
                        {(() => {
                           const totalBatchCost = detailRecipe.ingredients.reduce((sum, ing) => sum + ing.total_cost, 0)
                           const colors = ["text-cyan-400", "text-violet-400", "text-emerald-400", "text-rose-400", "text-amber-400", "text-blue-400"]
                           return detailRecipe.ingredients
                             .sort((a,b) => b.total_cost - a.total_cost)
                             .slice(0, 4) // Show top 4
                             .map((ing, idx) => {
                               const pct = totalBatchCost > 0 ? (ing.total_cost / totalBatchCost) * 100 : 0
                               return (
                                 <div key={idx} className="flex items-center gap-1 text-xs text-slate-400">
                                   <div className={`w-2 h-2 rounded-full ${colors[idx % colors.length].replace('text-', 'bg-')}`} />
                                   <span className="truncate max-w-[100px]">{ing.sku_name}</span>
                                   <span className="font-medium text-slate-300">({pct.toFixed(1)}%)</span>
                                 </div>
                               )
                             })
                        })()}
                        {detailRecipe.ingredients.length > 4 && (
                           <div className="flex items-center gap-1 text-xs text-slate-500">
                             + {detailRecipe.ingredients.length - 4} outros
                           </div>
                        )}
                      </div>
                    </div>
                  )}

                </div>

                {/* Right Column: Simulator */}
                <div>
                   <RecipeCostSimulator
                     recipeType={detailRecipe.type as any}
                     totalBatchCost={detailRecipe.ingredients?.reduce((sum, ing) => sum + ing.total_cost, 0) || 0}
                     yieldQuantity={detailRecipe.yield_quantity || 1}
                     portionSize={detailRecipe.portion_size || 1}
                   />
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Create Modal */}
      <AnimatePresence>
        {isCreateOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
          >
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 20, opacity: 0 }}
              className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl"
            >
              <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-800/30">
                <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <Plus className="h-5 w-5 text-[#00f0ff]" />
                  Nova Ficha Técnica
                </h3>
                <button
                  onClick={() => setIsCreateOpen(false)}
                  className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                <form id="create-recipe-form" onSubmit={handleCreateSubmit} className="space-y-8">
                  {/* Basic Info */}
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Informações Básicas</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Nome da Receita</label>
                        <input
                          required
                          value={formName}
                          onChange={(e) => setFormName(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 focus:outline-none focus:border-[#00f0ff] focus:ring-1 focus:ring-[#00f0ff] transition-all"
                          placeholder="Ex: Hambúrguer Clássico"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Tipo</label>
                        <select
                          value={formType}
                          onChange={(e) => setFormType(e.target.value as any)}
                          className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 focus:outline-none focus:border-[#00f0ff] focus:ring-1 focus:ring-[#00f0ff] transition-all"
                        >
                          <option value="MENU_ITEM">Prato (Item de Menu)</option>
                          <option value="PREPARED_ITEM">Pré-preparo (Base)</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Código PDV (Opcional)</label>
                        <input
                          value={formPosCode}
                          onChange={(e) => setFormPosCode(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100 focus:outline-none focus:border-[#00f0ff] focus:ring-1 focus:ring-[#00f0ff] transition-all"
                          placeholder="Ex: 1001"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Yield & Portion */}
                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Rendimento e Porção</h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Rendimento (Qtd)</label>
                        <input
                          required
                          type="number" step="0.01" min="0"
                          value={formYield}
                          onChange={(e) => setFormYield(parseFloat(e.target.value))}
                          className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Unid. Rendimento</label>
                        <select
                          required
                          value={formYieldUom}
                          onChange={(e) => setFormYieldUom(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100"
                        >
                          <option value="">Selecione...</option>
                          {initialCatalog.uoms.map((u) => (
                            <option key={u.id} value={u.id}>{u.name} ({u.symbol})</option>
                          ))}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Tamanho da Porção</label>
                        <input
                          required
                          type="number" step="0.01" min="0"
                          value={formPortionSize}
                          onChange={(e) => setFormPortionSize(parseFloat(e.target.value))}
                          className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">Unid. Porção</label>
                        <select
                          required
                          value={formPortionUom}
                          onChange={(e) => setFormPortionUom(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-100"
                        >
                          <option value="">Selecione...</option>
                          {initialCatalog.uoms.map((u) => (
                            <option key={u.id} value={u.id}>{u.name} ({u.symbol})</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Ingredients */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Ingredientes da Receita</h4>
                      <button
                        type="button"
                        onClick={handleAddIngredient}
                        className="text-sm text-[#00f0ff] hover:text-cyan-300 font-medium flex items-center gap-1"
                      >
                        <Plus className="h-4 w-4" /> Adicionar Linha
                      </button>
                    </div>
                    
                    <div className="border border-slate-700 rounded-xl overflow-hidden">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
                          <tr>
                            <th className="p-3">SKU (Ingrediente)</th>
                            <th className="p-3">Quantidade</th>
                            <th className="p-3">Unidade (UOM)</th>
                            <th className="p-3">Perda (%)</th>
                            <th className="p-3"></th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {ingredients.length === 0 && (
                            <tr>
                              <td colSpan={5} className="p-6 text-center text-slate-500">
                                Nenhum ingrediente adicionado.
                              </td>
                            </tr>
                          )}
                          {ingredients.map((ing, idx) => (
                            <tr key={idx} className="bg-slate-950/50">
                              <td className="p-3">
                                <select
                                  required
                                  value={ing.sku_id}
                                  onChange={(e) => handleUpdateIngredient(idx, "sku_id", e.target.value)}
                                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                  <option value="">Selecionar SKU...</option>
                                  {initialCatalog.skus.map(s => (
                                    <option key={s.id} value={s.id}>{s.name}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="p-3">
                                <input
                                  required
                                  type="number" step="0.0001" min="0"
                                  value={ing.quantity || ""}
                                  onChange={(e) => handleUpdateIngredient(idx, "quantity", parseFloat(e.target.value))}
                                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                  placeholder="0.0"
                                />
                              </td>
                              <td className="p-3">
                                <select
                                  required
                                  value={ing.uom_id}
                                  onChange={(e) => handleUpdateIngredient(idx, "uom_id", e.target.value)}
                                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                >
                                  <option value="">Unidade...</option>
                                  {initialCatalog.uoms.map(u => (
                                    <option key={u.id} value={u.id}>{u.symbol}</option>
                                  ))}
                                </select>
                              </td>
                              <td className="p-3">
                                <input
                                  type="number" step="0.1" min="0" max="100"
                                  value={ing.loss_percentage || 0}
                                  onChange={(e) => handleUpdateIngredient(idx, "loss_percentage", parseFloat(e.target.value))}
                                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200"
                                />
                              </td>
                              <td className="p-3 text-right">
                                <button
                                  type="button"
                                  onClick={() => handleRemoveIngredient(idx)}
                                  className="text-slate-500 hover:text-red-400 p-1 transition-colors"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </form>
              </div>

              <div className="p-6 border-t border-slate-800 bg-slate-900 flex items-center justify-between">
                <div className="text-slate-400 text-sm">
                  Custo da Porção Estimado: <span className="text-[#34d399] font-bold text-lg">{formatCurrency(reactivePortionCost)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setIsCreateOpen(false)}
                    className="px-4 py-2 rounded-xl text-slate-300 font-medium hover:bg-slate-800 transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    form="create-recipe-form"
                    disabled={isSubmitting || ingredients.length === 0}
                    className="bg-[#00f0ff] text-slate-950 px-6 py-2 rounded-xl font-bold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? "Salvando..." : "Salvar e Publicar"}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Kitchen Sheet Print Modal */}
      {showKitchenSheet && detailRecipe && (
        <RecipeKitchenSheet
          recipe={detailRecipe}
          onClose={() => setShowKitchenSheet(false)}
        />
      )}
    </div>
  )
}
