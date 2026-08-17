"use client"

import React, { useState } from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { MenuItem, MenuCategory } from "@/types/menu"
import { RecipeListItem } from "@/types/recipes"
import {
  fetchMenuItemsClient,
  createMenuItemClient,
  updateMenuItemClient,
  deleteMenuItemClient,
  fetchMenuCategoriesClient,
  createMenuCategoryClient,
} from "@/lib/api-client"
import {
  Plus,
  Search,
  BookOpen,
  DollarSign,
  PieChart,
  Edit2,
  Trash2,
  FolderPlus,
  RefreshCw,
  ChefHat,
  X,
  Layers,
  Check,
} from "lucide-react"

interface MenuItemsClientProps {
  initialItems: MenuItem[]
  categories: MenuCategory[]
  recipes: RecipeListItem[]
}

export function MenuItemsClient({
  initialItems,
  categories: initialCategories,
  recipes,
}: MenuItemsClientProps) {
  const [items, setItems] = useState<MenuItem[]>(initialItems)
  const [categories, setCategories] = useState<MenuCategory[]>(initialCategories)
  const [loading, setLoading] = useState(false)

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL")
  const [searchQuery, setSearchQuery] = useState("")

  // Item Modal State
  const [itemModalOpen, setItemModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null)
  const [formData, setFormData] = useState<{
    name: string
    category_id: string
    recipe_id: string
    pos_code: string
    description: string
    sale_price: string
    cost_price: string
    target_cmv_percentage: string
    is_active: boolean
  }>({
    name: "",
    category_id: "",
    recipe_id: "NONE",
    pos_code: "",
    description: "",
    sale_price: "0.00",
    cost_price: "0.00",
    target_cmv_percentage: "30.00",
    is_active: true,
  })

  // Category Modal State
  const [categoryModalOpen, setCategoryModalOpen] = useState(false)
  const [categoryName, setCategoryName] = useState("")

  const reloadData = async () => {
    setLoading(true)
    try {
      const [itemsRes, catsRes] = await Promise.all([
        fetchMenuItemsClient(selectedCategory === "ALL" ? undefined : selectedCategory),
        fetchMenuCategoriesClient(),
      ])
      setItems(itemsRes)
      setCategories(catsRes)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const openCreateModal = () => {
    setEditingItem(null)
    setFormData({
      name: "",
      category_id: categories.length > 0 ? categories[0].id : "",
      recipe_id: "NONE",
      pos_code: "",
      description: "",
      sale_price: "0.00",
      cost_price: "0.00",
      target_cmv_percentage: "30.00",
      is_active: true,
    })
    setItemModalOpen(true)
  }

  const openEditModal = (item: MenuItem) => {
    setEditingItem(item)
    setFormData({
      name: item.name,
      category_id: item.category_id || (categories.length > 0 ? categories[0].id : ""),
      recipe_id: item.recipe_id || "NONE",
      pos_code: item.pos_code || "",
      description: item.description || "",
      sale_price: item.sale_price.toFixed(2),
      cost_price: item.cost_price.toFixed(2),
      target_cmv_percentage: item.target_cmv_percentage.toFixed(2),
      is_active: item.is_active,
    })
    setItemModalOpen(true)
  }

  const handleSaveItem = async () => {
    try {
      const payload = {
        name: formData.name,
        category_id: formData.category_id || undefined,
        recipe_id: formData.recipe_id !== "NONE" ? formData.recipe_id : undefined,
        pos_code: formData.pos_code || undefined,
        description: formData.description || undefined,
        sale_price: parseFloat(formData.sale_price) || 0,
        cost_price: parseFloat(formData.cost_price) || 0,
        target_cmv_percentage: parseFloat(formData.target_cmv_percentage) || 30.0,
        is_active: formData.is_active,
      }

      if (editingItem) {
        await updateMenuItemClient(editingItem.id, payload)
      } else {
        await createMenuItemClient(payload)
      }
      setItemModalOpen(false)
      await reloadData()
    } catch (err) {
      console.error(err)
    }
  }

  const handleDeleteItem = async (id: string) => {
    if (!confirm("Tem certeza que deseja remover este item de cardápio?")) return
    try {
      await deleteMenuItemClient(id)
      await reloadData()
    } catch (err) {
      console.error(err)
    }
  }

  const handleCreateCategory = async () => {
    if (!categoryName.trim()) return
    try {
      await createMenuCategoryClient({ name: categoryName.trim() })
      setCategoryName("")
      setCategoryModalOpen(false)
      await reloadData()
    } catch (err) {
      console.error(err)
    }
  }

  const filteredItems = items.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.pos_code && item.pos_code.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesCategory =
      selectedCategory === "ALL" || item.category_id === selectedCategory
    return matchesSearch && matchesCategory
  })

  // Quick stats
  const totalItems = items.length
  const linkedRecipes = items.filter((i) => !!i.recipe_id).length
  const avgCmv =
    items.length > 0
      ? (items.reduce((acc, i) => acc + i.cmv_pct, 0) / items.length).toFixed(1)
      : "0.0"

  return (
    <div className="space-y-6">
      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassPanel className="p-5">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
            <span>Total de Itens Cadastrados</span>
            <div className="p-2 bg-amber-500/10 rounded-lg text-amber-400">
              <BookOpen className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-100">{totalItems} pratos</div>
          <p className="text-xs text-slate-500 mt-1">
            {categories.length} categorias cadastradas
          </p>
        </GlassPanel>

        <GlassPanel className="p-5">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
            <span>Vinculados à Ficha Técnica</span>
            <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
              <ChefHat className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-400">{linkedRecipes} itens</div>
          <p className="text-xs text-slate-500 mt-1">
            Custo por porção calculado pelo CMP dos insumos
          </p>
        </GlassPanel>

        <GlassPanel className="p-5">
          <div className="flex items-center justify-between text-xs text-slate-400 uppercase tracking-wider font-semibold mb-2">
            <span>CMV Médio Projetado</span>
            <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
              <PieChart className="h-4 w-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-blue-400">{avgCmv}%</div>
          <p className="text-xs text-slate-500 mt-1">
            Com base nos preços de venda e custos atuais
          </p>
        </GlassPanel>
      </div>

      {/* Action Bar */}
      <GlassPanel className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
            <input
              placeholder="Buscar item de cardápio..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-9 w-64 rounded-lg border border-slate-700 bg-slate-900/80 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="h-9 px-3 rounded-lg border border-slate-700 bg-slate-900/80 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
          >
            <option value="ALL">Todas as Categorias</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          <button
            onClick={reloadData}
            disabled={loading}
            className="h-9 px-3.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 font-medium flex items-center transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCategoryModalOpen(true)}
            className="h-9 px-3.5 rounded-lg border border-dashed border-slate-700 hover:border-slate-500 bg-slate-900/50 text-xs font-medium text-slate-300 flex items-center transition-colors"
          >
            <FolderPlus className="h-4 w-4 mr-1.5" />
            Nova Categoria
          </button>

          <button
            onClick={openCreateModal}
            className="h-9 px-4 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 font-bold hover:from-amber-600 hover:to-orange-600 text-xs flex items-center transition-colors shadow-lg shadow-amber-500/20"
          >
            <Plus className="h-4 w-4 mr-1.5" />
            Novo Item de Cardápio
          </button>
        </div>
      </GlassPanel>

      {/* Items Table */}
      <GlassPanel className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-900/60 border-b border-slate-800 text-slate-400">
              <tr>
                <th className="py-3 px-4 font-medium">Nome do Item</th>
                <th className="py-3 px-4 font-medium">Categoria</th>
                <th className="py-3 px-4 font-medium">Cód. POS</th>
                <th className="py-3 px-4 font-medium">Ficha Técnica Vinculada</th>
                <th className="py-3 px-4 font-medium text-right">Custo (R$)</th>
                <th className="py-3 px-4 font-medium text-right">Preço de Venda</th>
                <th className="py-3 px-4 font-medium text-right">Margem Unitária</th>
                <th className="py-3 px-4 font-medium text-right">CMV %</th>
                <th className="py-3 px-4 font-medium text-right">Meta CMV %</th>
                <th className="py-3 px-4 font-medium text-right">Preço Sugerido</th>
                <th className="py-3 px-4 font-medium text-center">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-slate-500 italic">
                    Nenhum item cadastrado. Clique em &quot;Novo Item de Cardápio&quot; para começar.
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-200">{item.name}</div>
                      {item.description && (
                        <div className="text-2xs text-slate-500 truncate max-w-xs">
                          {item.description}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <Badge variant="default" className="text-2xs">
                        {item.category_name || "Geral"}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">
                      {item.pos_code || "—"}
                    </td>
                    <td className="py-3 px-4">
                      {item.recipe_name ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-medium text-xs">
                          <ChefHat className="h-3.5 w-3.5" />
                          {item.recipe_name}
                        </span>
                      ) : (
                        <span className="text-slate-500 italic text-2xs">Custo manual</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-slate-400">
                      R$ {item.cost_price.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-slate-200">
                      R$ {item.sale_price.toFixed(2)}
                    </td>
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
                    <td className="py-3 px-4 text-right font-mono text-slate-400">
                      {item.target_cmv_percentage.toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-amber-400">
                      R$ {item.suggested_price.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          className="p-1 text-slate-400 hover:text-slate-200 transition-colors"
                          onClick={() => openEditModal(item)}
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                        </button>
                        <button
                          className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                          onClick={() => handleDeleteItem(item.id)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </GlassPanel>

      {/* Item Modal (Create/Edit) */}
      {itemModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-amber-500/20 text-amber-400 rounded-lg">
                  <BookOpen className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-100">
                    {editingItem ? "Editar Item de Cardápio" : "Novo Item de Cardápio"}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Cadastre o prato para vendas e vincule à Ficha Técnica de produção.
                  </p>
                </div>
              </div>
              <button onClick={() => setItemModalOpen(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 py-1 text-xs">
              <div className="col-span-2 space-y-1">
                <label className="text-xs font-medium text-slate-300">Nome do Prato / Bebida</label>
                <input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Ex: Picanha Premium Grelhada 300g"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Categoria</label>
                <select
                  value={formData.category_id}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Código no PDV (opcional)</label>
                <input
                  value={formData.pos_code}
                  onChange={(e) => setFormData({ ...formData, pos_code: e.target.value })}
                  placeholder="Ex: POS-102"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs font-mono text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="col-span-2 space-y-1">
                <label className="text-xs font-medium text-slate-300 flex items-center justify-between">
                  <span>Vincular Ficha Técnica (Custo Dinâmico)</span>
                  <span className="text-2xs text-slate-500 font-normal">
                    Recalcula custo por porção em tempo real
                  </span>
                </label>
                <select
                  value={formData.recipe_id}
                  onChange={(e) => setFormData({ ...formData, recipe_id: e.target.value })}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                >
                  <option value="NONE">Sem Ficha Técnica (Custo Manual)</option>
                  {recipes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="col-span-2 space-y-1">
                <label className="text-xs font-medium text-slate-300">Descrição</label>
                <input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Ex: Picanha grelhada com arroz biro-biro e farofa de ovos"
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Preço de Venda (R$)</label>
                <input
                  type="number"
                  step="0.50"
                  value={formData.sale_price}
                  onChange={(e) => setFormData({ ...formData, sale_price: e.target.value })}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">
                  {formData.recipe_id !== "NONE" ? "Custo Ficha (Auto)" : "Custo Unitário (R$)"}
                </label>
                <input
                  type="number"
                  step="0.10"
                  disabled={formData.recipe_id !== "NONE"}
                  value={formData.cost_price}
                  onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500 disabled:opacity-50"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-300">Meta CMV % Desejada</label>
                <input
                  type="number"
                  step="0.5"
                  value={formData.target_cmv_percentage}
                  onChange={(e) => setFormData({ ...formData, target_cmv_percentage: e.target.value })}
                  className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="space-y-1 flex flex-col justify-end">
                <div className="p-2 bg-slate-950 rounded border border-slate-800 text-2xs">
                  <span className="text-slate-400">Preço Sugerido (Meta):</span>
                  <div className="font-bold text-xs text-amber-400 font-mono">
                    R${" "}
                    {parseFloat(formData.target_cmv_percentage) > 0
                      ? (
                          (parseFloat(formData.cost_price) || 0) /
                          (parseFloat(formData.target_cmv_percentage) / 100)
                        ).toFixed(2)
                      : "0.00"}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
              <button
                onClick={() => setItemModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveItem}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 text-xs font-bold hover:from-amber-600 hover:to-orange-600 transition-colors"
              >
                {editingItem ? "Salvar Alterações" : "Criar Item"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Category Modal */}
      {categoryModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FolderPlus className="h-5 w-5 text-amber-400" />
                <h3 className="text-base font-bold text-slate-100">Nova Categoria</h3>
              </div>
              <button onClick={() => setCategoryModalOpen(false)} className="text-slate-400 hover:text-slate-200">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Nome da Categoria</label>
              <input
                value={categoryName}
                onChange={(e) => setCategoryName(e.target.value)}
                placeholder="Ex: Sobremesas Artesanais"
                className="h-9 w-full px-3 rounded-lg border border-slate-700 bg-slate-950 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setCategoryModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateCategory}
                className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-bold transition-colors"
              >
                Criar Categoria
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
