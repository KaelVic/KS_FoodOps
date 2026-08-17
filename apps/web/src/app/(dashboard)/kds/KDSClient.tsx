"use client"

import React, { useState, useEffect } from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { KDSItem, ProductionStation, KDSItemStatus } from "@/types/orders"
import { fetchKDSQueueClient, updateKDSItemStatusClient } from "@/lib/api-client"
import {
  ChefHat,
  Flame,
  CheckCircle2,
  Clock,
  Wine,
  Pizza,
  IceCream,
  RefreshCw,
  Play,
  Check,
  AlertTriangle,
  Layers,
  Sparkles,
} from "lucide-react"

interface KDSClientProps {
  initialItems: KDSItem[]
}

export function KDSClient({ initialItems }: KDSClientProps) {
  const [items, setItems] = useState<KDSItem[]>(initialItems)
  const [loading, setLoading] = useState(false)
  const [selectedStation, setSelectedStation] = useState<string>("ALL")
  const [autoRefresh, setAutoRefresh] = useState(true)

  const reloadKDS = async () => {
    setLoading(true)
    try {
      const data = await fetchKDSQueueClient(
        selectedStation === "ALL" ? undefined : selectedStation
      )
      setItems(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Auto-refresh interval every 8 seconds
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => {
      reloadKDS()
    }, 8000)
    return () => clearInterval(interval)
  }, [autoRefresh, selectedStation])

  const handleStatusChange = async (itemId: string, newStatus: string) => {
    try {
      await updateKDSItemStatusClient(itemId, newStatus)
      await reloadKDS()
    } catch (err) {
      console.error(err)
    }
  }

  // Filter items by station
  const filteredItems = items.filter(
    (item) => selectedStation === "ALL" || item.production_station === selectedStation
  )

  const queuedItems = filteredItems.filter((i) => i.status === "QUEUED")
  const preparingItems = filteredItems.filter((i) => i.status === "PREPARING")
  const readyItems = filteredItems.filter((i) => i.status === "READY")

  const avgWait =
    filteredItems.length > 0
      ? (
          filteredItems.reduce((acc, i) => acc + i.wait_minutes, 0) /
          filteredItems.length
        ).toFixed(0)
      : "0"

  const stationIcons: Record<string, React.ReactNode> = {
    KITCHEN: <ChefHat className="h-4 w-4 text-orange-400" />,
    BAR: <Wine className="h-4 w-4 text-purple-400" />,
    PIZZERIA: <Pizza className="h-4 w-4 text-amber-400" />,
    DESSERT: <IceCream className="h-4 w-4 text-pink-400" />,
  }

  return (
    <div className="space-y-6">
      {/* Top Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassPanel className="p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase">
            <span>Fila de Espera</span>
            <Clock className="h-4 w-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-1">{queuedItems.length} pratos</div>
          <p className="text-2xs text-slate-500 mt-1">Aguardando início do preparo</p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="flex items-center justify-between text-xs text-amber-400 font-semibold uppercase">
            <span>No Fogo / Preparando</span>
            <Flame className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {preparingItems.length} pratos
          </div>
          <p className="text-2xs text-slate-500 mt-1">Em confecção na praça de produção</p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="flex items-center justify-between text-xs text-emerald-400 font-semibold uppercase">
            <span>Prontos para Saída</span>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{readyItems.length} pratos</div>
          <p className="text-2xs text-slate-500 mt-1">Aguardando garçom ou embalagem</p>
        </GlassPanel>

        <GlassPanel className="p-4">
          <div className="flex items-center justify-between text-xs text-blue-400 font-semibold uppercase">
            <span>Tempo Médio em Espera</span>
            <Clock className="h-4 w-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-blue-400 mt-1">{avgWait} min</div>
          <p className="text-2xs text-slate-500 mt-1">Tempo acumulado desde a comanda</p>
        </GlassPanel>
      </div>

      {/* Station Selector Bar */}
      <GlassPanel className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setSelectedStation("ALL")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              selectedStation === "ALL"
                ? "bg-amber-500 text-slate-950 font-bold"
                : "bg-slate-900/80 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            Todas as Praças ({items.length})
          </button>

          <button
            onClick={() => setSelectedStation("KITCHEN")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              selectedStation === "KITCHEN"
                ? "bg-orange-500 text-slate-950 font-bold"
                : "bg-slate-900/80 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <ChefHat className="h-3.5 w-3.5 text-orange-400" />
            Cozinha Quente ({items.filter((i) => i.production_station === "KITCHEN").length})
          </button>

          <button
            onClick={() => setSelectedStation("BAR")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              selectedStation === "BAR"
                ? "bg-purple-500 text-slate-950 font-bold"
                : "bg-slate-900/80 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <Wine className="h-3.5 w-3.5 text-purple-400" />
            Bar & Bebidas ({items.filter((i) => i.production_station === "BAR").length})
          </button>

          <button
            onClick={() => setSelectedStation("PIZZERIA")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              selectedStation === "PIZZERIA"
                ? "bg-amber-500 text-slate-950 font-bold"
                : "bg-slate-900/80 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <Pizza className="h-3.5 w-3.5 text-amber-400" />
            Pizzaria / Forno ({items.filter((i) => i.production_station === "PIZZERIA").length})
          </button>

          <button
            onClick={() => setSelectedStation("DESSERT")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              selectedStation === "DESSERT"
                ? "bg-pink-500 text-slate-950 font-bold"
                : "bg-slate-900/80 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <IceCream className="h-3.5 w-3.5 text-pink-400" />
            Sobremesas ({items.filter((i) => i.production_station === "DESSERT").length})
          </button>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-slate-700 bg-slate-900 text-amber-500 focus:ring-amber-400"
            />
            <span>Auto-refresh (8s)</span>
          </label>

          <button
            onClick={reloadKDS}
            disabled={loading}
            className="h-9 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 flex items-center transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </button>
        </div>
      </GlassPanel>

      {/* KDS 3 Columns Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Column 1: QUEUED (Na Fila) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-slate-800 text-slate-300 rounded-lg">
                <Clock className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-200">
                1. Na Fila de Espera ({queuedItems.length})
              </h3>
            </div>
            <Badge variant="default" className="text-2xs">
              Aguardando
            </Badge>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {queuedItems.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-10 text-center">
                Nenhum prato na fila
              </p>
            ) : (
              queuedItems.map((item) => {
                const isRed = item.sla_status === "RED"
                const isYellow = item.sla_status === "YELLOW"

                return (
                  <div
                    key={item.item_id}
                    className={`p-4 rounded-xl border transition-all bg-slate-900/90 ${
                      isRed
                        ? "border-rose-500/60 shadow-lg shadow-rose-500/10 animate-pulse"
                        : isYellow
                        ? "border-amber-500/40"
                        : "border-slate-800"
                    }`}
                  >
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                      <div className="flex items-center gap-1.5">
                        {stationIcons[item.production_station]}
                        <span className="font-bold text-sm text-slate-100">
                          {item.table_number || item.customer_name}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-2xs text-slate-400">
                          {item.order_number}
                        </span>
                        <Badge
                          variant={isRed ? "crimson" : isYellow ? "amber" : "emerald"}
                          className="text-2xs font-mono font-bold"
                        >
                          {item.wait_minutes} min
                        </Badge>
                      </div>
                    </div>

                    <div className="py-3">
                      <div className="text-base font-bold text-slate-100 flex items-baseline gap-2">
                        <span className="text-amber-400 font-mono">{item.quantity}x</span>
                        <span>{item.item_name}</span>
                      </div>

                      {item.preparation_notes && (
                        <div className="mt-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs font-semibold text-amber-300">
                          ⚠️ {item.preparation_notes}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => handleStatusChange(item.item_id, "PREPARING")}
                      className="w-full py-2.5 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 font-bold hover:from-amber-600 hover:to-orange-600 text-xs flex items-center justify-center transition-colors shadow-lg shadow-amber-500/20"
                    >
                      <Play className="h-3.5 w-3.5 mr-1.5 fill-slate-950" />
                      Iniciar Preparo
                    </button>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Column 2: PREPARING (No Fogo) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-amber-500/30">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-amber-500/20 text-amber-400 rounded-lg">
                <Flame className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-amber-400">
                2. Em Preparo ({preparingItems.length})
              </h3>
            </div>
            <Badge variant="amber" className="text-2xs">
              Cozinhando
            </Badge>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {preparingItems.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-10 text-center">
                Nenhum prato em confecção
              </p>
            ) : (
              preparingItems.map((item) => {
                const isRed = item.sla_status === "RED"
                const isYellow = item.sla_status === "YELLOW"

                return (
                  <div
                    key={item.item_id}
                    className={`p-4 rounded-xl border transition-all bg-gradient-to-br from-amber-950/20 via-slate-900 to-slate-950 ${
                      isRed
                        ? "border-rose-500/80 shadow-lg shadow-rose-500/20 animate-pulse"
                        : isYellow
                        ? "border-amber-500/60"
                        : "border-amber-500/30"
                    }`}
                  >
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                      <div className="flex items-center gap-1.5">
                        {stationIcons[item.production_station]}
                        <span className="font-bold text-sm text-slate-100">
                          {item.table_number || item.customer_name}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-2xs text-slate-400">
                          {item.order_number}
                        </span>
                        <Badge
                          variant={isRed ? "crimson" : isYellow ? "amber" : "emerald"}
                          className="text-2xs font-mono font-bold"
                        >
                          {item.wait_minutes} min
                        </Badge>
                      </div>
                    </div>

                    <div className="py-3">
                      <div className="text-base font-bold text-slate-100 flex items-baseline gap-2">
                        <span className="text-amber-400 font-mono">{item.quantity}x</span>
                        <span>{item.item_name}</span>
                      </div>

                      {item.preparation_notes && (
                        <div className="mt-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs font-semibold text-amber-300">
                          ⚠️ {item.preparation_notes}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => handleStatusChange(item.item_id, "READY")}
                      className="w-full py-2.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold hover:from-emerald-600 hover:to-teal-600 text-xs flex items-center justify-center transition-colors shadow-lg shadow-emerald-500/20"
                    >
                      <Check className="h-4 w-4 mr-1.5 font-bold" />
                      Pronto para Servir!
                    </button>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Column 3: READY (Prontos) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-emerald-500/30">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-emerald-500/20 text-emerald-400 rounded-lg">
                <CheckCircle2 className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold text-emerald-400">
                3. Prontos para Retirada ({readyItems.length})
              </h3>
            </div>
            <Badge variant="emerald" className="text-2xs">
              Pronto
            </Badge>
          </div>

          <div className="space-y-3 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            {readyItems.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-10 text-center">
                Nenhum prato aguardando saída
              </p>
            ) : (
              readyItems.map((item) => (
                <div
                  key={item.item_id}
                  className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/10 shadow-lg shadow-emerald-500/5 transition-all space-y-3"
                >
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                    <div className="flex items-center gap-1.5">
                      {stationIcons[item.production_station]}
                      <span className="font-bold text-sm text-emerald-400">
                        {item.table_number || item.customer_name}
                      </span>
                    </div>
                    <span className="font-mono text-2xs text-slate-400">
                      {item.order_number}
                    </span>
                  </div>

                  <div className="text-sm font-bold text-slate-100 flex items-baseline gap-2">
                    <span className="text-emerald-400 font-mono">{item.quantity}x</span>
                    <span>{item.item_name}</span>
                  </div>

                  <button
                    onClick={() => handleStatusChange(item.item_id, "SERVED")}
                    className="w-full py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center transition-colors"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 mr-1.5 text-emerald-400" />
                    Marcar como Servido / Despachado
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
