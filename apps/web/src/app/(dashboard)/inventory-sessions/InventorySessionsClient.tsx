"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Plus, X, ArrowRight, ClipboardList, AlertCircle, CheckCircle2, Warehouse } from "lucide-react"

import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { InventorySessionItem } from "@/types/inventory-sessions"
import { createInventorySession, fetchLocations, createLocation } from "@/lib/api-client"
import { Location } from "@/types/master-data"

interface Toast {
  message: string
  type: "success" | "error" | "info"
}

export default function InventorySessionsClient({ initialSessions }: { initialSessions: InventorySessionItem[] }) {
  const router = useRouter()
  const [sessions, setSessions] = useState(initialSessions)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isCreatingLocation, setIsCreatingLocation] = useState(false)
  
  const [locations, setLocations] = useState<Location[]>([])
  const [selectedLocationId, setSelectedLocationId] = useState<string>("")
  const [toast, setToast] = useState<Toast | null>(null)

  const showToast = (message: string, type: Toast["type"] = "info") => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  useEffect(() => {
    if (isCreateOpen) {
      fetchLocations().then((locs) => {
        setLocations(locs)
        if (locs.length > 0) {
          setSelectedLocationId(locs[0].id)
        }
      })
    }
  }, [isCreateOpen])

  const handleAutoProvisionLocation = async () => {
    setIsCreatingLocation(true)
    const location = await createLocation({ name: "Estoque Principal" })
    setIsCreatingLocation(false)
    
    if (location) {
      setLocations(prev => [location, ...prev])
      setSelectedLocationId(location.id)
      showToast("Local 'Estoque Principal' criado automaticamente", "success")
    } else {
      showToast("Erro ao criar local padrão. Verifique permissões.", "error")
    }
  }

  const handleCreateSession = async () => {
    if (!selectedLocationId) {
      showToast("Selecione um local de estoque.", "error")
      return
    }

    setIsSubmitting(true)
    const session = await createInventorySession({ location_id: selectedLocationId })
    setIsSubmitting(false)
    
    if (session) {
      setIsCreateOpen(false)
      showToast("Sessão de inventário iniciada!", "success")
      router.push(`/inventory-sessions/${session.id}`)
      router.refresh()
    } else {
      showToast("Erro ao criar sessão de inventário.", "error")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          onClick={() => setIsCreateOpen(true)}
          className="bg-[#00f0ff] text-slate-950 px-4 py-2 rounded-xl font-semibold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all flex items-center justify-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Nova Sessão de Contagem
        </button>
      </div>

      <GlassPanel className="p-0 overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-800/50 text-slate-400 border-b border-slate-700">
            <tr>
              <th className="px-6 py-4 font-semibold">ID da Sessão</th>
              <th className="px-6 py-4 font-semibold">Status</th>
              <th className="px-6 py-4 font-semibold">Criado em</th>
              <th className="px-6 py-4 font-semibold">Fechado em</th>
              <th className="px-6 py-4 font-semibold text-right">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 text-slate-300">
            {sessions.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                  Nenhuma sessão de inventário encontrada.
                </td>
              </tr>
            ) : (
              sessions.map((s) => (
                <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-mono text-slate-400">
                    {s.id.split("-")[0]}...
                  </td>
                  <td className="px-6 py-4">
                    {s.status === "OPEN" ? (
                      <Badge variant="cyan">Em Andamento</Badge>
                    ) : (
                      <Badge variant="violet">Fechado</Badge>
                    )}
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {new Date(s.created_at).toLocaleString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {s.closed_at ? new Date(s.closed_at).toLocaleString('pt-BR') : "-"}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => router.push(`/inventory-sessions/${s.id}`)}
                      className="text-[#00f0ff] hover:text-cyan-300 transition-colors flex items-center justify-end gap-1 w-full"
                    >
                      {s.status === "OPEN" ? "Continuar" : "Visualizar"}
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </GlassPanel>

      {/* Toast */}
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl backdrop-blur-md transition-all"
          style={{
            backgroundColor: toast.type === "success" ? "rgba(16, 185, 129, 0.2)" : toast.type === "error" ? "rgba(239, 68, 68, 0.2)" : "rgba(6, 182, 212, 0.2)",
            borderColor: toast.type === "success" ? "#10b981" : toast.type === "error" ? "#ef4444" : "#06b6d4",
            color: toast.type === "success" ? "#10b981" : toast.type === "error" ? "#ef4444" : "#06b6d4"
          }}
        >
          {toast.type === "success" && <CheckCircle2 className="h-5 w-5" />}
          {toast.type === "error" && <AlertCircle className="h-5 w-5" />}
          {toast.type === "info" && <Warehouse className="h-5 w-5" />}
          <span className="font-medium text-sm">{toast.message}</span>
        </motion.div>
      )}

      {/* Modal Nova Sessão */}
      <AnimatePresence>
        {isCreateOpen && (
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
              className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md overflow-hidden flex flex-col shadow-2xl"
            >
              <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-800/30">
                <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <ClipboardList className="h-5 w-5 text-[#00f0ff]" />
                  Iniciar Nova Contagem
                </h3>
                <button
                  onClick={() => setIsCreateOpen(false)}
                  disabled={isSubmitting || isCreatingLocation}
                  className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 disabled:opacity-50"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <p className="text-sm text-slate-400">
                  Uma sessão de inventário registrará a posição de estoque exata neste momento ("Snapshot"). Todas as discrepâncias contarão contra o estoque esperado gerado até este exato segundo.
                </p>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-300">Local de Estoque</label>
                  <div className="flex gap-2">
                    <select 
                      value={selectedLocationId}
                      onChange={(e) => setSelectedLocationId(e.target.value)}
                      disabled={locations.length === 0 || isCreatingLocation}
                      className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 outline-none focus:border-[#00f0ff] transition-colors disabled:opacity-50"
                    >
                      {locations.length === 0 ? (
                        <option value="">Nenhum local cadastrado</option>
                      ) : (
                        locations.map(loc => (
                          <option key={loc.id} value={loc.id}>{loc.name}</option>
                        ))
                      )}
                    </select>
                    {locations.length === 0 && (
                      <button
                        onClick={handleAutoProvisionLocation}
                        disabled={isCreatingLocation}
                        className="px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                        title="Criar local 'Estoque Principal' automaticamente"
                      >
                        <Warehouse className="h-4 w-4" />
                        {isCreatingLocation ? "Criando..." : "Criar Estoque Principal"}
                      </button>
                    )}
                  </div>
                  {locations.length === 0 && (
                    <p className="text-xs text-slate-500">
                      Nenhum local de estoque encontrado. Clique em "Criar Estoque Principal" para provisionar automaticamente.
                    </p>
                  )}
                </div>
                <div className="bg-amber-500/10 border border-amber-500/30 text-amber-500 p-4 rounded-xl text-sm">
                  <strong>Atenção:</strong> Certifique-se de que não haja recebimentos em andamento durante a contagem deste local.
                </div>
              </div>

              <div className="p-6 border-t border-slate-800 bg-slate-900 flex items-center justify-end gap-3">
                <button
                  onClick={() => setIsCreateOpen(false)}
                  disabled={isSubmitting || isCreatingLocation}
                  className="px-4 py-2 rounded-xl text-slate-300 font-medium hover:bg-slate-800 transition-colors disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreateSession}
                  disabled={isSubmitting || !selectedLocationId || isCreatingLocation}
                  className="bg-[#00f0ff] text-slate-950 px-6 py-2 rounded-xl font-bold shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.5)] transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {isSubmitting ? "Iniciando..." : "Iniciar Sessão"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}