"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { Activity, Bell, Search, ServerCog, Store } from "lucide-react"

export function Header({ tenantName }: { tenantName?: string }) {
  return (
    <header className="h-20 border-b border-slate-800/50 bg-[rgba(3,7,18,0.4)] backdrop-blur-md flex items-center justify-between px-8 relative z-20">
      <div className="flex items-center gap-6">
        {/* Active Tenant Display */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900 border border-slate-800 text-slate-400">
            <Store className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] tracking-widest text-slate-500 font-mono uppercase">Unidade Operacional</span>
            <span className="text-sm font-semibold text-slate-200">{tenantName || "Selecione uma Unidade"}</span>
          </div>
        </div>

        {/* Global Search */}
        <div className="ml-8 relative group hidden md:block">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-slate-500 group-focus-within:text-[#00f0ff] transition-colors" />
          </div>
          <input 
            type="text" 
            placeholder="Buscar insumos, receitas, NFe..." 
            className="block w-96 pl-10 pr-3 py-2 border border-slate-800 rounded-lg leading-5 bg-slate-900/50 text-slate-300 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-[#00f0ff] focus:border-[#00f0ff] sm:text-sm transition-all shadow-inner"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Telemetry Status */}
        <div className="flex items-center gap-3 px-4 py-1.5 rounded-full bg-slate-900/80 border border-slate-800">
          <motion.div 
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="flex items-center justify-center"
          >
            <Activity className="h-4 w-4 text-[#10b981]" />
          </motion.div>
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">API:</span>
            <span className="text-[#10b981]">ONLINE</span>
            <span className="text-slate-600 ml-1">|</span>
            <span className="text-slate-400 ml-1">RLS:</span>
            <span className="text-[#00f0ff]">SECURE</span>
          </div>
        </div>

        {/* Notification Bell */}
        <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 block h-2 w-2 rounded-full bg-[#ef4444] shadow-[0_0_8px_#ef4444]" />
        </button>

        {/* System Config */}
        <button className="p-2 text-slate-400 hover:text-[#a855f7] transition-colors">
          <ServerCog className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}
