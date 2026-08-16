"use client"

import * as React from "react"
import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import {
  Upload,
  FileText,
  Eye,
  CheckCircle,
  AlertTriangle,
  Clock,
  Loader2,
  XCircle,
  Trash2,
  ShoppingCart,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { uploadNFeFile, approveExtractionAction, fetchExtractions } from "@/lib/api-client"
import { DocumentExtractionItem } from "@/types/documents"

interface PurchasingClientProps {
  initialExtractions: DocumentExtractionItem[]
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function formatDate(dateString: string | null): string {
  if (!dateString) return "—"
  try {
    return new Date(dateString).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    })
  } catch {
    return "—"
  }
}

function getStatusBadge(status: string) {
  switch (status) {
    case "APPROVED":
      return <Badge variant="emerald"><CheckCircle className="h-3 w-3 mr-1" /> Aprovado</Badge>
    case "READY_FOR_APPROVAL":
      return <Badge variant="amber"><AlertTriangle className="h-3 w-3 mr-1" /> Pronto p/ Aprovação</Badge>
    case "NEEDS_REVIEW":
      return <Badge variant="crimson"><Clock className="h-3 w-3 mr-1" /> Revisão Necessária</Badge>
    default:
      return <Badge variant="violet"><Clock className="h-3 w-3 mr-1" /> {status}</Badge>
  }
}

