"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { 
  Clock, Play, Square, CheckCircle2, AlertCircle, 
  Calendar, User, Building2, Coffee 
} from "lucide-react"
import { TeamNavigation } from "../TeamClient"
import { clockInClient, clockOutClient } from "@/lib/api-client"

interface TimeClockClientProps {
  initialEntries: any[]
  employees: any[]
  locations: any[]
}

export function TimeClockClient({ initialEntries, employees, locations }: TimeClockClientProps) {
  const router = useRouter()
  const [entries, setEntries] = React.useState<any[]>(initialEntries)

  // Clock in/out form
  const [employeeId, setEmployeeId] = React.useState(employees[0]?.id || "")
  const [locationId, setLocationId] = React.useState(locations[0]?.id || "")
  const [breakMinutes, setBreakMinutes] = React.useState("0")
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [message, setMessage] = React.useState<{ type: "success" | "error"; text: string } | null>(null)

  const handleClockIn = async () => {
    if (!employeeId || !locationId) {
      setMessage({ type: "error", text: "Selecione o colaborador e o local." })
      return
    }

    setIsSubmitting(true)
    setMessage(null)

    try {
      await clockInClient({
        employee_id: employeeId,
        location_id: locationId
      })
      setMessage({ type: "success", text: "Entrada registrada com sucesso!" })
      router.refresh()
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Erro ao registrar entrada." })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClockOut = async () => {
    if (!employeeId) {
      setMessage({ type: "error", text: "Selecione o colaborador." })
      return
    }

    setIsSubmitting(true)
    setMessage(null)

    try {
      await clockOutClient({
        employee_id: employeeId,
        break_minutes: parseInt(breakMinutes) || 0
      })
      setMessage({ type: "success", text: "Saída registrada e horas calculadas com sucesso!" })
      router.refresh()
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Erro ao registrar saída." })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono tracking-widest text-[#00f0ff] uppercase bg-[#00f0ff]/10 px-2 py-0.5 rounded border border-[#00f0ff]/20">
              DIGITAL TIME CLOCK
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 flex items-center gap-3">
            <Clock className="w-8 h-8 text-[#00f0ff]" />
            Terminal de Ponto Digital
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Registro de jornadas, pausas, cálculo de horas trabalhadas e base para o rateio de gorjetas.
          </p>
        </div>
      </div>

      <TeamNavigation />

      {/* Clock Terminal Card */}
      <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-xl space-y-4">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Clock className="w-4 h-4 text-[#00f0ff]" />
          Terminal de Bater Ponto
        </h2>

        {message && (
          <div className={`p-3.5 rounded-xl border text-xs flex items-center gap-2 ${
            message.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-rose-500/10 border-rose-500/30 text-rose-300"
          }`}>
            {message.type === "success" ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertCircle className="w-4 h-4 text-rose-400" />}
            {message.text}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Colaborador *</label>
            <select
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
            >
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.name} — {emp.role_title} ({emp.department})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Local / Unidade *</label>
            <select
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
            >
              {locations.map((loc) => (
                <option key={loc.id} value={loc.id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Intervalo / Almoço (Minutos)</label>
            <input
              type="number"
              value={breakMinutes}
              onChange={(e) => setBreakMinutes(e.target.value)}
              placeholder="0"
              className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
            />
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={handleClockIn}
            disabled={isSubmitting}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 hover:opacity-95 transition-all inline-flex items-center gap-2 disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-slate-950" />
            Entrada (Clock In)
          </button>

          <button
            onClick={handleClockOut}
            disabled={isSubmitting}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-rose-500 text-slate-950 font-bold text-xs shadow-lg shadow-amber-500/20 hover:opacity-95 transition-all inline-flex items-center gap-2 disabled:opacity-50"
          >
            <Square className="w-4 h-4 fill-slate-950" />
            Saída (Clock Out)
          </button>
        </div>
      </div>

      {/* Entries Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/80 font-mono text-slate-400 uppercase">
                <th className="p-4">Colaborador</th>
                <th className="p-4">Função / Praça</th>
                <th className="p-4">Entrada</th>
                <th className="p-4">Saída</th>
                <th className="p-4">Intervalo</th>
                <th className="p-4">Total de Horas</th>
                <th className="p-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {entries.map((ent) => (
                <tr key={ent.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 font-bold text-slate-100">{ent.employee_name}</td>
                  <td className="p-4 text-slate-300">{ent.role_title} ({ent.department})</td>
                  <td className="p-4 font-mono text-[#00f0ff]">
                    {new Date(ent.clock_in).toLocaleString("pt-BR")}
                  </td>
                  <td className="p-4 font-mono text-slate-300">
                    {ent.clock_out ? new Date(ent.clock_out).toLocaleString("pt-BR") : "-"}
                  </td>
                  <td className="p-4 font-mono text-slate-400">{ent.break_minutes} min</td>
                  <td className="p-4 font-mono font-bold text-emerald-400">
                    {Number(ent.total_hours).toFixed(2)}h
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                      ent.status === "APPROVED"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                        : "bg-blue-500/10 text-blue-400 border-blue-500/30"
                    }`}>
                      {ent.status}
                    </span>
                  </td>
                </tr>
              ))}
              {entries.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    Nenhum registro de ponto encontrado.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
