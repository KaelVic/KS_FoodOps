import { redirect } from "next/navigation"
import { getSession, getActiveTenantId } from "@/lib/session"
import { Sidebar } from "@/components/layout/sidebar"
import { Header } from "@/components/layout/header"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getSession()
  if (!session) {
    redirect("/login")
  }

  const tenantId = await getActiveTenantId()
  if (!tenantId) {
    redirect("/select-tenant")
  }

  // Tenant display fallback
  const tenantName = tenantId ? `Tenant ${tenantId.slice(0, 8)}` : undefined

  return (
    <div className="flex h-screen w-full bg-[#030712] text-slate-50 overflow-hidden relative selection:bg-[rgba(0,240,255,0.3)] selection:text-white">
      {/* Background Cyber Mesh */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none" style={{
        backgroundImage: `
          linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px'
      }} />

      {/* Holographic Sidebar */}
      <Sidebar email={session.email} />

      <div className="flex-1 flex flex-col relative z-10 overflow-hidden">
        {/* Top HUD Header */}
        <Header tenantName={tenantName} />

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto p-8 relative">
          {children}
        </main>
      </div>
    </div>
  )
}
