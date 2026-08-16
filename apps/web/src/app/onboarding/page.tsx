"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { submitOnboardingClient } from "@/lib/api-client"

export default function OnboardingWizard() {
  const router = useRouter()
  const [restaurantName, setRestaurantName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const res = await submitOnboardingClient(restaurantName)

      if (!res.success) {
        throw new Error(res.error || "Falha ao criar restaurante")
      }

      // Redireciona para o painel principal
      router.push("/inventory")
      
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 text-zinc-100">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md p-10">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-white">
            Bem-vindo ao KS FoodOps
          </h2>
          <p className="mt-2 text-center text-sm text-zinc-400">
            Vamos configurar o seu restaurante para começar.
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4 rounded-md shadow-sm">
            <div>
              <label htmlFor="restaurant-name" className="block text-sm font-medium text-zinc-300">
                Nome do Restaurante
              </label>
              <input
                id="restaurant-name"
                name="restaurantName"
                type="text"
                required
                className="mt-1 block w-full rounded-md border border-white/10 bg-black/50 px-3 py-2 text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
                placeholder="Ex: Cantina Italiana"
                value={restaurantName}
                onChange={(e) => setRestaurantName(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="text-red-500 text-sm font-medium text-center">
              {error}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative flex w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-black disabled:opacity-50"
            >
              {loading ? "Criando..." : "Criar Meu Restaurante"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
