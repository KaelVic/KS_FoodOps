"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { 
  ClipboardList, 
  CheckCircle, 
  Search, 
  AlertTriangle, 
  ArrowLeft, 
  ScanLine, 
  Info, 
  TrendingDown, 
  TrendingUp,
  Check,
  Clock,
  Sparkles,
  ArrowRight
} from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { InventorySessionDetail, CloseResultItem } from "@/types/inventory-sessions"
import { CatalogSkusAndUoms } from "@/types/recipes"
import { addCountLine, closeInventorySession, fetchCloseResults } from "@/lib/api-client"

export default function SessionDetailClient({ 
  initialDetail, 
  catalog 
}: { 
  initialDetail: InventorySessionDetail
  catalog: CatalogSkusAndUoms
}) {
  const router = useRouter()
  const [session, setSession] = useState(initialDetail)
  const [searchTerm, setSearchTerm] = useState("")
  const [activeFilter, setActiveFilter] = useState<"all" | "pending" | "counted">("all")
  const [inputQuantities, setInputQuantities] = useState<Record<string, string>>({})
  const [savedStatus, setSavedStatus] = useState<Record<string, boolean>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [closeResults, setCloseResults] = useState<CloseResultItem[]>([])
  const [showConfirmModal, setShowConfirmModal] = useState(false)

  // Load initial counts into input map
  useEffect(() => {
    const map: Record<string, string> = {}
    const saved: Record<string, boolean> = {}
    session.lines.forEach(line => {
      map[line.sku_id] = line.counted_quantity.toString()
      saved[line.sku_id] = true
    })
    setInputQuantities(map)
    setSavedStatus(saved)
  }, [session.lines])

  // Fetch results if closed
  useEffect(() => {
    if (session.status === "CLOSED") {
      fetchCloseResults(session.id).then(res => setCloseResults(res))
    }
  }, [session.status, session.id])

  // Computed counts for progress
  const totalSkus = catalog.skus.length
  const countedSkusCount = useMemo(() => {
    return catalog.skus.filter(s => inputQuantities[s.id] !== undefined && inputQuantities[s.id] !== "").length
  }, [catalog.skus, inputQuantities])

  const progressPct = totalSkus > 0 ? Math.round((countedSkusCount / totalSkus) * 100) : 0

  const filteredSkus = useMemo(() => {
    return catalog.skus.filter(s => {
      const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase())
      if (!matchesSearch) return false

      const isCounted = inputQuantities[s.id] !== undefined && inputQuantities[s.id] !== ""
      if (activeFilter === "counted") return isCounted
      if (activeFilter === "pending") return !isCounted
      return true
    })
  }, [catalog.skus, searchTerm, activeFilter, inputQuantities])

  const handleInputBlur = async (sku_id: string, value: string) => {
    if (session.status === "CLOSED") return
    
    const quantity = parseFloat(value)
    if (isNaN(quantity) || quantity < 0) return

    // Save line to API
    const res = await addCountLine(session.id, { sku_id, counted_quantity: quantity })
    if (res) {
      setSavedStatus(prev => ({ ...prev, [sku_id]: true }))
    }
  }

  const handleCloseSession = async () => {
    setIsSubmitting(true)
    const success = await closeInventorySession(session.id)
    setIsSubmitting(false)

    if (success) {
      setShowConfirmModal(false)
      router.refresh()
    } else {
      alert("Erro ao fechar sessão.")
    }
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  return (
    <div className="space-y-6 pb-24 max-w-7xl mx-auto">
      {/* Confirm Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
          <GlassPanel className="w-full max-w-md p-6 animate-in fade-in zoom-in-95 border-red-500/30">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="h-16 w-16 rounded-full bg-red-500/20 flex items-center justify-center text-red-500">
                <AlertTriangle className="h-8 w-8" />
              </div>
              <h3 className="text-2xl font-bold text-white">Fechar Inventário?</h3>
              <p className="text-zinc-400 text-sm">
                Esta ação é irreversível. Qualquer divergência entre o estoque teórico e a sua contagem física será processada e lançada no Ledger como ajuste de perda ou sobra.
              </p>
              
              <div className="w-full bg-zinc-900/80 rounded-xl p-3 border border-white/10 text-left text-xs space-y-1">
                <div className="flex justify-between text-zinc-300">
                  <span>Itens contados:</span>
                  <strong className="text-emerald-400 font-mono">{countedSkusCount} de {totalSkus}</strong>
                </div>
                <div className="flex justify-between text-zinc-300">
                  <span>Itens não contados (assumidos 0):</span>
                  <strong className="text-amber-400 font-mono">{totalSkus - countedSkusCount}</strong>
                </div>
              </div>

              <div className="flex gap-3 w-full mt-4">
                <button 
                  onClick={() => setShowConfirmModal(false)}
                  className="flex-1 px-4 py-3 rounded-xl bg-zinc-800 text-zinc-300 font-semibold hover:bg-zinc-700 transition-colors"
                >
                  Cancelar
                </button>
                <button 
                  onClick={handleCloseSession}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-3 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold transition-all shadow-lg shadow-red-600/30 disabled:opacity-50"
                >
                  {isSubmitting ? "Fechando..." : "Confirmar e Fechar"}
                </button>
              </div>
            </div>
          </GlassPanel>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col gap-4">
        <button 
          onClick={() => router.push("/inventory-sessions")}
          className="text-sm text-zinc-400 hover:text-white flex items-center gap-1 w-fit transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Voltar para Sessões
        </button>
        
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                <ClipboardList className="h-7 w-7 text-cyan-400" />
                Contagem Física Mobile
              </h1>
              <span className="hidden sm:inline-flex rounded-full bg-cyan-500/10 px-2.5 py-0.5 text-xs font-semibold text-cyan-400 border border-cyan-500/20">
                Chão de Loja
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-xs text-zinc-400">
              <span className="font-mono">Sessão: {session.id.slice(0, 8)}...</span>
              {session.status === "OPEN" ? (
                <span className="inline-flex items-center gap-1 text-cyan-400 font-semibold">
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
                  Contagem em Aberto
                </span>
              ) : (
                <span className="text-purple-400 font-semibold">Sessão Fechada</span>
              )}
            </div>
          </div>

          {session.status === "OPEN" && (
            <button
              onClick={() => setShowConfirmModal(true)}
              className="bg-amber-500 hover:bg-amber-400 text-zinc-950 px-6 py-3 rounded-xl font-bold shadow-lg shadow-amber-500/20 transition-all flex items-center justify-center gap-2 active:scale-95"
            >
              <CheckCircle className="h-5 w-5" />
              Finalizar Contagem
            </button>
          )}
        </div>

        {/* Progress Bar (Mobile and Desktop) */}
        {session.status === "OPEN" && (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-md space-y-2">
            <div className="flex justify-between items-center text-xs font-medium">
              <span className="text-zinc-300 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                Progresso da Contagem
              </span>
              <span className="font-mono text-cyan-400 font-bold">
                {countedSkusCount} de {totalSkus} itens ({progressPct}%)
              </span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-zinc-800 overflow-hidden">
              <div 
                className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Sticky Search & Filter Tabs */}
      <div className="sticky top-0 z-20 py-3 bg-zinc-950/90 backdrop-blur-md space-y-3">
        <div className="relative flex w-full">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-400" />
          <input
            type="text"
            placeholder="Buscar insumo para contar..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-zinc-900 border border-white/10 rounded-2xl pl-11 pr-14 py-3.5 text-white text-base shadow-lg focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all placeholder:text-zinc-500"
          />
          <button className="absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 flex items-center justify-center bg-white/10 text-cyan-400 rounded-xl hover:bg-white/15 transition-colors">
            <ScanLine className="h-5 w-5" />
          </button>
        </div>

        {/* Filter Tabs */}
        {session.status === "OPEN" && (
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            <button
              onClick={() => setActiveFilter("all")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                activeFilter === "all"
                  ? "bg-white/15 text-white border border-white/20 shadow-sm"
                  : "bg-white/5 text-zinc-400 hover:text-zinc-200 border border-transparent"
              }`}
            >
              Todos ({totalSkus})
            </button>
            <button
              onClick={() => setActiveFilter("pending")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                activeFilter === "pending"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow-sm"
                  : "bg-white/5 text-zinc-400 hover:text-zinc-200 border border-transparent"
              }`}
            >
              Pendentes ({totalSkus - countedSkusCount})
            </button>
            <button
              onClick={() => setActiveFilter("counted")}
              className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                activeFilter === "counted"
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow-sm"
                  : "bg-white/5 text-zinc-400 hover:text-zinc-200 border border-transparent"
              }`}
            >
              Contados ({countedSkusCount})
            </button>
          </div>
        )}
      </div>

      {/* Content Area */}
      {session.status === "OPEN" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredSkus.map(sku => {
            const isCounted = inputQuantities[sku.id] !== undefined && inputQuantities[sku.id] !== ""
            const isSaved = savedStatus[sku.id]

            return (
              <div 
                key={sku.id} 
                className={`rounded-2xl border p-4 flex flex-col gap-4 backdrop-blur-md transition-all ${
                  isCounted 
                    ? "bg-emerald-950/10 border-emerald-500/30 shadow-sm shadow-emerald-950/20" 
                    : "bg-white/5 border-white/10 hover:border-white/20"
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-bold text-zinc-100 leading-tight">
                      {sku.name}
                    </h3>
                  </div>

                  {isCounted ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
                      <Check className="w-3 h-3" /> Contado
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-bold text-amber-400 border border-amber-500/20">
                      <Clock className="w-3 h-3" /> Pendente
                    </span>
                  )}
                </div>
                
                <div className="mt-auto pt-1">
                  <div className="flex flex-col gap-2">
                    {/* Primary Number Pad Row */}
                    <div className="flex items-center gap-2 w-full">
                      <button 
                        onClick={() => {
                          const curr = parseFloat(inputQuantities[sku.id] || "0")
                          const next = Math.max(0, curr - 1)
                          setInputQuantities(prev => ({...prev, [sku.id]: next.toString()}))
                          handleInputBlur(sku.id, next.toString())
                        }}
                        className="h-14 w-16 rounded-xl bg-zinc-800/80 text-zinc-300 hover:bg-zinc-700 hover:text-white transition-colors flex items-center justify-center font-bold text-xl active:scale-95"
                      >
                        -1
                      </button>
                      <input
                        type="number"
                        inputMode="decimal"
                        step="0.01"
                        min="0"
                        value={inputQuantities[sku.id] || ""}
                        onChange={(e) => {
                          const val = e.target.value
                          setInputQuantities(prev => ({...prev, [sku.id]: val}))
                          setSavedStatus(prev => ({...prev, [sku.id]: false}))
                        }}
                        onBlur={(e) => handleInputBlur(sku.id, e.target.value)}
                        className="flex-1 min-w-0 bg-zinc-900 border-2 border-zinc-700/80 rounded-xl px-2 py-3 text-white text-center font-mono text-2xl font-bold focus:outline-none focus:border-cyan-400 transition-all placeholder:text-zinc-600"
                        placeholder="0"
                      />
                      <button 
                        onClick={() => {
                          const curr = parseFloat(inputQuantities[sku.id] || "0")
                          const next = curr + 1
                          setInputQuantities(prev => ({...prev, [sku.id]: next.toString()}))
                          handleInputBlur(sku.id, next.toString())
                        }}
                        className="h-14 w-16 rounded-xl bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 transition-colors flex items-center justify-center font-bold text-xl active:scale-95 border border-cyan-500/30"
                      >
                        +1
                      </button>
                    </div>
                    
                    {/* Quick Step Buttons */}
                    <div className="grid grid-cols-3 gap-2">
                      <button 
                        onClick={() => {
                          const curr = parseFloat(inputQuantities[sku.id] || "0")
                          const next = curr + 5
                          setInputQuantities(prev => ({...prev, [sku.id]: next.toString()}))
                          handleInputBlur(sku.id, next.toString())
                        }}
                        className="h-10 rounded-xl bg-zinc-800/50 text-zinc-300 hover:bg-zinc-700/70 transition-colors flex items-center justify-center font-bold text-sm active:scale-95"
                      >
                        +5
                      </button>
                      <button 
                        onClick={() => {
                          const curr = parseFloat(inputQuantities[sku.id] || "0")
                          const next = curr + 10
                          setInputQuantities(prev => ({...prev, [sku.id]: next.toString()}))
                          handleInputBlur(sku.id, next.toString())
                        }}
                        className="h-10 rounded-xl bg-zinc-800/50 text-zinc-300 hover:bg-zinc-700/70 transition-colors flex items-center justify-center font-bold text-sm active:scale-95"
                      >
                        +10
                      </button>
                      <button 
                        onClick={() => {
                          const curr = parseFloat(inputQuantities[sku.id] || "0")
                          const next = curr + 25
                          setInputQuantities(prev => ({...prev, [sku.id]: next.toString()}))
                          handleInputBlur(sku.id, next.toString())
                        }}
                        className="h-10 rounded-xl bg-zinc-800/50 text-zinc-300 hover:bg-zinc-700/70 transition-colors flex items-center justify-center font-bold text-sm active:scale-95"
                      >
                        +25
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
          {filteredSkus.length === 0 && (
            <div className="col-span-full py-12 text-center text-zinc-500 rounded-2xl border border-white/5 bg-white/5">
              Nenhum insumo encontrado no filtro selecionado.
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="bg-zinc-900/80 border border-white/10 rounded-2xl p-6 flex flex-col md:flex-row items-center gap-6">
            <div className="h-14 w-14 bg-purple-500/20 text-purple-400 rounded-2xl flex items-center justify-center flex-shrink-0">
              <Info className="h-7 w-7" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-1">Relatório de Variância (Pós-Fechamento)</h3>
              <p className="text-zinc-400 text-sm">
                O inventário foi processado comparando a contagem física com o saldo teórico esperado. As divergências foram lançadas e estão detalhadas abaixo.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {closeResults.length === 0 && <p className="text-zinc-500 italic p-4">Nenhum resultado processado.</p>}
            
            {closeResults.sort((a,b) => a.variance_value - b.variance_value).map((result) => {
              const sku = catalog.skus.find(s => s.id === result.sku_id)
              const isLoss = result.variance_quantity < 0
              const isSurplus = result.variance_quantity > 0
              
              return (
                <div 
                  key={result.sku_id} 
                  className={`rounded-2xl border p-5 flex flex-col gap-3 bg-white/5 backdrop-blur-md border-l-4 ${
                    isLoss ? 'border-l-red-500 border-white/10' : isSurplus ? 'border-l-cyan-400 border-white/10' : 'border-l-zinc-600 border-white/10'
                  }`}
                >
                  <h4 className="text-lg font-bold text-zinc-100">{sku?.name || "SKU Desconhecido"}</h4>
                  
                  <div className="grid grid-cols-2 gap-3 mt-1">
                    <div className="bg-zinc-900/90 p-3 rounded-xl border border-white/5">
                      <span className="text-[10px] text-zinc-500 uppercase tracking-wider block mb-1">Esperado Teórico</span>
                      <span className="font-mono text-lg text-zinc-300 font-bold">{result.expected_quantity}</span>
                    </div>
                    <div className="bg-zinc-900/90 p-3 rounded-xl border border-white/5">
                      <span className="text-[10px] text-zinc-500 uppercase tracking-wider block mb-1">Contagem Física</span>
                      <span className="font-mono text-lg text-white font-bold">{result.counted_quantity}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-1 pt-3 border-t border-white/10">
                    <div>
                      <span className="text-[10px] text-zinc-500 block uppercase">Divergência</span>
                      <span className={`font-mono text-base font-bold flex items-center gap-1 ${
                        isLoss ? 'text-red-400' : isSurplus ? 'text-cyan-400' : 'text-zinc-400'
                      }`}>
                        {isLoss && <TrendingDown className="h-4 w-4" />}
                        {isSurplus && <TrendingUp className="h-4 w-4" />}
                        {isSurplus ? "+" : ""}{result.variance_quantity}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-zinc-500 block uppercase">Impacto Financeiro</span>
                      <span className={`font-mono text-base font-bold ${
                        isLoss ? 'text-red-400' : isSurplus ? 'text-cyan-400' : 'text-zinc-400'
                      }`}>
                        {formatCurrency(result.variance_value)}
                      </span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
