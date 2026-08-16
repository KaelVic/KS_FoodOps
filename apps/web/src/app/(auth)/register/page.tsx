"use client"

import { useActionState } from "react"
import { registerAction } from "../actions"
import Link from "next/link"

const initialState = {
  error: null as string | null,
}

export default function RegisterPage() {
  const [state, formAction, isPending] = useActionState(registerAction, initialState)

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-slate-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.3),rgba(255,255,255,0))] p-4">
      <div className="w-full max-w-md overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-8 shadow-2xl backdrop-blur-xl">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
            <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Criar Conta</h1>
          <p className="mt-2 text-sm text-slate-400">Cadastre-se no KS FoodOps para gerenciar seu restaurante</p>
        </div>

        <form action={formAction} className="space-y-4">
          {state?.error && (
            <div className="animate-in fade-in slide-in-from-top-2 rounded-lg bg-red-500/10 p-3 text-sm text-red-400 border border-red-500/20 text-center">
              {state.error}
            </div>
          )}

          <div>
            <label className="text-sm font-medium text-slate-300">Nome Completo</label>
            <div className="relative mt-1">
              <input 
                type="text" 
                name="full_name" 
                required 
                className="block w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2.5 px-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors" 
                placeholder="Ex: Carlos Silva"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">Nome do Restaurante / Estabelecimento</label>
            <div className="relative mt-1">
              <input 
                type="text" 
                name="restaurant_name" 
                required 
                className="block w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2.5 px-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors" 
                placeholder="Ex: Hamburgueria Gourmet"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">Email de Acesso</label>
            <div className="relative mt-1">
              <input 
                type="email" 
                name="email" 
                required 
                className="block w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2.5 px-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors" 
                placeholder="carlos@exemplo.com"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-300">Senha</label>
            <div className="relative mt-1">
              <input 
                type="password" 
                name="password" 
                required 
                className="block w-full rounded-lg border border-slate-700 bg-slate-800/50 py-2.5 px-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-colors" 
                placeholder="••••••••"
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isPending}
            className="w-full mt-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all hover:from-indigo-400 hover:to-purple-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? "Criando conta..." : "Criar Minha Conta"}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-slate-400">
          Já possui cadastro?{" "}
          <Link href="/login" className="font-medium text-indigo-400 hover:text-indigo-300 underline underline-offset-4">
            Entrar aqui
          </Link>
        </div>

        <div className="mt-6 text-center text-xs text-slate-500">
          &copy; 2026 KS FoodOps. Todos os direitos reservados.
        </div>
      </div>
    </div>
  )
}
