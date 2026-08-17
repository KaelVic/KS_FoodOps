"use client"

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { 
  Bot, Send, Sparkles, AlertTriangle, CheckCircle2, 
  TrendingUp, DollarSign, PackageSearch, UtensilsCrossed, 
  MessageSquare, Share2, Copy, Check, ShieldAlert, 
  Flame, Radio, RefreshCw, Layers, ArrowRight, Zap
} from "lucide-react"
import { 
  sendCopilotMessageClient, 
  fetchCopilotAuditClient, 
  fetchTodayBriefingClient, 
  dispatchBriefingClient 
} from "@/lib/api-client"

interface CopilotClientProps {
  initialAudit: any | null
  initialBriefing: any | null
}

interface Message {
  id: string
  sender: "USER" | "COPILOT"
  content: string
  created_at: string
}

export function CopilotClient({ initialAudit, initialBriefing }: CopilotClientProps) {
  const [messages, setMessages] = React.useState<Message[]>([
    {
      id: "welcome",
      sender: "COPILOT",
      content: "👋 **Olá! Eu sou o FoodOps Copilot**, sua IA agêntica para gestão de restaurantes.\n\nAnalisei o faturamento, CMV, CMO, estoque e tempos de cozinha em tempo real. Como posso ajudar na sua operação hoje?",
      created_at: new Date().toISOString()
    }
  ])

  const [inputPrompt, setInputPrompt] = React.useState("")
  const [isLoading, setIsLoading] = React.useState(false)
  const [conversationId, setConversationId] = React.useState<string | undefined>(undefined)

  const [audit, setAudit] = React.useState<any | null>(initialAudit)
  const [briefing, setBriefing] = React.useState<any | null>(initialBriefing)
  const [copied, setCopied] = React.useState(false)
  const [dispatchStatus, setDispatchStatus] = React.useState<string | null>(null)

  const chatEndRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSendMessage = async (textToSend?: string) => {
    const prompt = textToSend || inputPrompt
    if (!prompt.trim() || isLoading) return

    const tempUserMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "USER",
      content: prompt,
      created_at: new Date().toISOString()
    }

    setMessages(prev => [...prev, tempUserMsg])
    if (!textToSend) setInputPrompt("")
    setIsLoading(true)

    try {
      const res = await sendCopilotMessageClient(prompt, conversationId)
      if (res.conversation_id) setConversationId(res.conversation_id)

      const copilotReply: Message = {
        id: res.message_id || `bot-${Date.now()}`,
        sender: "COPILOT",
        content: res.content,
        created_at: res.created_at || new Date().toISOString()
      }
      setMessages(prev => [...prev, copilotReply])
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "COPILOT",
          content: `❌ **Erro ao processar:** ${err.message || "Não foi possível consultar a base de dados."}`,
          created_at: new Date().toISOString()
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopyWhatsApp = () => {
    if (!briefing?.summary_text) return
    navigator.clipboard.writeText(briefing.summary_text)
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }

  const handleDispatchWhatsApp = async () => {
    setDispatchStatus("Enviando...")
    try {
      await dispatchBriefingClient("WHATSAPP")
      setDispatchStatus("Enviado com Sucesso!")
      setTimeout(() => setDispatchStatus(null), 3000)
    } catch (err) {
      setDispatchStatus("Falha no Envio")
      setTimeout(() => setDispatchStatus(null), 3000)
    }
  }

  const quickPrompts = [
    { label: "📊 Auditar Prime Cost (CMV+CMO)", prompt: "Qual é o nosso Prime Cost atual e como reduzir o CMV?" },
    { label: "🚨 Checar Risco de Ruptura de Estoque", prompt: "Quais insumos estão com risco de ruptura no estoque?" },
    { label: "📲 Gerar Resumo Diário para WhatsApp", prompt: "Gere o resumo executivo diário para envio no WhatsApp da diretoria." },
    { label: "🎯 Análise 360° da Operação", prompt: "Faça uma auditoria 360 graus completa do restaurante agora." },
  ]

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono tracking-widest text-[#00f0ff] uppercase bg-[#00f0ff]/10 px-2 py-0.5 rounded border border-[#00f0ff]/20 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00f0ff] animate-pulse" />
              NEURAL AGENTIC CORE
            </span>
            <span className="text-[11px] font-mono tracking-widest text-purple-400 uppercase bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
              FASE 9 (FINAL ERP)
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 flex items-center gap-3">
            <Bot className="w-8 h-8 text-[#00f0ff]" />
            FoodOps Copilot — IA Agêntica & Automação Preditiva
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Auditoria autônoma 360°, detecção preditiva de desvios de CMV/CMO e resumos diários para WhatsApp.
          </p>
        </div>
      </div>

      {/* Main Grid: Chat Left (7 cols) / Diagnostics Right (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Chat Window */}
        <div className="lg:col-span-7 flex flex-col h-[700px] rounded-2xl bg-slate-900/60 border border-slate-800/90 backdrop-blur-xl shadow-2xl overflow-hidden relative">
          
          {/* Chat Header */}
          <div className="p-4 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00f0ff] to-[#a855f7] flex items-center justify-center shadow-[0_0_10px_rgba(0,240,255,0.3)]">
                <Sparkles className="w-4 h-4 text-slate-950" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                  FoodOps Intelligence Engine
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                </div>
                <div className="text-[10px] font-mono text-slate-400">RAG Ativo sobre Dados do Restaurante</div>
              </div>
            </div>

            <button
              onClick={() => setMessages([{
                id: `reset-${Date.now()}`,
                sender: "COPILOT",
                content: "🔄 **Sessão reiniciada.** Como posso ajudar você agora?",
                created_at: new Date().toISOString()
              }])}
              className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-xs transition-colors"
              title="Limpar Conversa"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${m.sender === "USER" ? "justify-end" : "justify-start"}`}
              >
                {m.sender === "COPILOT" && (
                  <div className="w-7 h-7 rounded-lg bg-[#00f0ff]/10 border border-[#00f0ff]/30 flex items-center justify-center flex-shrink-0 text-[#00f0ff]">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed ${
                  m.sender === "USER"
                    ? "bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-medium rounded-tr-none shadow-lg shadow-[#00f0ff]/10"
                    : "bg-slate-950/90 border border-slate-800 text-slate-200 rounded-tl-none whitespace-pre-line prose prose-invert prose-xs"
                }`}>
                  {m.content}
                </div>
              </motion.div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-slate-400 text-xs py-2 px-3 bg-slate-950/60 rounded-xl w-fit border border-slate-800">
                <Sparkles className="w-3.5 h-3.5 animate-spin text-[#00f0ff]" />
                <span>Analisando base de dados operacional...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Quick Prompts */}
          <div className="px-4 py-2 bg-slate-950/40 border-t border-slate-800/60 flex items-center gap-1.5 overflow-x-auto">
            {quickPrompts.map((qp, i) => (
              <button
                key={i}
                onClick={() => handleSendMessage(qp.prompt)}
                className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/60 text-[10px] font-medium text-slate-300 hover:text-slate-100 transition-all flex-shrink-0"
              >
                {qp.label}
              </button>
            ))}
          </div>

          {/* Input Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSendMessage()
            }}
            className="p-3 bg-slate-950 border-t border-slate-800 flex items-center gap-2"
          >
            <input
              type="text"
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              placeholder="Pergunte ao Copilot sobre CMV, Prime Cost, Rupturas ou Vendas..."
              className="flex-1 px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#00f0ff]"
            />
            <button
              type="submit"
              disabled={isLoading || !inputPrompt.trim()}
              className="p-2.5 rounded-xl bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-bold hover:opacity-95 transition-all disabled:opacity-40"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Right Column: WhatsApp Briefing & 360 Diagnostics */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* WhatsApp Executive Briefing Card */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-emerald-500/30 backdrop-blur-xl space-y-3 relative overflow-hidden shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Share2 className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold font-mono text-slate-100 uppercase tracking-wider">
                  Resumo WhatsApp (Diretoria)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                1-CLICK DISPATCH
              </span>
            </div>

            {briefing && (
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 whitespace-pre-line leading-relaxed max-h-56 overflow-y-auto">
                {briefing.summary_text}
              </div>
            )}

            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={handleCopyWhatsApp}
                className="flex-1 py-2 px-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? "Copiado para o Clipboard!" : "Copiar para WhatsApp"}
              </button>

              <button
                onClick={handleDispatchWhatsApp}
                className="py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
              >
                {dispatchStatus || "Webhook"}
              </button>
            </div>
          </div>

          {/* 360 Operational Audit Diagnostics */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-[#00f0ff]" />
                <h3 className="text-xs font-bold font-mono text-slate-100 uppercase tracking-wider">
                  Auditoria 360° em Tempo Real
                </h3>
              </div>
              {audit && (
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                  audit.overall_health === "HEALTHY" || audit.overall_health === "EXCELLENT"
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                }`}>
                  STATUS: {audit.overall_health}
                </span>
              )}
            </div>

            <div className="space-y-3">
              {audit?.diagnostics?.map((d: any, index: number) => (
                <div 
                  key={index}
                  className={`p-3.5 rounded-xl border space-y-1.5 ${
                    d.severity === "CRITICAL"
                      ? "bg-rose-500/5 border-rose-500/30"
                      : d.severity === "WARNING"
                      ? "bg-amber-500/5 border-amber-500/30"
                      : "bg-emerald-500/5 border-emerald-500/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono tracking-wider font-bold text-slate-400">
                      {d.pillar}
                    </span>
                    <span className={`text-[10px] font-bold ${
                      d.severity === "CRITICAL" ? "text-rose-400" : (d.severity === "WARNING" ? "text-amber-400" : "text-emerald-400")
                    }`}>
                      {d.severity}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-slate-100">{d.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-normal">{d.detail}</p>
                  
                  <div className="pt-1 flex items-center gap-1.5 text-[10px] font-semibold text-[#00f0ff]">
                    <ArrowRight className="w-3 h-3 flex-shrink-0" />
                    <span>{d.action}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  )
}
