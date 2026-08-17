"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  TrendingUp,
  Plus,
  Layers,
  Utensils,
  AlertTriangle,
  FileSpreadsheet,
  CheckCircle,
  Clock,
  ArrowRight,
  Flame
} from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import {
  SalesImportItem,
  TheoreticalConsumptionItem,
  POSMappingItem,
  LossItem
} from "@/types/sales"
import { RecipeListItem, CatalogSkusAndUoms } from "@/types/recipes"
import {
  importSales,
  createOrUpdatePOSMapping,
  registerLoss
} from "@/lib/api-client"

interface SalesClientProps {
  initialImports: SalesImportItem[]
  initialTheoReport: TheoreticalConsumptionItem[]
  initialMappings: POSMappingItem[]
  recipes: RecipeListItem[]
  initialLosses: LossItem[]
  catalog: CatalogSkusAndUoms
  locations: any[]
}

export default function SalesClient({
  initialImports,
  initialTheoReport,
  initialMappings,
  recipes,
  initialLosses,
  catalog,
  locations
}: SalesClientProps) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<"THEO" | "IMPORTS" | "MAPPINGS" | "LOSSES">("THEO")
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Mapping Form State
  const [posProductId, setPosProductId] = useState("")
  const [posProductName, setPosProductName] = useState("")
  const [selectedRecipeId, setSelectedRecipeId] = useState("")

  // Loss Form State
  const [lossLocationId, setLossLocationId] = useState(locations.length > 0 ? locations[0].id : "")
  const [lossSkuId, setLossSkuId] = useState(catalog.skus[0]?.id || "")
  const [lossQuantity, setLossQuantity] = useState("1.0")
  const [lossReason, setLossReason] = useState("Validade Expirada / Descarte")
  const [lossActor, setLossActor] = useState("Cozinha Principal")

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const handleSimulateSalesImport = async () => {
    setIsSubmitting(true)
    const randomBatch = Math.floor(Math.random() * 9000 + 1000)
    
    // Choose available recipe/mappings or use generic
    const targetPosId = initialMappings[0]?.pos_product_id || "POS_BURGER_01"

    const payload = {
      pos_system: "TOAST_POS",
      import_reference: `LOTE_PDV_${randomBatch}`,
      sales: [
        {
          pos_sale_id: `SAT_${randomBatch}_1`,
          sale_date: new Date().toISOString(),
          total_amount: 145.00,
          lines: [
            {
              pos_product_id: targetPosId,
              quantity: 4,
              unit_price: 35.00
            }
          ]
        },
        {
          pos_sale_id: `SAT_${randomBatch}_2`,
          sale_date: new Date().toISOString(),
          total_amount: 70.00,
          lines: [
            {
              pos_product_id: targetPosId,
              quantity: 2,
              unit_price: 35.00
            }
          ]
        }
      ]
    }

    const result = await importSales(payload)
    setIsSubmitting(false)

    if (result) {
      alert(`Vendas do lote ${payload.import_reference} importadas com sucesso! Consumo teórico calculado.`)
      router.refresh()
    } else {
      alert("Falha ao importar lote de vendas.")
    }
  }

  const handleSaveMapping = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!posProductId || !posProductName) {
      alert("Preencha o Código e Nome do Produto no PDV.")
      return
    }

    setIsSubmitting(true)
    const result = await createOrUpdatePOSMapping({
      pos_product_id: posProductId,
      pos_product_name: posProductName,
      recipe_id: selectedRecipeId || null
    })
    setIsSubmitting(false)

    if (result) {
      alert("Mapeamento com Ficha Técnica salvo com sucesso!")
      setPosProductId("")
      setPosProductName("")
      setSelectedRecipeId("")
      router.refresh()
    } else {
      alert("Falha ao salvar mapeamento.")
    }
  }

  const handleRegisterLoss = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!lossSkuId || !lossLocationId || parseFloat(lossQuantity) <= 0) {
      alert("Selecione um Local, um SKU e informe uma quantidade válida.")
      return
    }

    setIsSubmitting(true)
    const result = await registerLoss({
      location_id: lossLocationId,
      sku_id: lossSkuId,
      quantity: parseFloat(lossQuantity),
      reason: lossReason,
      actor: lossActor
    })
    setIsSubmitting(false)

    if (result) {
      alert("Perda / Desperdício registrado no estoque com sucesso!")
      setLossQuantity("1.0")
      router.refresh()
    } else {
      alert("Falha ao registrar perda.")
    }
  }

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-2 bg-slate-900/50 p-1 rounded-xl w-fit border border-slate-800">
        <button
          onClick={() => setActiveTab("THEO")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "THEO"
              ? "bg-slate-800 text-[#00f0ff] shadow-lg shadow-cyan-950/50"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <span className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" /> Teórico vs Real & Perdas
          </span>
        </button>

        <button
          onClick={() => setActiveTab("IMPORTS")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "IMPORTS"
              ? "bg-slate-800 text-[#a855f7] shadow-lg shadow-purple-950/50"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <span className="flex items-center gap-2">
            <FileSpreadsheet className="h-4 w-4" /> Importações de Vendas (PDV)
          </span>
        </button>

        <button
          onClick={() => setActiveTab("MAPPINGS")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "MAPPINGS"
              ? "bg-slate-800 text-amber-400 shadow-lg shadow-amber-950/50"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <span className="flex items-center gap-2">
            <Layers className="h-4 w-4" /> De-Para PDV / Ficha Técnica
          </span>
        </button>

        <button
          onClick={() => setActiveTab("LOSSES")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === "LOSSES"
              ? "bg-slate-800 text-rose-400 shadow-lg shadow-rose-950/50"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <span className="flex items-center gap-2">
            <Flame className="h-4 w-4" /> Registro de Perdas (Quebras)
          </span>
        </button>
      </div>

      {/* TAB 1: Theoretical vs Actual */}
      {activeTab === "THEO" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">
              Cálculo em tempo real da baixa de insumos esperada pela Engenharia de Cardápio versus perdas declaradas.
            </p>
            <button
              onClick={handleSimulateSalesImport}
              disabled={isSubmitting}
              className="bg-[#00f0ff] text-slate-950 px-4 py-2 rounded-xl text-sm font-semibold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              {isSubmitting ? "Processando Vendas..." : "Simular Vendas do Turno (PDV)"}
            </button>
          </div>

          <GlassPanel className="p-0 overflow-x-auto border-cyan-500/20">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 font-semibold">Insumo (SKU)</th>
                  <th className="px-6 py-4 font-semibold text-right">Consumo Teórico (Receitas)</th>
                  <th className="px-6 py-4 font-semibold text-right">Perdas Registradas</th>
                  <th className="px-6 py-4 font-semibold text-right">Descarte Total Esperado</th>
                  <th className="px-6 py-4 font-semibold text-right">Custo Teórico Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50 text-slate-300">
                {initialTheoReport.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                      Nenhum consumo teórico registrado ainda. Importe vendas do PDV acima.
                    </td>
                  </tr>
                ) : (
                  initialTheoReport.map((item) => (
                    <tr key={item.sku_id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-100">{item.sku_name}</td>
                      <td className="px-6 py-4 text-right font-mono text-[#00f0ff]">
                        {Number(item.theoretical_quantity).toFixed(3)} {item.uom_symbol}
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-rose-400">
                        {Number(item.registered_losses_quantity).toFixed(3)} {item.uom_symbol}
                      </td>
                      <td className="px-6 py-4 text-right font-mono font-bold text-amber-300">
                        {Number(item.total_expected_depletion).toFixed(3)} {item.uom_symbol}
                      </td>
                      <td className="px-6 py-4 text-right font-bold text-slate-100">
                        {formatCurrency(Number(item.theoretical_cost))}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </GlassPanel>
        </div>
      )}

      {/* TAB 2: Imports List */}
      {activeTab === "IMPORTS" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={handleSimulateSalesImport}
              disabled={isSubmitting}
              className="bg-[#a855f7] text-slate-100 px-4 py-2 rounded-xl text-sm font-semibold shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:shadow-[0_0_25px_rgba(168,85,247,0.5)] transition-all flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              {isSubmitting ? "Importando..." : "Nova Ingestão de Vendas (Simulação)"}
            </button>
          </div>

          <GlassPanel className="p-0 overflow-x-auto border-purple-500/20">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 font-semibold">Referência do Lote</th>
                  <th className="px-6 py-4 font-semibold">Sistema de PDV</th>
                  <th className="px-6 py-4 font-semibold">Status</th>
                  <th className="px-6 py-4 font-semibold text-right">Qtd Cupons</th>
                  <th className="px-6 py-4 font-semibold text-right">Data/Hora</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50 text-slate-300">
                {initialImports.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                      Nenhum lote de vendas importado.
                    </td>
                  </tr>
                ) : (
                  initialImports.map((imp) => (
                    <tr key={imp.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 font-mono font-medium text-slate-200">{imp.import_reference}</td>
                      <td className="px-6 py-4 text-slate-300">{imp.pos_system}</td>
                      <td className="px-6 py-4">
                        <Badge variant="emerald">
                          <CheckCircle className="h-3 w-3 mr-1" /> {imp.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-slate-200">{imp.sales_count}</td>
                      <td className="px-6 py-4 text-right text-slate-400">
                        {new Date(imp.created_at).toLocaleString("pt-BR")}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </GlassPanel>
        </div>
      )}

      {/* TAB 3: POS Mappings */}
      {activeTab === "MAPPINGS" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Mapping Form */}
          <GlassPanel className="p-5 flex flex-col space-y-4 lg:col-span-1 border-amber-500/20">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Layers className="h-5 w-5 text-amber-400" />
              Mapear Item do PDV
            </h3>
            <p className="text-xs text-slate-400">
              Vincule um código de produto do seu PDV (ex: Toast, Linx, Saipos) à Ficha Técnica correspondente.
            </p>

            <form onSubmit={handleSaveMapping} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Código no PDV (SKU/ID)
                </label>
                <input
                  type="text"
                  placeholder="ex: POS_BURGER_01"
                  value={posProductId}
                  onChange={(e) => setPosProductId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-amber-400 outline-none"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Nome do Item no PDV
                </label>
                <input
                  type="text"
                  placeholder="ex: Burger Clássico Duplo"
                  value={posProductName}
                  onChange={(e) => setPosProductName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-amber-400 outline-none"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Ficha Técnica Vinculada
                </label>
                <select
                  value={selectedRecipeId}
                  onChange={(e) => setSelectedRecipeId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-amber-400 outline-none"
                >
                  <option value="">-- Sem vínculo (Não consome insumos) --</option>
                  {recipes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} ({r.type})
                    </option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full mt-2 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold py-2 rounded-xl text-sm transition-all shadow-[0_0_15px_rgba(251,191,36,0.3)]"
              >
                {isSubmitting ? "Salvando..." : "Salvar Mapeamento"}
              </button>
            </form>
          </GlassPanel>

          {/* Mappings Table */}
          <GlassPanel className="p-0 overflow-x-auto lg:col-span-2 border-amber-500/20">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 font-semibold">Código PDV</th>
                  <th className="px-6 py-4 font-semibold">Nome no PDV</th>
                  <th className="px-6 py-4 font-semibold">Ficha Técnica</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50 text-slate-300">
                {initialMappings.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-6 py-8 text-center text-slate-500">
                      Nenhum mapeamento de produto cadastrado.
                    </td>
                  </tr>
                ) : (
                  initialMappings.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 font-mono text-amber-300">{m.pos_product_id}</td>
                      <td className="px-6 py-4 font-medium text-slate-100">{m.pos_product_name}</td>
                      <td className="px-6 py-4">
                        {m.recipe_name ? (
                          <Badge variant="cyan">{m.recipe_name}</Badge>
                        ) : (
                          <Badge variant="default">Sem Ficha</Badge>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </GlassPanel>
        </div>
      )}

      {/* TAB 4: Losses / Waste */}
      {activeTab === "LOSSES" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Loss Registration Form */}
          <GlassPanel className="p-5 flex flex-col space-y-4 lg:col-span-1 border-rose-500/20">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Flame className="h-5 w-5 text-rose-400" />
              Lançar Quebra / Desperdício
            </h3>
            <p className="text-xs text-slate-400">
              Registra uma perda física imediata de estoque com justificativa e responsável.
            </p>

            <form onSubmit={handleRegisterLoss} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Local de Estoque
                </label>
                <select
                  value={lossLocationId}
                  onChange={(e) => setLossLocationId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-rose-400 outline-none"
                  required
                >
                  <option value="">Selecione o local...</option>
                  {locations.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Insumo (SKU)
                </label>
                <select
                  value={lossSkuId}
                  onChange={(e) => setLossSkuId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-rose-400 outline-none"
                  required
                >
                  {catalog.skus.map((sku) => (
                    <option key={sku.id} value={sku.id}>
                      {sku.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Quantidade Desperdiçada
                </label>
                <input
                  type="number"
                  step="0.001"
                  min="0.001"
                  value={lossQuantity}
                  onChange={(e) => setLossQuantity(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-rose-400 outline-none"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Motivo da Perda
                </label>
                <select
                  value={lossReason}
                  onChange={(e) => setLossReason(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-rose-400 outline-none"
                >
                  <option value="Validade Expirada / Descarte">Validade Expirada / Descarte</option>
                  <option value="Erro de Manipulação / Cozinha">Erro de Manipulação / Cozinha</option>
                  <option value="Armazenamento Incorreto / Refrigeração">Armazenamento Incorreto / Refrigeração</option>
                  <option value="Avaria de Embalagem / Transporte">Avaria de Embalagem / Transporte</option>
                  <option value="Degustação / Treinamento">Degustação / Treinamento</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Responsável / Operador
                </label>
                <input
                  type="text"
                  placeholder="ex: Cozinha Principal"
                  value={lossActor}
                  onChange={(e) => setLossActor(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-rose-400 outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full mt-2 bg-rose-500 hover:bg-rose-400 text-white font-bold py-2 rounded-xl text-sm transition-all shadow-[0_0_15px_rgba(244,63,94,0.3)]"
              >
                {isSubmitting ? "Registrando..." : "Baixar Estoque por Perda"}
              </button>
            </form>
          </GlassPanel>

          {/* Losses Table */}
          <GlassPanel className="p-0 overflow-x-auto lg:col-span-2 border-rose-500/20">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 font-semibold">Insumo</th>
                  <th className="px-6 py-4 font-semibold text-right">Qtd Perda</th>
                  <th className="px-6 py-4 font-semibold">Motivo</th>
                  <th className="px-6 py-4 font-semibold">Responsável</th>
                  <th className="px-6 py-4 font-semibold text-right">Data</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50 text-slate-300">
                {initialLosses.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                      Nenhuma quebra ou perda registrada.
                    </td>
                  </tr>
                ) : (
                  initialLosses.map((loss) => (
                    <tr key={loss.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-100">{loss.sku_name || "SKU"}</td>
                      <td className="px-6 py-4 text-right font-mono text-rose-400 font-bold">
                        {Number(loss.quantity).toFixed(3)}
                      </td>
                      <td className="px-6 py-4 text-slate-300">{loss.reason}</td>
                      <td className="px-6 py-4 text-slate-400">{loss.actor || "—"}</td>
                      <td className="px-6 py-4 text-right text-slate-400">
                        {loss.created_at ? new Date(loss.created_at).toLocaleDateString("pt-BR") : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </GlassPanel>
        </div>
      )}
    </div>
  )
}
