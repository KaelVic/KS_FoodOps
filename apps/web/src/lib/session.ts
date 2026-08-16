import { cookies } from "next/headers"

export interface SessionPayload {
  sub: string
  email: string
  exp: number
}

export async function getSession(): Promise<SessionPayload | null> {
  const cookieStore = await cookies()
  const token = cookieStore.get("session_token")?.value
  if (!token) return null

  try {
    // Note: We only decode the JWT here for UI purposes.
    // The actual validation happens in the FastAPI backend.
    const parts = token.split(".")
    if (parts.length !== 3) return null
    
    const payloadStr = atob(parts[1])
    return JSON.parse(payloadStr) as SessionPayload
  } catch (e) {
    return null
  }
}

export async function getActiveTenantId(): Promise<string | null> {
  const cookieStore = await cookies()
  return cookieStore.get("active_tenant_id")?.value ?? null
}

export async function setSessionCookies(token: string, tenantId?: string) {
  const cookieStore = await cookies()
  const isProd = process.env.NODE_ENV === "production"
  
  cookieStore.set("session_token", token, {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax",
    path: "/",
    maxAge: 8 * 60 * 60 // 8 hours
  })

  if (tenantId) {
    cookieStore.set("active_tenant_id", tenantId, {
      httpOnly: true,
      secure: isProd,
      sameSite: "lax",
      path: "/",
      maxAge: 8 * 60 * 60
    })
  }
}

export async function clearSession() {
  const cookieStore = await cookies()
  cookieStore.delete("session_token")
  cookieStore.delete("active_tenant_id")
  cookieStore.delete("available_tenants") // Temporary cookie for selection
}
