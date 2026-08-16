"use client"

import * as React from "react"
import { motion, type Variants } from "framer-motion"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import { 
  ArrowUpRight, 
  ArrowDownRight, 
  Zap, 
  TrendingUp, 
  AlertTriangle,
  PlayCircle,
  FileText
} from "lucide-react"

export default function ExecutiveDashboard() {
  const container: Variants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const item: Variants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  }

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100">Executive Command Center</h2>
          <p className="text-slate-400 mt-1">Visão geral da operação, telemetria de estoque e performance financeira.</p>
        </div>
        <div className="flex gap-3">
          <Badge variant="cyan" className="px-3 py-1">Atualizado agora</Badge>
          <Badge variant="emerald" className="px-3 py-1">Conectado ao Engine V7</Badge>
        </div>
      </div>

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-6 flex-1"
      >
        {/* Widget 1: CMV Gauge (Hero) */}
        <motion.div variants={item} className="col-span-1 md:col-span-2 lg:col-span-2 row-span-2">
          <GlassPanel accent="cyan" hoverEffect className="h-full p-6 flex flex-col">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-200">CMV Operacional</h3>
                <p className="text-xs text-slate-500 font-mono mt-1">REAL vs TEÓRICO</p>
              </div>
              <div className="p-2 bg-[rgba(0,240,255,0.1)] rounded-lg">
                <TrendingUp className="h-5 w-5 text-[#00f0ff]" />
              </div>
            </div>
            
            <div className="flex-1 flex flex-col items-center justify-center relative">
              {/* Fake Holographic Gauge */}
              <div className="relative w-48 h-48 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                  <circle cx="50" cy="50" r="45" fill="none" stroke="url(#cyan-gradient)" strokeWidth="8" strokeDasharray="283" strokeDashoffset="70" strokeLinecap="round" className="drop-shadow-[0_0_10px_rgba(0,240,255,0.5)]" />
                  <defs>
                    <linearGradient id="cyan-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#00f0ff" />
                      <stop offset="100%" stopColor="#a855f7" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="text-4xl font-bold text-white text-glow-cyan">28.4%</span>
                  <span className="text-xs text-[#10b981] flex items-center mt-1">
                    <ArrowDownRight className="h-3 w-3 mr-1" />
                    -1.2% meta
                  </span>
                </div>
              </div>
            </div>
          </GlassPanel>
        </motion.div>

        {/* Widget 2: Alertas de Telemetria (Ruptura/Desvio) */}
        <motion.div variants={item} className="col-span-1 md:col-span-2 lg:col-span-4">
          <GlassPanel accent="amber" hoverEffect className="h-full p-6">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-slate-200">Alertas de Telemetria</h3>
                <p className="text-xs text-slate-500 font-mono mt-1">DETECÇÃO DE ANOMALIAS V7</p>
              </div>
              <Badge variant="amber" className="animate-pulse">3 Críticos</Badge>
            </div>
            <div className="space-y-3">
              {[
                { type: 'crimson', msg: "Estoque Crítico (Classe A): Filé Mignon Red Angus", time: "Há 2 mins" },
                { type: 'amber', msg: "Desvio de Consumo Detectado: Óleo de Soja (Teórico 10L / Real 15L)", time: "Há 15 mins" },
                { type: 'violet', msg: "Previsão de Ruptura: Tomate Italiano (Baseado em vendas projetadas)", time: "Há 1 hora" }
              ].map((alert, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.05)] transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`h-2 w-2 rounded-full shadow-[0_0_8px_currentColor] text-${alert.type === 'crimson' ? '#ef4444' : alert.type === 'amber' ? '#f59e0b' : '#a855f7'} bg-current`} />
                    <span className="text-sm text-slate-300">{alert.msg}</span>
                  </div>
                  <span className="text-xs text-slate-500 font-mono">{alert.time}</span>
                </div>
              ))}
            </div>
          </GlassPanel>
        </motion.div>

        {/* Widget 3: Curva ABC */}
        <motion.div variants={item} className="col-span-1 md:col-span-2 lg:col-span-2">
          <GlassPanel accent="violet" hoverEffect className="h-full p-6">
            <h3 className="text-lg font-semibold text-slate-200 mb-4">Distribuição Curva ABC</h3>
            <div className="flex flex-col gap-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300 font-bold">Classe A (80%)</span>
                  <span className="text-slate-500">12 itens</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: "80%" }} transition={{ duration: 1, delay: 0.2 }} className="h-full bg-gradient-to-r from-[#a855f7] to-[#00f0ff] shadow-[0_0_10px_#a855f7]" />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300">Classe B (15%)</span>
                  <span className="text-slate-500">45 itens</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: "15%" }} transition={{ duration: 1, delay: 0.4 }} className="h-full bg-slate-500" />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300">Classe C (5%)</span>
                  <span className="text-slate-500">180 itens</span>
                </div>
                <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: "5%" }} transition={{ duration: 1, delay: 0.6 }} className="h-full bg-slate-700" />
                </div>
              </div>
            </div>
          </GlassPanel>
        </motion.div>

        {/* Widget 4: Ações Rápidas */}
        <motion.div variants={item} className="col-span-1 md:col-span-2 lg:col-span-2">
          <GlassPanel accent="none" hoverEffect className="h-full p-6">
            <h3 className="text-lg font-semibold text-slate-200 mb-4">Ações Rápidas</h3>
            <div className="grid grid-cols-2 gap-3">
              <button className="flex flex-col items-center justify-center p-4 rounded-xl border border-[rgba(0,240,255,0.2)] bg-[rgba(0,240,255,0.05)] hover:bg-[rgba(0,240,255,0.1)] transition-colors group">
                <PlayCircle className="h-6 w-6 text-[#00f0ff] mb-2 group-hover:scale-110 transition-transform" />
                <span className="text-xs font-medium text-slate-300">Sessão de Inventário</span>
              </button>
              <button className="flex flex-col items-center justify-center p-4 rounded-xl border border-[rgba(168,85,247,0.2)] bg-[rgba(168,85,247,0.05)] hover:bg-[rgba(168,85,247,0.1)] transition-colors group">
                <FileText className="h-6 w-6 text-[#a855f7] mb-2 group-hover:scale-110 transition-transform" />
                <span className="text-xs font-medium text-slate-300">Importar XML (NFe)</span>
              </button>
              <button className="flex flex-col items-center justify-center p-4 rounded-xl border border-slate-700 bg-[rgba(255,255,255,0.02)] hover:bg-[rgba(255,255,255,0.05)] transition-colors group">
                <Zap className="h-6 w-6 text-slate-400 mb-2 group-hover:text-white transition-colors" />
                <span className="text-xs font-medium text-slate-300">Ajuste Manual</span>
              </button>
              <button className="flex flex-col items-center justify-center p-4 rounded-xl border border-slate-700 bg-[rgba(255,255,255,0.02)] hover:bg-[rgba(255,255,255,0.05)] transition-colors group">
                <ArrowUpRight className="h-6 w-6 text-slate-400 mb-2 group-hover:text-white transition-colors" />
                <span className="text-xs font-medium text-slate-300">Nova Receita</span>
              </button>
            </div>
          </GlassPanel>
        </motion.div>
      </motion.div>
    </div>
  )
}
