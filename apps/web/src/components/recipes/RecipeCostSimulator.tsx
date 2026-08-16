"use client"

import { useState, useEffect } from "react"
import { DollarSign, Calculator, TrendingUp, TrendingDown, Target, Percent } from "lucide-react"

interface RecipeCostSimulatorProps {
  totalBatchCost: number
  yieldQuantity: number
  portionSize: number
  recipeType: "MENU_ITEM" | "PREPARED_ITEM"
}

export function RecipeCostSimulator({
  totalBatchCost,
  yieldQuantity,
  portionSize,
  recipeType,
}: RecipeCostSimulatorProps) {
  // If it's a prepared item, we don't strictly "sell" it, but we can show cost metrics
  const isMenuItem = recipeType === "MENU_ITEM"

  const [sellPrice, setSellPrice] = useState<number>(0)
  const [targetCmv, setTargetCmv] = useState<number>(30) // Default 30%

  const costPerPortion = yieldQuantity > 0 ? totalBatchCost / (yieldQuantity / portionSize) : 0
  const currentCmv = sellPrice > 0 ? (costPerPortion / sellPrice) * 100 : 0
  const grossMargin = sellPrice - costPerPortion
  const grossMarginPercent = sellPrice > 0 ? (grossMargin / sellPrice) * 100 : 0

  const suggestedPrice = targetCmv > 0 ? costPerPortion / (targetCmv / 100) : 0

  // Matrix classification based on margin vs average (simplified simulation)
  // In a real scenario, volume comes from sales data. We simulate a heuristic here.
  const isHighMargin = grossMarginPercent >= 65
  const classification = isHighMargin ? "Estrela / Quebra-Cabeça (Alta Margem)" : "Burro de Carga / Cão (Baixa Margem)"
  const cmvHealth = currentCmv > 0 && currentCmv <= 30 ? "excellent" : currentCmv > 0 && currentCmv <= 35 ? "warning" : "danger"

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)

  return (
    <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-5 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <Calculator className="h-5 w-5 text-cyan-400" />
          Simulador de Margem & CMV
        </h3>
        {isMenuItem && currentCmv > 0 && (
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium border ${
              cmvHealth === "excellent"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                : cmvHealth === "warning"
                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                : "bg-rose-500/10 text-rose-400 border-rose-500/20"
            }`}
          >
            {cmvHealth === "excellent"
              ? "Margem Saudável"
              : cmvHealth === "warning"
              ? "Atenção ao Custo"
              : "Custo Crítico"}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/30">
          <p className="text-sm text-slate-400 mb-1">Custo do Lote</p>
          <p className="text-2xl font-bold text-slate-200">{formatCurrency(totalBatchCost)}</p>
          <p className="text-xs text-slate-500 mt-1">Rendimento: {yieldQuantity}</p>
        </div>
        <div className="p-4 bg-slate-800/40 rounded-lg border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.05)]">
          <p className="text-sm text-cyan-400/80 mb-1">Custo por Porção</p>
          <p className="text-2xl font-bold text-cyan-300">{formatCurrency(costPerPortion)}</p>
          <p className="text-xs text-slate-500 mt-1">Porção: {portionSize}</p>
        </div>
      </div>

      {isMenuItem && (
        <div className="space-y-5 pt-4 border-t border-slate-800">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-300">
                Simular Preço de Venda (R$)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={sellPrice || ""}
                  onChange={(e) => setSellPrice(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-slate-200 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all"
                  placeholder="0.00"
                />
              </div>

              <div className="flex justify-between items-center p-3 bg-slate-800/30 rounded-lg">
                <span className="text-sm text-slate-400">CMV Real:</span>
                <span
                  className={`font-bold ${
                    currentCmv > 35 ? "text-rose-400" : currentCmv > 30 ? "text-amber-400" : "text-emerald-400"
                  }`}
                >
                  {currentCmv > 0 ? currentCmv.toFixed(1) + "%" : "---"}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-slate-800/30 rounded-lg">
                <span className="text-sm text-slate-400">Lucro Bruto:</span>
                <span className="font-bold text-slate-200">{formatCurrency(grossMargin)}</span>
              </div>
            </div>

            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-300 flex items-center gap-2">
                <Target className="h-4 w-4 text-violet-400" />
                Meta de CMV Alvo (%)
              </label>
              <div className="relative">
                <Percent className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={targetCmv}
                  onChange={(e) => setTargetCmv(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-slate-200 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-all"
                />
              </div>

              <div className="p-4 bg-violet-500/10 border border-violet-500/20 rounded-lg">
                <p className="text-sm text-violet-300/80 mb-1">Preço Sugerido</p>
                <p className="text-2xl font-bold text-violet-300">{formatCurrency(suggestedPrice)}</p>
                <p className="text-xs text-violet-400/60 mt-1">Baseado no alvo de {targetCmv}%</p>
              </div>
            </div>
          </div>

          <div className="pt-2">
             <div className="flex items-center gap-2 text-sm">
                <span className="text-slate-400">Posição Estimada (Engenharia):</span>
                <span className={isHighMargin ? "text-emerald-400 font-medium" : "text-amber-400 font-medium"}>
                  {classification}
                </span>
             </div>
          </div>
        </div>
      )}
    </div>
  )
}
