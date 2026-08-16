import os
import uuid
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from packages.tenant.database import async_session_maker
from packages.observability.logging import setup_logging, request_id_ctx_var, tenant_id_ctx_var
from packages.observability.telemetry import setup_telemetry

# Setup JSON structured logging
setup_logging()

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup OpenTelemetry
    setup_telemetry(app)
    yield
    # Shutdown logic

is_production = os.environ.get("ENVIRONMENT") == "production"
docs_url = None if is_production else "/docs"
redoc_url = None if is_production else "/redoc"

app = FastAPI(
    title="KS FoodOps API",
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Setup request ID
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_ctx_var.set(req_id)
    
    response: Response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Request-ID"] = req_id
    return response

@app.get("/health")
@app.get("/health/live")
@limiter.limit("10/minute")
async def health_check(request: Request):
    return {"status": "healthy"}

@app.get("/readiness")
@app.get("/health/ready")
@limiter.limit("10/minute")
async def readiness_check(request: Request):
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    # Ideally add Redis check here too using a redis async client
    
    return {"status": "ready"}
from apps.api.routers.auth import router as auth_router
from apps.api.routers.inventory import router as inventory_router
from apps.api.routers import (
    auth, documents, pos_integrations, 
    purchasing, inventory, inventory_sessions, recipes, sales, intelligence,
    catalog, suppliers, locations, team, notifications, onboarding, reports
)
from packages.security.dependencies import get_current_user

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"], dependencies=[Depends(get_current_user)])
app.include_router(inventory_sessions.router, dependencies=[Depends(get_current_user)])
app.include_router(documents.router, prefix="/documents", tags=["Documents"], dependencies=[Depends(get_current_user)])
app.include_router(recipes.router, prefix="/recipes", tags=["Recipes"], dependencies=[Depends(get_current_user)])
app.include_router(purchasing.router, dependencies=[Depends(get_current_user)])
app.include_router(sales.router, prefix="/sales", tags=["Sales"], dependencies=[Depends(get_current_user)])
app.include_router(intelligence.router, prefix="/intelligence", tags=["Intelligence"], dependencies=[Depends(get_current_user)])
app.include_router(pos_integrations.router, prefix="/integrations", tags=["POS Integrations"])
app.include_router(catalog.router, prefix="/catalog", tags=["Catalog"], dependencies=[Depends(get_current_user)])
app.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"], dependencies=[Depends(get_current_user)])
app.include_router(locations.router, prefix="/locations", tags=["Locations"], dependencies=[Depends(get_current_user)])
app.include_router(team.router, prefix="/team", tags=["Team"], dependencies=[Depends(get_current_user)])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"], dependencies=[Depends(get_current_user)])
app.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"], dependencies=[Depends(get_current_user)])
app.include_router(reports.router, prefix="/reports", tags=["Reports"], dependencies=[Depends(get_current_user)])
