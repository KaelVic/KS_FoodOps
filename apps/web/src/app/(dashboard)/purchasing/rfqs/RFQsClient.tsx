"use client"

import * as React from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { 
  FileText, Plus, Search, Filter, ArrowRight, Building2, Calendar, 
  CheckCircle2, Clock, AlertCircle, Sparkles, Scale, DollarSign, Layers
} from "lucide-react"

interface RFQItem {
  id: string
  rfq_number: string
  title: string
  location_id?: string
  status: string
  deadline?: string
  notes?: string
  created_at: string
  updated_at: string
}

export function RFQsClient({ initialRfqs }: { initialRfqs: RFQItem[] }) {
  const [rfqs, setRfqs] = React.useState<RFQItem[]>(initialRfqs)
  const [search, setSearch] = React.useState("")
  const [statusFilter, setStatusFilter] = React.useState("ALL")

  const filteredRfqs = rfqs.filter(r => {
    const matchesSearch = r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.rfq_number.toLowerCase().includes(search.toLowerCase())
    const matchesStatus = statusFilter === "ALL" || r.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "DRAFT":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700"><Clock className="w-3 h-3" /> Rascunho</span>
      case "OPEN":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30"><AlertCircle className="w-3 h-3" /> Aberta (Cotando)</span>
      case "EVALUATING":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30"><Scale className="w-3 h-3" /> Em Avaliação</span>
      case "AWARDED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"><CheckCircle2 className="w-3 h-3" /> Homologada (PO Gerado)</span>
      case "CANCELLED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/30">Cancelada</span>
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">{status}</span>
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono tracking-widest text-[#00f0ff] uppercase bg-[#00f0ff]/10 px-2 py-0.5 rounded border border-[#00f0ff]/20">
              SUPPLY CHAIN & B2B
            </span>
            <span className="text-[11px] font-mono tracking-widest text-emerald-400 uppercase bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              FASE 7 ERP
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 flex items-center gap-3">
            <Scale className="w-8 h-8 text-[#00f0ff]" />
            Cotações Eletrônicas B2B (RFQs)
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Tomada de preços com fornecedores homologados, quadro comparativo automático e emissão direta de Pedidos de Compra.
          </p>
        </div>

        <Link
          href="/purchasing/rfqs/new"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-semibold shadow-lg shadow-[#00f0ff]/20 hover:opacity-95 transition-all text-sm"
        >
          <Plus className="w-4 h-4" />
          Nova Cotação B2B
        </Link>
      </div>

      {/* Highlights / Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">TOTAL COTAÇÕES</span>
            <FileText className="w-4 h-4 text-slate-500" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{rfqs.length}</p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-blue-400">EM ANDAMENTO</span>
            <Clock className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-blue-300 mt-2">
            {rfqs.filter(r => r.status === "OPEN" || r.status === "EVALUATING").length}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-emerald-400">HOMOLOGADAS (PO)</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-300 mt-2">
            {rfqs.filter(r => r.status === "AWARDED").length}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-amber-400">ECONOMIA MÉDIA</span>
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-amber-300 mt-2">~14.2%</p>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/40 border border-slate-800/80">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Buscar por título ou número da cotação..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#00f0ff]/50"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <Filter className="w-4 h-4 text-slate-500 flex-shrink-0" />
          {["ALL", "OPEN", "EVALUATING", "AWARDED", "DRAFT"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex-shrink-0 ${
                statusFilter === st
                  ? "bg-[#00f0ff]/20 text-[#00f0ff] border border-[#00f0ff]/40"
                  : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {st === "ALL" ? "Todos" : st}
            </button>
          ))}
        </div>
      </div>

      {/* List / Cards */}
      {filteredRfqs.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800/80 flex flex-col items-center justify-center">
          <FileText className="w-12 h-12 text-slate-600 mb-3" />
          <h3 className="text-base font-semibold text-slate-300">Nenhuma cotação encontrada</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm">
            Inicie sua primeira tomada de preços para cotar insumos com múltiplos fornecedores e otimizar custos.
          </p>
          <Link
            href="/purchasing/rfqs/new"
            className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all inline-flex items-center gap-2"
          >
            <Plus className="w-3.5 h-3.5" />
            Criar Cotação B2B
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {filteredRfqs.map((rfq) => (
            <motion.div
              key={rfq.id}
              whileHover={{ y: -2 }}
              className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition-all backdrop-blur-xl flex flex-col md:flex-row md:items-center md:justify-between gap-4"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-[#00f0ff] font-bold bg-[#00f0ff]/10 px-2 py-0.5 rounded border border-[#00f0ff]/20">
                    {rfq.rfq_number}
                  </span>
                  {getStatusBadge(rfq.status)}
                  {rfq.deadline && (
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <Calendar className="w-3 h-3" /> Prazo: {new Date(rfq.deadline).toLocaleDateString("pt-BR")}
                    </span>
                  )}
                </div>

                <h2 className="text-base font-bold text-slate-100">{rfq.title}</h2>
                {rfq.notes && (
                  <p className="text-xs text-slate-400 line-clamp-1">{rfq.notes}</p>
                )}
              </div>

              <div className="flex items-center gap-3 self-end md:self-center">
                <Link
                  href={`/purchasing/rfqs/${rfq.id}`}
                  className="px-4 py-2 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all inline-flex items-center gap-2 group"
                >
                  <span>Ver Detalhes & Comparativo</span>
                  <ArrowRight className="w-3.5 h-3.5 text-[#00f0ff] group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
