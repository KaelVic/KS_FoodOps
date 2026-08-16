"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { motion } from "framer-motion"
import { 
  LayoutDashboard, 
  PackageSearch, 
  ShoppingCart, 
  ChefHat, 
  TrendingUp,
  LogOut,
  Hexagon,
  Lightbulb
} from "lucide-react"
import { cn } from "@/lib/utils"

const NAV_ITEMS = [
  { name: "Command Center", href: "/dashboard", icon: LayoutDashboard },
  { name: "Inteligência", href: "/intelligence", icon: Lightbulb },
  { name: "Estoque", href: "/inventory", icon: PackageSearch },
  { name: "Inventário Físico", href: "/inventory-sessions", icon: PackageSearch },
  { name: "Pedidos de Compra", href: "/purchase-orders", icon: ShoppingCart },
  { name: "Ingestão de NFe", href: "/purchasing", icon: ShoppingCart },
  { name: "Reconciliação 3-Way", href: "/purchasing/reconciliation", icon: PackageSearch },
  { name: "Engenharia de Menu", href: "/recipes", icon: ChefHat },
  { name: "Vendas & Teórico", href: "/sales", icon: TrendingUp },
  { name: "Análise Teórico vs Real", href: "/reports/variance", icon: TrendingUp },
]

export function Sidebar({ email }: { email: string }) {
  const pathname = usePathname()

  return (
    <aside className="w-72 border-r border-slate-800/50 bg-[rgba(3,7,18,0.6)] backdrop-blur-2xl flex flex-col relative overflow-hidden">
      {/* Decorative ambient glow */}
      <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-[rgba(0,240,255,0.05)] to-transparent pointer-events-none" />
      
      {/* Logo Area */}
      <div className="flex h-20 items-center px-6 border-b border-slate-800/50 relative z-10">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 border border-[rgba(0,240,255,0.3)] shadow-[0_0_15px_rgba(0,240,255,0.2)] mr-4 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-[#00f0ff] to-[#a855f7] opacity-20" />
          <Hexagon className="h-5 w-5 text-[#00f0ff]" />
        </div>
        <div className="flex flex-col">
          <h1 className="text-lg font-bold tracking-widest text-slate-100 uppercase">KS FoodOps</h1>
          <span className="text-[10px] tracking-widest text-[#00f0ff] font-mono">SYS.VER.7.0</span>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 space-y-2 p-4 relative z-10 mt-4">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
          const Icon = item.icon
          
          return (
            <Link 
              key={item.name} 
              href={item.href}
              className="relative block"
            >
              <motion.div
                className={cn(
                  "flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-colors relative z-10",
                  isActive 
                    ? "text-[#00f0ff]" 
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
                )}
                whileHover={{ x: 4 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                <Icon className={cn("h-5 w-5 transition-colors", isActive ? "text-[#00f0ff]" : "text-slate-500")} />
                {item.name}
              </motion.div>
              
              {/* Active Indicator Glow */}
              {isActive && (
                <motion.div 
                  layoutId="activeNavIndicator"
                  className="absolute inset-0 rounded-lg bg-[rgba(0,240,255,0.08)] border border-[rgba(0,240,255,0.2)] shadow-[inset_0_0_12px_rgba(0,240,255,0.1)] z-0"
                  initial={false}
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </Link>
          )
        })}
      </nav>

      {/* User Profile & Logout */}
      <div className="p-4 border-t border-slate-800/50 bg-slate-900/20 relative z-10">
        <div className="mb-4 flex items-center gap-3 px-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 border border-slate-700 text-sm font-bold text-slate-300">
            {email.charAt(0).toUpperCase()}
          </div>
          <div className="flex flex-col overflow-hidden">
            <span className="truncate text-sm font-medium text-slate-200">{email}</span>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="flex h-1.5 w-1.5 rounded-full bg-[#10b981] shadow-[0_0_5px_#10b981]" />
              <span className="truncate text-[10px] tracking-widest uppercase font-mono text-[#10b981]">Conectado</span>
            </div>
          </div>
        </div>
        <form action="/api/logout" method="POST">
          <button type="submit" className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2.5 text-sm font-medium text-slate-400 transition-all hover:bg-slate-800 hover:text-white hover:border-slate-700">
            <LogOut className="h-4 w-4" />
            Desconectar
          </button>
        </form>
      </div>
    </aside>
  )
}
