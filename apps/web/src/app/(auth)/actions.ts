"use server"

import { redirect } from "next/navigation"
import { cookies } from "next/headers"
import { clearSession, setSessionCookies } from "@/lib/session"

const API_URL = process.env.API_URL ?? "http://localhost:8000"

export async function loginAction(prevState: any, formData: FormData) {
  const email = formData.get("email") as string
  const password = formData.get("password") as string

  if (!email || !password) {
    return { error: "Email and password are required" }
  }

  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })

    if (!response.ok) {
      return { error: "Credenciais inválidas" }
    }

    const data = await response.json()
    const tenants = data.tenants || []

    if (tenants.length === 0) {
      return { error: "Usuário não possui acesso a nenhum tenant" }
    }

    if (tenants.length === 1) {
      await setSessionCookies(data.access_token, tenants[0].id)
      redirect("/inventory")
    } else {
      await setSessionCookies(data.access_token) // Just token
      const cookieStore = await cookies()
      cookieStore.set("available_tenants", JSON.stringify(tenants), {
        httpOnly: true,
        path: "/",
      })
      redirect("/select-tenant")
    }
  } catch (err: any) {
    // If it's a redirect, we must throw it so Next.js can handle it
    if (err.message === "NEXT_REDIRECT") throw err;
    return { error: "Falha ao conectar no servidor" }
  }
}

export async function registerAction(prevState: any, formData: FormData) {
  const email = formData.get("email") as string
  const password = formData.get("password") as string
  const fullName = formData.get("full_name") as string
  const restaurantName = formData.get("restaurant_name") as string

  if (!email || !password || !fullName) {
    return { error: "Todos os campos obrigatórios devem ser preenchidos." }
  }

  try {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        email, 
        password, 
        full_name: fullName,
        restaurant_name: restaurantName || "Meu Restaurante"
      }),
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      return { error: errData.detail || "Erro ao criar conta." }
    }

    const data = await response.json()
    const tenants = data.tenants || []

    if (tenants.length > 0) {
      await setSessionCookies(data.access_token, tenants[0].id)
      redirect("/")
    } else {
      await setSessionCookies(data.access_token)
      redirect("/onboarding")
    }
  } catch (err: any) {
    if (err.message === "NEXT_REDIRECT") throw err;
    return { error: "Falha ao conectar no servidor" }
  }
}

export async function selectTenantAction(formData: FormData) {
  const tenantId = formData.get("tenant_id") as string
  if (tenantId) {
    const cookieStore = await cookies()
    const isProd = process.env.NODE_ENV === "production"
    cookieStore.set("active_tenant_id", tenantId, {
      httpOnly: true,
      secure: isProd,
      sameSite: "lax",
      path: "/",
      maxAge: 8 * 60 * 60
    })
    cookieStore.delete("available_tenants")
    redirect("/inventory")
  }
}

export async function logoutAction() {
  await clearSession()
  redirect("/login")
}
