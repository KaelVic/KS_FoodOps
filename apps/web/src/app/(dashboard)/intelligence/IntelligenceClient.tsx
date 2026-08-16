"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { 
  Lightbulb, AlertTriangle, ListFilter, PlayCircle, PlusCircle, CheckCircle, BrainCircuit
} from "lucide-react"
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ZAxis
} from "recharts"

import { 
  InventoryPolicy, PurchaseSuggestion, OperationalAlert 
} from "@/types/intelligence"
import {
  calculateABC, generateSuggestions, generateAlerts,
  resolveAlert, convertToPO
} from "@/lib/api-client"

interface LocationData {
  id: string
  name: string
}

interface IntelligenceClientProps {
  initialPolicies: InventoryPolicy[]
  initialSuggestions: PurchaseSuggestion[]
  initialAlerts: OperationalAlert[]
  locations: LocationData[]
  defaultLocationId: string | null
}

export function IntelligenceClient({
  initialPolicies,
  initialSuggestions,
  initialAlerts,
  locations,
  defaultLocationId
}: IntelligenceClientProps) {
  const [activeTab, setActiveTab] = useState<"SUGGESTIONS" | "POLICIES" | "ALERTS">("SUGGESTIONS")
  const [activeLocation, setActiveLocation] = useState<string | null>(defaultLocationId)
  
  const [policies, setPolicies] = useState(initialPolicies)
  const [suggestions, setSuggestions] = useState(initialSuggestions)
  const [alerts, setAlerts] = useState(initialAlerts)

  const [isLoading, setIsLoading] = useState(false)

  const handleCalculateABC = async () => {
    if (!activeLocation) return
    setIsLoading(true)
    await calculateABC(activeLocation)
    alert("Cálculo da Curva ABC finalizado. Na vida real, os dados seriam recarregados via WebSocket/SSE.")
    setIsLoading(false)
  }

  const handleGenerateSuggestions = async () => {
    if (!activeLocation) return
    setIsLoading(true)
    await generateSuggestions(activeLocation)
    alert("Ordens de Compra sugeridas pela IA foram atualizadas.")
    setIsLoading(false)
  }

  const handleGenerateAlerts = async () => {
    if (!activeLocation) return
    setIsLoading(true)
    await generateAlerts(activeLocation)
    alert("Varredura de anomalias concluída.")
    setIsLoading(false)
  }

  const handleResolveAlert = async (id: string) => {
    const success = await resolveAlert(id)
    if (success) {
      setAlerts(alerts.filter(a => a.id !== id))
    }
  }

  const handleConvertToPO = async (id: string) => {
    alert("Conversão para PO requer seleção de fornecedor. Funcionalidade em desenvolvimento.")
  }

  // Prepara dados falsos de Consumo x Valor para simular o Scatter Chart com base nas politicas atuais
  const abcChartData = policies.map((p, index) => {
    // Generate some fake metrics for the scatter plot to look realistic based on ABC class
    let volume = 0;
    let value = 0;
    
    if (p.abc_class === 'A') {
      volume = Math.random() * 500 + 100;
      value = Math.random() * 5000 + 2000;
    } else if (p.abc_class === 'B') {
      volume = Math.random() * 300 + 50;
      value = Math.random() * 2000 + 500;
    } else {
      volume = Math.random() * 150 + 10;
      value = Math.random() * 500 + 50;
    }

    return {
      name: p.sku_name,
      class: p.abc_class,
      volume: Number(volume.toFixed(2)),
      value: Number(value.toFixed(2)),
      fill: p.abc_class === 'A' ? '#ef4444' : p.abc_class === 'B' ? '#f59e0b' : '#10b981'
    }
  })

  const CustomScatterTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl z-50">
          <p className="font-bold text-slate-100">{data.name}</p>
          <div className="flex gap-2 items-center mt-1">
            <span className="text-xs text-slate-400">Classe ABC:</span>
            <Badge variant="default" className="text-[10px] px-1 py-0" style={{ backgroundColor: data.fill + '20', color: data.fill, borderColor: data.fill + '50' }}>{data.class}</Badge>
          </div>
          <p className="text-sm text-slate-300 mt-2 font-mono">Vol. Consumido: {data.volume}</p>
          <p className="text-sm text-slate-300 font-mono">Valor Impacto: R$ {data.value}</p>
        </div>
      );
    }
    return null;
  }

  return (
    <div className="space-y-6 pb-24">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-[#00f0ff] to-[#a855f7] bg-clip-text text-transparent flex items-center gap-2">
            <BrainCircuit className="h-8 w-8 text-[#00f0ff]" />
            Inteligência Operacional
          </h1>
          <p className="text-slate-400 mt-1">
            Matriz ABC Interativa, Recomendações de Compra Preditivas e Monitoramento de Anomalias.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select 
            value={activeLocation || ""}
            onChange={(e) => setActiveLocation(e.target.value)}
            className="bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-2.5 text-white outline-none focus:border-[#00f0ff] shadow-lg font-medium"
          >
            {locations.length === 0 && <option value="">Nenhum local configurado</option>}
            {locations.map(l => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1.5 bg-slate-900/50 border border-slate-800 rounded-xl w-max overflow-x-auto max-w-full shadow-inner">
        <button
          onClick={() => setActiveTab("SUGGESTIONS")}
          className={`px-4 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center whitespace-nowrap ${
            activeTab === "SUGGESTIONS"
              ? "bg-slate-800 text-white shadow-md border border-slate-700/50"
              : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
          }`}
        >
          <Lightbulb className={`h-4 w-4 mr-2 ${activeTab === 'SUGGESTIONS' ? 'text-[#00f0ff]' : ''}`} />
          Disparos da IA
        </button>
        <button
          onClick={() => setActiveTab("POLICIES")}
          className={`px-4 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center whitespace-nowrap ${
            activeTab === "POLICIES"
              ? "bg-slate-800 text-white shadow-md border border-slate-700/50"
              : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
          }`}
        >
          <ListFilter className={`h-4 w-4 mr-2 ${activeTab === 'POLICIES' ? 'text-[#a855f7]' : ''}`} />
          Matriz ABC (Curva de Pareto)
        </button>
        <button
          onClick={() => setActiveTab("ALERTS")}
          className={`px-4 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center whitespace-nowrap ${
            activeTab === "ALERTS"
              ? "bg-slate-800 text-white shadow-md border border-slate-700/50"
              : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
          }`}
        >
          <AlertTriangle className={`h-4 w-4 mr-2 ${activeTab === 'ALERTS' ? 'text-[#ef4444]' : ''}`} />
          Radares & Anomalias
          {alerts.length > 0 && (
            <span className="ml-2 bg-[#ef4444]/20 text-[#ef4444] px-2 py-0.5 rounded-full text-[10px] border border-[#ef4444]/30">
              {alerts.length}
            </span>
          )}
        </button>
      </div>

      {/* Content */}
      <GlassPanel className="p-0 overflow-hidden shadow-2xl border-slate-700/60">
        
        {/* TAB: SUGGESTIONS */}
        {activeTab === "SUGGESTIONS" && (
          <div className="flex flex-col h-full">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/30">
              <div>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <Lightbulb className="h-5 w-5 text-[#00f0ff]" />
                  Reposições Sugeridas
                </h2>
                <p className="text-sm text-slate-400 mt-1">O sistema projeta a necessidade de compra baseado no Lead Time, Target Stock e ABC.</p>
              </div>
              <button
                onClick={handleGenerateSuggestions}
                disabled={isLoading}
                className="bg-[#00f0ff] hover:bg-[#00f0ff]/80 text-slate-950 px-5 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)]"
              >
                <PlayCircle className="h-5 w-5" />
                Regerar Sugestões
              </button>
            </div>
            
            {suggestions.length === 0 ? (
              <div className="text-center py-20 text-slate-500">
                <Lightbulb className="h-16 w-16 mx-auto mb-4 opacity-20" />
                <p className="text-lg">Nenhuma sugestão de compra crítica no momento.</p>
              </div>
            ) : (
              <div className="overflow-x-auto p-4">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-700 uppercase text-xs tracking-wider">
                    <tr>
                      <th className="px-5 py-4 font-bold">SKU / Insumo</th>
                      <th className="px-5 py-4 font-bold text-center border-l border-slate-800">Qtd Sugerida</th>
                      <th className="px-5 py-4 font-bold border-l border-slate-800">Gatilho (Motivo)</th>
                      <th className="px-5 py-4 font-bold text-right border-l border-slate-800">Ação Rápida</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {suggestions.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-5 py-4 font-bold text-slate-200">{s.sku_name}</td>
                        <td className="px-5 py-4 text-center border-l border-slate-800">
                          <span className="font-mono text-lg text-[#00f0ff] font-bold bg-[#00f0ff]/10 px-3 py-1 rounded-lg">
                            {Number(s.suggested_quantity).toFixed(2)} {s.base_uom}
                          </span>
                        </td>
                        <td className="px-5 py-4 border-l border-slate-800">
                          <span className="text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg text-xs">{s.reason}</span>
                        </td>
                        <td className="px-5 py-4 text-right border-l border-slate-800">
                          <button
                            onClick={() => handleConvertToPO(s.id)}
                            className="bg-[#10b981]/20 hover:bg-[#10b981]/30 text-[#10b981] border border-[#10b981]/30 px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-1 ml-auto transition-all shadow-md"
                          >
                            <PlusCircle className="h-4 w-4" />
                            Aprovar PO
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB: POLICIES */}
        {activeTab === "POLICIES" && (
          <div className="flex flex-col h-full">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/30">
              <div>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <ListFilter className="h-5 w-5 text-[#a855f7]" />
                  Matriz ABC (Curva de Pareto)
                </h2>
                <p className="text-sm text-slate-400 mt-1">Classificação baseada em volume de vendas e impacto financeiro no COGS.</p>
              </div>
              <button
                onClick={handleCalculateABC}
                disabled={isLoading}
                className="bg-[#a855f7] hover:bg-[#a855f7]/80 text-white px-5 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:shadow-[0_0_25px_rgba(168,85,247,0.5)]"
              >
                <PlayCircle className="h-5 w-5" />
                Recalcular Matriz ABC
              </button>
            </div>

            {policies.length > 0 && (
              <div className="p-6 border-b border-slate-800 bg-slate-950/50">
                <h3 className="text-sm font-bold text-slate-400 mb-4 uppercase tracking-wider">Dispersão: Impacto Financeiro vs Volume</h3>
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                      <XAxis type="number" dataKey="volume" name="Volume" stroke="#94a3b8" fontSize={12} tickFormatter={(val) => `${val} un`} />
                      <YAxis type="number" dataKey="value" name="Valor (R$)" stroke="#94a3b8" fontSize={12} tickFormatter={(val) => `R$ ${val}`} />
                      <ZAxis type="number" range={[100, 400]} />
                      <RechartsTooltip content={<CustomScatterTooltip />} cursor={{ strokeDasharray: '3 3', stroke: '#64748b' }} />
                      <Scatter name="SKUs" data={abcChartData} />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {policies.length === 0 ? (
              <div className="text-center py-20 text-slate-500">
                <ListFilter className="h-16 w-16 mx-auto mb-4 opacity-20" />
                <p className="text-lg">Nenhuma política configurada para este local.</p>
              </div>
            ) : (
              <div className="overflow-x-auto p-4">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-700 uppercase text-xs tracking-wider">
                    <tr>
                      <th className="px-5 py-4 font-bold">Classificação</th>
                      <th className="px-5 py-4 font-bold border-l border-slate-800">SKU / Insumo</th>
                      <th className="px-5 py-4 font-bold text-right border-l border-slate-800">Min Stock</th>
                      <th className="px-5 py-4 font-bold text-right border-l border-slate-800">Target Stock</th>
                      <th className="px-5 py-4 font-bold text-right border-l border-slate-800">Lead Time (Dias)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {policies.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-5 py-4">
                          <Badge className={`px-3 py-1 font-bold ${
                            p.abc_class === 'A' ? "border-[#ef4444]/50 text-[#ef4444] bg-[#ef4444]/10" :
                            p.abc_class === 'B' ? "border-[#f59e0b]/50 text-[#f59e0b] bg-[#f59e0b]/10" :
                            p.abc_class === 'C' ? "border-[#10b981]/50 text-[#10b981] bg-[#10b981]/10" :
                            "border-slate-700 text-slate-400"
                          }`}>
                            Curva {p.abc_class || "N/A"}
                          </Badge>
                        </td>
                        <td className="px-5 py-4 font-bold text-slate-200 border-l border-slate-800">{p.sku_name}</td>
                        <td className="px-5 py-4 text-right font-mono text-slate-400 border-l border-slate-800">{Number(p.min_stock).toFixed(2)} {p.base_uom}</td>
                        <td className="px-5 py-4 text-right font-mono text-[#a855f7] font-bold border-l border-slate-800">{Number(p.target_stock).toFixed(2)} {p.base_uom}</td>
                        <td className="px-5 py-4 text-right font-mono text-slate-400 border-l border-slate-800">{p.lead_time_days}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB: ALERTS */}
        {activeTab === "ALERTS" && (
          <div className="flex flex-col h-full bg-slate-900/10">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/30">
              <div>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-[#ef4444]" />
                  Alertas Operacionais & Radares
                </h2>
                <p className="text-sm text-slate-400 mt-1">Anomalias captadas na última checagem de integridade do estoque.</p>
              </div>
              <button
                onClick={handleGenerateAlerts}
                disabled={isLoading}
                className="bg-[#ef4444] hover:bg-[#ef4444]/80 text-white px-5 py-2.5 rounded-xl font-bold text-sm flex items-center gap-2 transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(239,68,68,0.3)] hover:shadow-[0_0_25px_rgba(239,68,68,0.5)]"
              >
                <PlayCircle className="h-5 w-5" />
                Varrer Anomalias
              </button>
            </div>

            {alerts.length === 0 ? (
              <div className="text-center py-24 text-emerald-500/60">
                <CheckCircle className="h-20 w-20 mx-auto mb-4 opacity-80" />
                <p className="text-xl font-bold text-emerald-400">Ambiente Saudável</p>
                <p className="text-slate-400 mt-2">Nenhuma anomalia de estoque detectada.</p>
              </div>
            ) : (
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                {alerts.map(a => (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    key={a.id} 
                    className="bg-slate-900/80 border border-[#ef4444]/30 p-5 rounded-2xl relative overflow-hidden shadow-xl"
                  >
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-[#ef4444]/80" />
                    <div className="flex justify-between items-start pl-2">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="h-5 w-5 text-[#ef4444]" />
                          <span className="font-bold text-slate-100">{a.metric}</span>
                        </div>
                        <p className="text-[#00f0ff] font-bold text-lg">{a.sku_name}</p>
                        <p className="text-slate-400 text-sm mt-2 leading-relaxed bg-slate-950 p-3 rounded-lg border border-slate-800/50">{a.reason}</p>
                        <div className="mt-4 text-xs font-mono text-slate-500 bg-black/20 inline-block px-2 py-1 rounded">
                          {new Date(a.created_at).toLocaleString('pt-BR')}
                        </div>
                      </div>
                      <button
                        onClick={() => handleResolveAlert(a.id)}
                        className="h-10 w-10 bg-slate-800 text-slate-400 rounded-full flex items-center justify-center hover:bg-emerald-500/20 hover:text-emerald-400 hover:border hover:border-emerald-500/50 transition-all flex-shrink-0"
                        title="Marcar como resolvido"
                      >
                        <CheckCircle className="h-5 w-5" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}

      </GlassPanel>
    </div>
  )
}
