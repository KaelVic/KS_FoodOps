"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { 
  Users, Plus, Search, Filter, Calendar, Clock, DollarSign, 
  Sparkles, TrendingUp, ShieldCheck, Mail, Phone, ChefHat, 
  Wine, Store, Briefcase, Check, AlertCircle, X
} from "lucide-react"
import { createEmployeeClient, updateEmployeeClient } from "@/lib/api-client"

interface TeamClientProps {
  initialEmployees: any[]
}

export function TeamNavigation() {
  const pathname = usePathname()

  const tabs = [
    { name: "Colaboradores", href: "/team", icon: Users },
    { name: "Escalas & Turnos", href: "/team/shifts", icon: Calendar },
    { name: "Ponto Digital", href: "/team/time-clock", icon: Clock },
    { name: "Rateio de Gorjetas (Lei 13.419)", href: "/team/tips", icon: DollarSign },
    { name: "Prime Cost (CMV + CMO)", href: "/team/prime-cost", icon: TrendingUp },
  ]

  return (
    <div className="flex items-center gap-2 border-b border-slate-800 pb-2 overflow-x-auto">
      {tabs.map((t) => {
        const isActive = pathname === t.href
        const Icon = t.icon
        return (
          <Link
            key={t.href}
            href={t.href}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 flex-shrink-0 ${
              isActive
                ? "bg-[#00f0ff]/10 text-[#00f0ff] border border-[#00f0ff]/30 shadow-[0_0_12px_rgba(0,240,255,0.15)]"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {t.name}
          </Link>
        )
      })}
    </div>
  )
}

export function TeamClient({ initialEmployees }: TeamClientProps) {
  const router = useRouter()
  const [employees, setEmployees] = React.useState<any[]>(initialEmployees)
  const [search, setSearch] = React.useState("")
  const [deptFilter, setDeptFilter] = React.useState("ALL")

  // Modal State
  const [isModalOpen, setIsModalOpen] = React.useState(false)
  const [editingEmployee, setEditingEmployee] = React.useState<any | null>(null)
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null)

  // Form State
  const [name, setName] = React.useState("")
  const [email, setEmail] = React.useState("")
  const [phone, setPhone] = React.useState("")
  const [roleTitle, setRoleTitle] = React.useState("")
  const [department, setDepartment] = React.useState("FLOOR")
  const [monthlySalary, setMonthlySalary] = React.useState("0.00")
  const [hourlyRate, setHourlyRate] = React.useState("0.00")
  const [tipPoints, setTipPoints] = React.useState("1.00")

  const openCreateModal = () => {
    setEditingEmployee(null)
    setName("")
    setEmail("")
    setPhone("")
    setRoleTitle("")
    setDepartment("FLOOR")
    setMonthlySalary("0.00")
    setHourlyRate("0.00")
    setTipPoints("1.00")
    setErrorMsg(null)
    setIsModalOpen(true)
  }

  const openEditModal = (emp: any) => {
    setEditingEmployee(emp)
    setName(emp.name)
    setEmail(emp.email || "")
    setPhone(emp.phone || "")
    setRoleTitle(emp.role_title)
    setDepartment(emp.department)
    setMonthlySalary(String(emp.monthly_salary))
    setHourlyRate(String(emp.hourly_rate))
    setTipPoints(String(emp.tip_points))
    setErrorMsg(null)
    setIsModalOpen(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setErrorMsg(null)

    try {
      const payload = {
        name,
        email: email || null,
        phone: phone || null,
        role_title: roleTitle,
        department,
        monthly_salary: parseFloat(monthlySalary) || 0,
        hourly_rate: parseFloat(hourlyRate) || 0,
        tip_points: parseFloat(tipPoints) || 1,
        is_active: true
      }

      if (editingEmployee) {
        const updated = await updateEmployeeClient(editingEmployee.id, payload)
        setEmployees(prev => prev.map(e => e.id === updated.id ? updated : e))
      } else {
        const created = await createEmployeeClient(payload)
        setEmployees(prev => [...prev, created])
      }

      setIsModalOpen(false)
      router.refresh()
    } catch (err: any) {
      setErrorMsg(err.message || "Erro ao salvar colaborador.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const filteredEmployees = employees.filter(e => {
    const matchesSearch = e.name.toLowerCase().includes(search.toLowerCase()) ||
      e.role_title.toLowerCase().includes(search.toLowerCase())
    const matchesDept = deptFilter === "ALL" || e.department === deptFilter
    return matchesSearch && matchesDept
  })

  const totalFixedPayroll = employees.reduce((acc, e) => acc + (parseFloat(e.monthly_salary) || 0), 0)

  const getDepartmentBadge = (dept: string) => {
    switch (dept) {
      case "FLOOR":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30"><Store className="w-3 h-3" /> Salão</span>
      case "KITCHEN":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30"><ChefHat className="w-3 h-3" /> Cozinha</span>
      case "BAR":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30"><Wine className="w-3 h-3" /> Bar</span>
      case "ADMIN":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"><Briefcase className="w-3 h-3" /> Admin</span>
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">{dept}</span>
    }
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-mono tracking-widest text-[#00f0ff] uppercase bg-[#00f0ff]/10 px-2 py-0.5 rounded border border-[#00f0ff]/20">
              OPERATIONAL HR & LABOR
            </span>
            <span className="text-[11px] font-mono tracking-widest text-emerald-400 uppercase bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              FASE 8 ERP
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-100 flex items-center gap-3">
            <Users className="w-8 h-8 text-[#00f0ff]" />
            Recursos Humanos & Equipe Operacional
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Controle de cargos, salários, escalas de turnos, ponto digital e apuração de Custo de Mão de Obra (CMO).
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#00f0ff] to-[#3b82f6] text-slate-950 font-semibold shadow-lg shadow-[#00f0ff]/20 hover:opacity-95 transition-all text-sm"
        >
          <Plus className="w-4 h-4" />
          Novo Colaborador
        </button>
      </div>

      {/* Sub Navigation */}
      <TeamNavigation />

      {/* Highlights / KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">TOTAL COLABORADORES</span>
            <Users className="w-4 h-4 text-slate-500" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2">{employees.length}</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-blue-400">FOLHA FIXA MENSAL</span>
            <DollarSign className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-blue-300 mt-2">
            R$ {totalFixedPayroll.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-amber-400">PRAÇAS ATIVAS</span>
            <Store className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-amber-300 mt-2">4 Praças</p>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-emerald-400">PONTOS DE GORJETA</span>
            <Sparkles className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-300 mt-2">
            {employees.reduce((acc, e) => acc + (parseFloat(e.tip_points) || 0), 0).toFixed(1)} pts
          </p>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/40 border border-slate-800/80">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Buscar por nome ou cargo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950/60 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#00f0ff]/50"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <Filter className="w-4 h-4 text-slate-500 flex-shrink-0" />
          {["ALL", "FLOOR", "KITCHEN", "BAR", "ADMIN"].map((dept) => (
            <button
              key={dept}
              onClick={() => setDeptFilter(dept)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex-shrink-0 ${
                deptFilter === dept
                  ? "bg-[#00f0ff]/20 text-[#00f0ff] border border-[#00f0ff]/40"
                  : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {dept === "ALL" ? "Todos os Departamentos" : dept}
            </button>
          ))}
        </div>
      </div>

      {/* Employees Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/80 font-mono text-slate-400 uppercase">
                <th className="p-4">Colaborador</th>
                <th className="p-4">Cargo / Função</th>
                <th className="p-4">Departamento</th>
                <th className="p-4">Salário Fixo</th>
                <th className="p-4">Valor / Hora</th>
                <th className="p-4">Pontos Gorjeta</th>
                <th className="p-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredEmployees.map((emp) => (
                <tr key={emp.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-4">
                    <div className="font-bold text-slate-100">{emp.name}</div>
                    {emp.email && <div className="text-[10px] text-slate-500">{emp.email}</div>}
                  </td>
                  <td className="p-4 font-medium text-slate-300">{emp.role_title}</td>
                  <td className="p-4">{getDepartmentBadge(emp.department)}</td>
                  <td className="p-4 font-mono text-slate-200">
                    R$ {Number(emp.monthly_salary).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-4 font-mono text-slate-400">
                    R$ {Number(emp.hourly_rate).toFixed(2)}
                  </td>
                  <td className="p-4 font-mono font-bold text-[#00f0ff]">
                    {Number(emp.tip_points).toFixed(1)} pts
                  </td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => openEditModal(emp)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-all"
                    >
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
              {filteredEmployees.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    Nenhum colaborador encontrado.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Create / Edit */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Users className="w-4 h-4 text-[#00f0ff]" />
                {editingEmployee ? "Editar Colaborador" : "Novo Colaborador"}
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
                <label className="block text-xs font-medium text-slate-300 mb-1">Nome Completo *</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Carlos Alberto Silva"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">E-mail</label>
                  <input
                    type="email"
                    placeholder="carlos@restaurante.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Telefone / WhatsApp</label>
                  <input
                    type="text"
                    placeholder="11999998888"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Cargo / Função *</label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: Garçom, Cozinheiro, Barman"
                    value={roleTitle}
                    onChange={(e) => setRoleTitle(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Departamento *</label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  >
                    <option value="FLOOR">Salão (Floor)</option>
                    <option value="KITCHEN">Cozinha (Kitchen)</option>
                    <option value="BAR">Bar</option>
                    <option value="ADMIN">Administrativo</option>
                    <option value="DELIVERY">Delivery / Expedição</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Salário Fixo (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={monthlySalary}
                    onChange={(e) => setMonthlySalary(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Valor / Hora (R$)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={hourlyRate}
                    onChange={(e) => setHourlyRate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Pontos Gorjeta</label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="1.0"
                    value={tipPoints}
                    onChange={(e) => setTipPoints(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-[#00f0ff]"
                  />
                </div>
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
                  {isSubmitting ? "Salvando..." : "Salvar Colaborador"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
