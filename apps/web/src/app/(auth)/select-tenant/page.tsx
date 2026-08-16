import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { selectTenantAction } from "../actions"

export default async function SelectTenantPage() {
  const cookieStore = await cookies()
  const availableTenantsStr = cookieStore.get("available_tenants")?.value
  
  if (!availableTenantsStr) {
    redirect("/login")
  }

  let tenants = []
  try {
    tenants = JSON.parse(availableTenantsStr)
  } catch (e) {
    redirect("/login")
  }

  if (tenants.length === 0) {
    redirect("/login")
  }

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-slate-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(120,119,198,0.3),rgba(255,255,255,0))]">
      <div className="w-full max-w-md overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-8 shadow-2xl backdrop-blur-xl">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
            <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Selecionar Restaurante</h1>
          <p className="mt-2 text-sm text-slate-400">Escolha o ambiente para continuar</p>
        </div>

        <div className="space-y-3">
          {tenants.map((tenant: any) => (
            <form key={tenant.id} action={selectTenantAction}>
              <input type="hidden" name="tenant_id" value={tenant.id} />
              <button 
                type="submit"
                className="group flex w-full items-center justify-between rounded-xl border border-slate-700 bg-slate-800/50 p-4 transition-all hover:border-indigo-500 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <div className="flex flex-col items-start">
                  <span className="font-semibold text-white group-hover:text-indigo-400 transition-colors">{tenant.name}</span>
                  <span className="mt-1 text-xs font-medium uppercase tracking-wider text-slate-500">
                    Role: <span className="text-slate-300">{tenant.role}</span>
                  </span>
                </div>
                <svg className="h-5 w-5 text-slate-600 group-hover:text-indigo-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </form>
          ))}
        </div>
      </div>
    </div>
  )
}
