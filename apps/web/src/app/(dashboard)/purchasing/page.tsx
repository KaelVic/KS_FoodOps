import { GlassPanel } from "@/components/ui/glass-panel"
import { Badge } from "@/components/ui/badge"
import {
  ShoppingCart,
  Upload,
  FileText,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  Loader2,
  XCircle,
} from "lucide-react"
import { fetchExtractionsServer } from "@/lib/api-server"
import PurchasingClient from "./PurchasingClient"

export const dynamic = "force-dynamic"

async function getExtractions() {
  return await fetchExtractionsServer()
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

export default async function PurchasingPage() {
  const extractions = await getExtractions()

  const totalImported = extractions.length
  const totalValue = extractions.reduce((sum, e) => sum + (e.total_amount || 0), 0)
  const pendingApproval = extractions.filter(
    (e) => e.status === "NEEDS_REVIEW" || e.status === "READY_FOR_APPROVAL"
  ).length

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-100 flex items-center gap-3">
            <ShoppingCart className="h-8 w-8 text-[#00f0ff]" />
            Compras & Ingestão de NFe
          </h2>
          <p className="text-slate-400 mt-1">Upload de NFes XML, conciliação 3-way e aprovação de documentos fiscais.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <GlassPanel accent="cyan" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="h-5 w-5 text-[#00f0ff]" />
            <span className="text-slate-400 text-sm font-medium">Total de NFes Importadas</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{totalImported}</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="violet" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="h-5 w-5 text-[#a855f7]" />
            <span className="text-slate-400 text-sm font-medium">Volume Financeiro Processado</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{formatCurrency(totalValue)}</span>
          </div>
        </GlassPanel>

        <GlassPanel accent="amber" className="p-5 flex flex-col">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="h-5 w-5 text-[#f59e0b]" />
            <span className="text-slate-400 text-sm font-medium">Pendentes de Aprovação</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-slate-100 tabular-nums">{pendingApproval}</span>
          </div>
        </GlassPanel>
      </div>

      <PurchasingClient initialExtractions={extractions} />
    </div>
  )
}