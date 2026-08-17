"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { 
  Calendar, Plus, Clock, User, Building2, Store, 
  ChefHat, Wine, Briefcase, CheckCircle2, AlertCircle, X 
} from "lucide-react"
import { TeamNavigation } from "../TeamClient"
import { createShiftClient } from "@/lib/api-client"

interface ShiftsClientProps {
  initialShifts: any[]
  employees: any[]
  locations: any[]
}

export function ShiftsClient({ initialShifts, employees, locations }: ShiftsClientProps) {
  const router = useRouter()
  const [shifts, setShifts] = React.useState<any[]>(initialShifts)
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)

  // Form State
  const [employeeId, setEmployeeId] = React.useState(employees[0]?.id || "")
  const [locationId, setLocationId] = React.useState(locations[0]?.id || "")
  const [shiftDate, setShiftDate] = React.useState(new Date().toISOString().split("T")[0])
  const [startTime, setStartTime] = React.useState("17:00")
  const [endTime, setEndTime] = React.useState("23:30")
  const [notes, setNotes] = React.useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!employeeId || !locationId || !shiftDate || !startTime || !endTime) {
      setErrorMsg("Preencha todos os campos obrigatórios.")
      return
    }

    setIsSubmitting(true)
    setErrorMsg(null)

    try {
      const startDateTime = `${shiftDate}T${startTime}:00Z`
      const endDateTime = `${shiftDate}T${endTime}:00Z`

      await createShiftClient({
        employee_id: employeeId,
        location_id: locationId,
        shift_date: shiftDate,
        start_time: startDateTime,
        end_time: endDateTime,
        notes: notes || null
      })

      setIsModalOpen(false)
      router.refresh()
    } catch (err: any) {
      setErrorMsg(err.message || "Erro ao criar turno.")
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
              ROSTER & SCHEDULING
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 flex items-center gap-3">
            <Calendar className="w-8 h-8 text-[#00f0ff]" />
            Escalas & Turnos de Trabalho
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Planejamento de jornadas por praça (Salão, Cozinha, Bar, Delivery) e controle de presença.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-semibold shadow-lg shadow-[#00f0ff]/20 hover:opacity-95 transition-all text-sm"
        >
          <Plus className="w-4 h-4" />
          Agendar Turno
        </button>
      </div>

      <TeamNavigation />

      {/* Shifts Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/80 font-mono text-slate-400 uppercase">
                <th className="p-4">Data do Turno</th>
                <th className="p-4">Colaborador</th>
                <th className="p-4">Função / Praça</th>
                <th className="p-4">Horário de Início</th>
                <th className="p-4">Horário de Término</th>
                <th className="p-4">Status</th>
                <th className="p-4">Observações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {shifts.map((s) => (
                <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4 font-mono font-bold text-[#00f0ff]">
                    {new Date(s.shift_date + "T00:00:00").toLocaleDateString("pt-BR")}
                  </td>
                  <td className="p-4 font-bold text-slate-100">{s.employee_name}</td>
                  <td className="p-4 text-slate-300">{s.role_title} ({s.department})</td>
                  <td className="p-4 font-mono text-slate-300">
                    {new Date(s.start_time).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td className="p-4 font-mono text-slate-300">
                    {new Date(s.end_time).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td className="p-4">
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                      <Clock className="w-3 h-3" /> {s.status}
                    </span>
                  </td>
                  <td className="p-4 text-slate-400 max-w-xs truncate">{s.notes || "-"}</td>
                </tr>
              ))}
              {shifts.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    Nenhum turno agendado para o período.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Schedule Shift */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-[#00f0ff]" />
                Agendar Novo Turno
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 text-slate-500 hover:text-slate-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {errorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-rose-400" />
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Colaborador *</label>
                <select
                  required
                  value={employeeId}
                  onChange={(e) => setEmployeeId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                >
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.name} — {emp.role_title} ({emp.department})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Local / Praça *</label>
                <select
                  required
                  value={locationId}
                  onChange={(e) => setLocationId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                >
                  {locations.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Data do Turno *</label>
                <input
                  type="date"
                  required
                  value={shiftDate}
                  onChange={(e) => setShiftDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Início *</label>
                  <input
                    type="time"
                    required
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Término *</label>
                  <input
                    type="time"
                    required
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Observações</label>
                <input
                  type="text"
                  placeholder="Ex: Turno de abertura, evento especial"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-lg bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-bold text-xs shadow-lg shadow-[#00f0ff]/20 hover:opacity-95 transition-all disabled:opacity-50"
                >
                  {isSubmitting ? "Agendando..." : "Confirmar Escala"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