export default function PurchasingClient({ initialExtractions }: PurchasingClientProps) {
  const [extractions, setExtractions] = React.useState<DocumentExtractionItem[]>(initialExtractions)
  const [uploading, setUploading] = React.useState(false)
  const [uploadMessage, setUploadMessage] = React.useState<{ type: "success" | "error"; text: string } | null>(null)
  const [approvingId, setApprovingId] = React.useState<string | null>(null)
  const [dragActive, setDragActive] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const refreshExtractions = async () => {
    const data = await fetchExtractions()
    setExtractions(data)
  }

  const handleFileSelect = (file: File | null) => {
    if (!file) return
    if (!file.name.endsWith(".xml")) {
      setUploadMessage({ type: "error", text: "Por favor, selecione um arquivo .xml" })
      return
    }
    uploadFile(file)
  }

  const uploadFile = async (file: File) => {
    setUploading(true)
    setUploadMessage(null)

    const formData = new FormData()
    formData.append("file", file)

    const result = await uploadNFeFile(formData)
    setUploading(false)

    if (result) {
      setUploadMessage({ type: "success", text: `NFe ${result.invoice_number} importada com sucesso!` })
      await refreshExtractions()
      if (fileInputRef.current) fileInputRef.current.value = ""
    } else {
      setUploadMessage({ type: "error", text: "Falha ao importar NFe. Verifique o arquivo e tente novamente." })
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const file = e.dataTransfer.files[0]
    if (file) handleFileSelect(file)
  }

  const handleApprove = async (extractionId: string) => {
    setApprovingId(extractionId)
    const result = await approveExtractionAction(extractionId)
    setApprovingId(null)

    if (result?.success) {
      setUploadMessage({ type: "success", text: "Documento aprovado com sucesso!" })
      await refreshExtractions()
    } else {
      setUploadMessage({ type: "error", text: "Falha ao aprovar. Verifique se todas as linhas estão matchadas." })
    }
  }

  return (
    <div className="flex flex-col space-y-6">
      <GlassPanel accent="cyan" className="p-5 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-transparent to-violet-500/5 pointer-events-none" />
        <div className="relative">
          <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
            <Upload className="h-5 w-5 text-[#00f0ff]" />
            Carregar NFe XML
          </h3>

          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
              dragActive
                ? "border-[#00f0ff] bg-cyan-500/10"
                : "border-white/10 hover:border-white/20"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".xml"
              className="hidden"
              onChange={(e) => handleFileSelect(e.target.files?.[0] ?? null)}
              disabled={uploading}
            />
            <div className="flex flex-col items-center gap-3">
              <div className={`flex items-center justify-center w-16 h-16 rounded-full transition-colors ${
                dragActive ? "bg-cyan-500/20 text-[#00f0ff]" : "bg-white/5 text-slate-500"
              }`}>
                <Upload className="h-8 w-8" />
              </div>
              <div>
                <p className="text-slate-300 font-medium">Arraste e solte um arquivo <span className="font-mono text-[#00f0ff]">.xml</span> aqui</p>
                <p className="text-slate-500 text-sm mt-1">ou clique para selecionar</p>
              </div>
              {uploading && (
                <div className="flex items-center gap-2 text-cyan-400 mt-2">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Processando...</span>
                </div>
              )}
            </div>
          </div>

          <AnimatePresence>
            {uploadMessage && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className={`mt-4 p-3 rounded-lg flex items-center gap-3 ${
                  uploadMessage.type === "success"
                    ? "bg-emerald-500/20 border border-emerald-500/30 text-emerald-300"
                    : "bg-crimson-500/20 border border-crimson-500/30 text-crimson-300"
                }`}
              >
                {uploadMessage.type === "success" ? (
                  <CheckCircle className="h-5 w-5 flex-shrink-0" />
                ) : (
                  <XCircle className="h-5 w-5 flex-shrink-0" />
                )}
                <p className="text-sm">{uploadMessage.text}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </GlassPanel>

      <GlassPanel accent="cyan" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px]">
            <thead>
              <tr className="border-b border-white/5 bg-slate-950/50">
                <th className="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span className="flex items-center gap-2">
                    <FileText className="h-3.5 w-3.5" />
                    Número NFe
                  </span>
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <span className="flex items-center gap-2">
                    <ShoppingCart className="h-3.5 w-3.5" />
                    Fornecedor
                  </span>
                </th>
                <th className="px-5 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Data Emissão
                </th>
                <th className="px-5 py-3.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Valor Total
                </th>
                <th className="px-5 py-3.5 text-center text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-5 py-3.5 text-center text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {extractions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center">
                    <div className="flex flex-col items-center gap-3 text-slate-500">
                      <FileText className="h-12 w-12 opacity-30" />
                      <p className="text-lg">Nenhuma NFe importada</p>
                      <p className="text-sm">Faça upload do primeiro XML para começar</p>
                    </div>
                  </td>
                </tr>
              ) : (
                extractions.map((extraction) => (
                  <tr key={extraction.id} className="hover:bg-white/2.5 transition-colors">
                    <td className="px-5 py-4">
                      <span className="font-mono text-slate-100">{extraction.invoice_number}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-slate-300">{extraction.supplier_name || "Não identificado"}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-slate-400 font-mono">{formatDate(extraction.issue_date)}</span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <span className="font-mono tabular-nums text-slate-100 font-medium">{formatCurrency(extraction.total_amount || 0)}</span>
                    </td>
                    <td className="px-5 py-4 text-center">
                      {getStatusBadge(extraction.status)}
                    </td>
                    <td className="px-5 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {extraction.status === "READY_FOR_APPROVAL" && (
                          <button
                            onClick={() => handleApprove(extraction.id)}
                            disabled={approvingId === extraction.id}
                            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-950
                              bg-gradient-to-r from-[#10b981] to-[#059669]
                              hover:from-[#059669] hover:to-[#047857]
                              active:scale-[0.98] transition-all duration-200
                              shadow-[0_4px_14px_rgba(16,185,129,0.3)]
                              disabled:opacity-50 disabled:cursor-not-allowed
                              flex items-center gap-1.5"
                          >
                            {approvingId === extraction.id ? (
                              <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                              <CheckCircle className="h-3.5 w-3.5" />
                            )}
                            Aprovar
                          </button>
                        )}
                        {extraction.status === "NEEDS_REVIEW" && (
                          <button
                            className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-100
                              bg-gradient-to-r from-[#a855f7] to-[#9333ea]
                              hover:from-[#9333ea] hover:to-[#7e22ce]
                              active:scale-[0.98] transition-all duration-200
                              shadow-[0_4px_14px_rgba(168,85,247,0.3)]
                              flex items-center gap-1.5"
                          >
                            <Eye className="h-3.5 w-3.5" />
                            Revisar
                          </button>
                        )}
                        {extraction.status === "APPROVED" && (
                          <Badge variant="emerald" className="text-xs">
                            <CheckCircle className="h-3 w-3 mr-1" /> Aprovado
                          </Badge>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {extractions.length > 0 && (
          <div className="px-5 py-3 border-t border-white/5 bg-slate-950/30">
            <p className="text-xs text-slate-500 text-right">
              Exibindo {extractions.length} documento{extractions.length !== 1 ? "s" : ""}
            </p>
          </div>
        )}
      </GlassPanel>
    </div>
  )
}