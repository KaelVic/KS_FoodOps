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
  CreditCard,
  Landmark,
  FileSpreadsheet,
  CalendarDays,
  LineChart,
  LogOut,
  Hexagon,
  Lightbulb,
  Sparkles,
  UtensilsCrossed,
  Flame,
  Bike,
  Users,
  Factory,
  ArrowLeftRight,
  Scale,
  Bot
} from "lucide-react"
import { cn } from "@/lib/utils"

import { logoutAction } from "@/app/(auth)/actions"

const NAV_ITEMS = [
  { name: "Command Center", href: "/dashboard", icon: LayoutDashboard },
  { name: "FoodOps Copilot (IA)", href: "/copilot", icon: Bot },
  { name: "Mesas & Salão (PDV)", href: "/pos/tables", icon: Users },
  { name: "KDS (Cozinha & Bar)", href: "/kds", icon: Flame },
  { name: "Delivery Hub", href: "/delivery", icon: Bike },
  { name: "RH & Equipe (Escalas/Ponto)", href: "/team", icon: Users },
  { name: "Prime Cost (CMV + CMO)", href: "/team/prime-cost", icon: LineChart },
  { name: "Ordens de Produção (OP)", href: "/production/orders", icon: Factory },
  { name: "Transferências", href: "/inventory/transfers", icon: ArrowLeftRight },
  { name: "Cotações B2B (RFQ)", href: "/purchasing/rfqs", icon: Scale },
  { name: "Inteligência & ABC", href: "/intelligence", icon: Lightbulb },
  { name: "Engenharia de Menu (BCG)", href: "/menu/engineering", icon: Sparkles },
  { name: "Cardápio & Preços", href: "/menu/items", icon: UtensilsCrossed },
  { name: "Contas a Pagar (ERP)", href: "/financial/payables", icon: CreditCard },
  { name: "Contas a Receber (ERP)", href: "/financial/receivables", icon: TrendingUp },
  { name: "Fluxo de Caixa (ERP)", href: "/financial/cash-flow", icon: CalendarDays },
  { name: "DRE Gerencial (ERP)", href: "/financial/dre", icon: LineChart },
  { name: "Contas & Caixas", href: "/financial/bank-accounts", icon: Landmark },
  { name: "Estoque & Saldos", href: "/inventory", icon: PackageSearch },
  { name: "Inventário Físico", href: "/inventory-sessions", icon: PackageSearch },
  { name: "Pedidos de Compra", href: "/purchase-orders", icon: ShoppingCart },
  { name: "Ingestão de NFe", href: "/purchasing", icon: ShoppingCart },
  { name: "Fichas Técnicas", href: "/recipes", icon: ChefHat },
  { name: "Vendas & Teórico", href: "/sales", icon: TrendingUp },
  { name: "Fechamento & DRE", href: "/reports/closing", icon: FileSpreadsheet },
]


export function Sidebar({ email }: { email: string }) {
  const pathname = usePathname()

  return (
    <aside className="w-72 border-r border-slate-800/50 bg-[rgba(3,7,18,0.6)] backdrop-blur-2xl flex flex-col relative overflow-hidden h-full">
      {/* Decorative ambient glow */}
      <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-[rgba(0,240,255,0.05)] to-transparent pointer-events-none" />
      
      {/* Logo Area */}
      <div className="flex h-20 shrink-0 items-center px-6 border-b border-slate-800/50 relative z-10">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 border border-[rgba(0,240,255,0.3)] shadow-[0_0_15px_rgba(0,240,255,0.2)] mr-4 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-[#00f0ff] to-[#a855f7] opacity-20" />
          <Hexagon className="h-5 w-5 text-[#00f0ff]" />
        </div>
        <div className="flex flex-col">
          <h1 className="text-lg font-bold tracking-widest text-slate-100 uppercase">KS FoodOps</h1>
          <span className="text-[10px] tracking-widest text-[#00f0ff] font-mono">SYS.VER.9.0 (ERP PRO)</span>
        </div>
      </div>

      {/* Navigation - Scrollable Area */}
      <nav className="flex-1 space-y-1.5 p-4 relative z-10 overflow-y-auto min-h-0 pr-3">
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
                  "flex items-center gap-3.5 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors relative z-10",
                  isActive 
                    ? "text-[#00f0ff]" 
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
                )}
                whileHover={{ x: 4 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
              >
                <Icon className={cn("h-4.5 w-4.5 transition-colors shrink-0", isActive ? "text-[#00f0ff]" : "text-slate-500")} />
                <span className="truncate">{item.name}</span>
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

      {/* User Profile & Logout - Fixed at bottom */}
      <div className="p-4 border-t border-slate-800/50 bg-slate-900/40 relative z-10 shrink-0 mt-auto">
        <div className="mb-3 flex items-center gap-3 px-1">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 border border-slate-700 text-sm font-bold text-slate-300 shrink-0">
            {email.charAt(0).toUpperCase()}
          </div>
          <div className="flex flex-col overflow-hidden">
            <span className="truncate text-xs font-medium text-slate-200">{email}</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="flex h-1.5 w-1.5 rounded-full bg-[#10b981] shadow-[0_0_5px_#10b981]" />
              <span className="truncate text-[9px] tracking-widest uppercase font-mono text-[#10b981]">Conectado</span>
            </div>
          </div>
        </div>
        <form action={logoutAction}>
          <button type="submit" className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-xs font-medium text-slate-400 transition-all hover:bg-slate-800 hover:text-white hover:border-slate-700 cursor-pointer">
            <LogOut className="h-3.5 w-3.5" />
            Desconectar
          </button>
        </form>
      </div>
    </aside>
  )
}

