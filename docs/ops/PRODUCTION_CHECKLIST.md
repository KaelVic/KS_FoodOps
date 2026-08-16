# Checklist Oficial de Go-Live e Produção — KS FoodOps

Este documento formaliza todos os requisitos e validações necessárias para deploy do **KS FoodOps** em ambiente de produção para restaurantes reais.

---

## 1. Segurança & Multi-Tenancy (PostgreSQL RLS)
- [x] **PostgreSQL Row-Level Security (RLS)**: Habilitado e forçado (`FORCE ROW LEVEL SECURITY`) em todas as tabelas com escopo de tenant.
- [x] **Database User**: Usuário de execução da aplicação (`app_user`) não possui `SUPERUSER` nem `BYPASSRLS`.
- [x] **Contexto Transacional**: Sessões SQLAlchemy configuradas para injetar `app.current_tenant_id` no início de cada transação via middleware.
- [x] **Rate Limiting**: `slowapi` ativo nas rotas de autenticação, upload de NFe e webhooks de POS.
- [x] **Headers de Segurança HTTP**:
  - `Content-Security-Policy: default-src 'self'`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`

---

## 2. Infraestrutura & Containers
- [x] **Docker Segregation**: Rede isolada para PostgreSQL, Redis, Worker e API.
- [x] **Non-root Users**: Contêineres de aplicação executando como `appuser` (UID 1000).
- [x] **Celery Beat & Worker**: Workers de fila com retentativas exponenciais (`max_retries=5`) e outbox transacional para eventos assíncronos.
- [x] **Health & Readiness Probes**:
  - `/health/live`: Liveness probe para orquestradores (K8s/Docker Swarm).
  - `/health/ready`: Readiness probe validando conexão com PostgreSQL e pool de conexões.

---

## 3. Variáveis de Ambiente Mandatórias (Produção)
```bash
# Core & Security
ENVIRONMENT=production
JWT_SECRET=super_secret_min_32_bytes_random_string_generated_securely!
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://app_user:strong_password@db:5432/ks_foodops

# Frontend URL (para CORS)
FRONTEND_URL=https://app.ksfoodops.com

# Redis / Celery
REDIS_URL=redis://redis:6379/0

# Ingestão de Documentos (S3 / Cloud Storage)
STORAGE_BUCKET_NAME=ks-foodops-protected-docs
AWS_REGION=us-east-1
```

---

## 4. Auditoria de Dados & Ledger Imutável
- [x] Movimentações postadas em `stock_movements` são imutáveis (proibido `UPDATE` ou `DELETE`).
- [x] Saldos derivam da tabela de fatos `stock_ledger_entries`.
- [x] Cálculos financeiros e de custo utilizam estritamente tipos exatos `Numeric(24, 12)` / `Decimal` (proibido `float`).
