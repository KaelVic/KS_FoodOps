"use client"

import { useState } from "react"
import { TrendingDown, Filter, AlertTriangle, ArrowRight } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"

import { GlassPanel } from "@/components/ui/glass-panel"
import { VarianceReportItem } from "@/types/reports"

export default function VarianceClient({ 
  initialData 
}: { 
  initialData: VarianceReportItem[]
}) {
  const [searchTerm, setSearchTerm] = useState("")

  const filteredData = initialData.filter(item => 
    item.sku_name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(val)
  }

  const totalTheoreticalCost = initialData.reduce((acc, curr) => acc + curr.theoretical_cost, 0)
  const totalItems = initialData.length
  // Estimate accuracy based on total expected vs losses. A very simplified metric for demo.
  const totalDepletion = initialData.reduce((acc, curr) => acc + curr.total_expected_depletion, 0)
  const totalLosses = initialData.reduce((acc, curr) => acc + curr.registered_losses_quantity, 0)
  const lossRate = totalDepletion > 0 ? (totalLosses / totalDepletion) * 100 : 0

  // Chart Data Preparation (Top 10 items by theoretical cost)
  const chartData = [...initialData]
    .sort((a, b) => b.theoretical_cost - a.theoretical_cost)
    .slice(0, 10)
    .map(item => ({
      name: item.sku_name.length > 15 ? item.sku_name.substring(0, 15) + "..." : item.sku_name,
      'Consumo Teórico': Number(item.theoretical_quantity.toFixed(2)),
      'Depletado Real (C/ Perdas)': Number(item.total_expected_depletion.toFixed(2)),
      uom: item.uom_symbol
    }))

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl">
          <p className="font-bold text-slate-100 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm flex items-center gap-2" style={{ color: entry.color }}>
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }}></span>
              {entry.name}: <span className="font-mono font-bold">{entry.value}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6 pb-24">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <TrendingDown className="h-8 w-8 text-[#00f0ff]" />
            Teórico vs Real & Perdas
          </h2>
          <p className="text-slate-400 mt-1">
            Analise o impacto financeiro da depleção teórica gerada por vendas versus o consumo real e perdas operacionais.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassPanel className="flex flex-col gap-2 border-l-4 border-l-[#00f0ff]">
          <span className="text-sm font-medium text-slate-400">Custo Teórico Acumulado</span>
          <span className="text-3xl font-bold text-[#00f0ff]">{formatCurrency(totalTheoreticalCost)}</span>
          <span className="text-xs text-slate-500">Baseado em Vendas POS x Fichas Técnicas</span>
        </GlassPanel>

        <GlassPanel className="flex flex-col gap-2 border-l-4 border-l-slate-600">
          <span className="text-sm font-medium text-slate-400">Total de Insumos Movimentados</span>
          <span className="text-3xl font-bold text-white">{totalItems} SKUs</span>
          <span className="text-xs text-slate-500">Registrando depleção ou perdas</span>
        </GlassPanel>

        <GlassPanel className="flex flex-col gap-2 border-l-4 border-l-[#ef4444]">
          <span className="text-sm font-medium text-slate-400">Taxa de Perda Operacional</span>
          <span className="text-3xl font-bold text-[#ef4444]">{lossRate.toFixed(2)}%</span>
          <span className="text-xs text-[#ef4444]/70">Proporção de perdas sobre o consumo total</span>
        </GlassPanel>
      </div>

      {/* CHART SECTION */}
      {chartData.length > 0 && (
        <GlassPanel className="p-6 h-[450px] w-full flex flex-col">
          <h3 className="text-lg font-bold text-slate-100 mb-6 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-[#f59e0b]" />
            Top 10 Insumos (Custo Teórico) vs Consumo Real
          </h3>
          <div className="flex-1 w-full h-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 0, bottom: 25 }}
                barGap={8}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis 
                  dataKey="name" 
                  stroke="#94a3b8" 
                  fontSize={12} 
                  tickMargin={10} 
                  angle={-25} 
                  textAnchor="end"
                />
                <YAxis 
                  stroke="#94a3b8" 
                  fontSize={12} 
                  tickFormatter={(value) => `${value}`}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: '#334155', opacity: 0.4 }} />
                <Legend wrapperStyle={{ paddingTop: "20px" }} />
                <Bar 
                  dataKey="Consumo Teórico" 
                  fill="#00f0ff" 
                  radius={[4, 4, 0, 0]} 
                  barSize={20}
                />
                <Bar 
                  dataKey="Depletado Real (C/ Perdas)" 
                  fill="#ef4444" 
                  radius={[4, 4, 0, 0]} 
                  barSize={20}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassPanel>
      )}

      {/* TABLE SECTION */}
      <GlassPanel className="p-0 overflow-hidden flex flex-col">
        <div className="p-4 border-b border-slate-700 bg-slate-800/30 flex items-center justify-between">
          <div className="relative flex-1 max-w-md">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
            <input
              type="text"
              placeholder="Filtrar Insumo..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-slate-100 focus:outline-none focus:border-[#00f0ff] focus:ring-1 focus:ring-[#00f0ff] transition-all shadow-inner"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-700 uppercase text-xs tracking-wider">
              <tr>
                <th className="px-6 py-4 font-semibold">Insumo</th>
                <th className="px-6 py-4 font-semibold text-center border-l border-slate-700/50 bg-[#00f0ff]/5">1. Consumo Teórico</th>
                <th className="px-6 py-4 font-semibold text-center border-l border-slate-700/50 bg-[#f59e0b]/5">2. Perdas Registradas</th>
                <th className="px-6 py-4 font-semibold text-center border-l border-slate-700/50 bg-[#ef4444]/5">3. Total Depletado (Real)</th>
                <th className="px-6 py-4 font-semibold text-right text-[#00f0ff] border-l border-slate-700/50">Custo Teórico Estimado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-slate-300">
              {filteredData.map(row => {
                const isDivergent = row.total_expected_depletion > row.theoretical_quantity;
                
                return (
                  <tr key={row.sku_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-100 text-base">{row.sku_name}</div>
                      <div className="text-xs text-slate-500 font-mono">{row.uom_symbol}</div>
                    </td>
                    <td className="px-6 py-4 text-center font-mono text-slate-300 border-l border-slate-700/50 bg-[#00f0ff]/5">
                      {row.theoretical_quantity.toFixed(3)}
                    </td>
                    <td className={`px-6 py-4 text-center font-mono border-l border-slate-700/50 bg-[#f59e0b]/5 ${row.registered_losses_quantity > 0 ? "text-[#f59e0b] font-bold" : "text-slate-500"}`}>
                      {row.registered_losses_quantity > 0 ? `+ ${row.registered_losses_quantity.toFixed(3)}` : "-"}
                    </td>
                    <td className={`px-6 py-4 text-center font-mono border-l border-slate-700/50 bg-[#ef4444]/5 ${isDivergent ? 'text-[#ef4444] font-bold' : 'text-slate-300'}`}>
                      {row.total_expected_depletion.toFixed(3)}
                    </td>
                    <td className="px-6 py-4 text-right font-mono text-[#00f0ff] font-bold border-l border-slate-700/50">
                      {formatCurrency(row.theoretical_cost)}
                    </td>
                  </tr>
                )
              })}
              {filteredData.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                    <TrendingDown className="h-10 w-10 mx-auto mb-3 opacity-20" />
                    Nenhum dado encontrado para os filtros selecionados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </GlassPanel>
    </div>
  )
}
