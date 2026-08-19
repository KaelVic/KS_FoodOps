import { NextRequest, NextResponse } from "next/server"

const API_BACKEND_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function getAuthHeaders(request: NextRequest): Promise<Headers> {
  const cookieStore = request.cookies
  const token = cookieStore.get("session_token")?.value
  const tenantId = cookieStore.get("active_tenant_id")?.value

  const headers = new Headers()
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }
  if (tenantId) {
    headers.set("X-Tenant-ID", tenantId)
  }
  return headers
}

async function proxyRequest(
  request: NextRequest,
  method: string,
  path: string
): Promise<NextResponse> {
  const authHeaders = await getAuthHeaders(request)
  
  const contentType = request.headers.get("content-type")
  if (contentType) {
    authHeaders.set("Content-Type", contentType)
  }

  const backendUrl = `${API_BACKEND_URL}${path}`

  let body: string | FormData | null = null
  if (method !== "GET" && method !== "HEAD") {
    const contentTypeHeader = request.headers.get("content-type") || ""
    if (contentTypeHeader.includes("multipart/form-data")) {
      body = await request.formData()
    } else {
      body = await request.text()
    }
  }

  const response = await fetch(backendUrl, {
    method,
    headers: authHeaders,
    body,
    cache: "no-store",
  })

  const responseHeaders = new Headers()
  response.headers.forEach((value, key) => {
    if (!key.toLowerCase().startsWith("set-cookie")) {
      responseHeaders.set(key, value)
    }
  })

  const responseBody = await response.arrayBuffer()
  return new NextResponse(responseBody, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  })
}

export async function GET(request: NextRequest) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace(/^\/api/, "") || "/"
  return proxyRequest(request, "GET", path)
}

export async function POST(request: NextRequest) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace(/^\/api/, "") || "/"
  return proxyRequest(request, "POST", path)
}

export async function PUT(request: NextRequest) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace(/^\/api/, "") || "/"
  return proxyRequest(request, "PUT", path)
}

export async function PATCH(request: NextRequest) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace(/^\/api/, "") || "/"
  return proxyRequest(request, "PATCH", path)
}

export async function DELETE(request: NextRequest) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace(/^\/api/, "") || "/"
  return proxyRequest(request, "DELETE", path)
}

export async function HEAD(request: NextRequest) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace(/^\/api/, "") || "/"
  return proxyRequest(request, "HEAD", path)
}

export async function OPTIONS(request: NextRequest) {
  const { pathname } = new URL(request.url)
  const path = pathname.replace(/^\/api/, "") || "/"
  return proxyRequest(request, "OPTIONS", path)
}