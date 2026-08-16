# Changelog

## 2026-08-16 - Phase 15 Completion (Modo Contagem Mobile & Go-Live)
- **Phase 15 (Pilar D):** Aprimorado o módulo de contagem física de estoque (`SessionDetailClient.tsx`) com interface touch responsiva para smartphones (Mobile Count Sheet), barra de progresso visual em tempo real (`X/Y itens contados`), abas de filtro (`Todos`, `Pendentes`, `Contados`) e feedback instantâneo de autosave.
- Criados `docs/ops/PRODUCTION_CHECKLIST.md` (requisitos técnicos, infraestrutura e segurança) e `docs/ops/OPERATIONAL_MANUAL.md` (manual de uso para donos de restaurantes, gerentes, chefs e estoquistas).
- Conclusão com 100% de sucesso de todas as 15 Fases do KS FoodOps. Build de frontend e testes de backend totalmente validados.
## 2026-08-16 - Phase 14 Completion (Relatórios Contábeis & Exportações CMV)
- **Phase 14 (Pilar C):** Implementado módulo de relatórios analíticos de Fechamento Contábil e DRE Operacional (`modules/reporting/service.py`, `consolidated.py`, `exporter.py`, `apps/api/routers/reports.py`).
- Exportação de inventário valorizado em formato CSV (BOM UTF-8, compatível com Excel) e padrão SPED Fiscal Bloco H (`|H001|`, `|H005|`, `|H010|`, `|H990|`).
- Dashboard de Fechamento Contábil no frontend Next.js 16 (`/reports/closing`) com KPIs de Faturamento, CMV Real (%), CMV Teórico, Perdas e Divergência, e download em um clique. Validação de testes pytest e build do Next.js aprovados.
## 2026-08-16 - Phase 13 Completion (Onboarding Wizard & Notificações)
- **Phase 13 (Pilar B):** Implementada rota transacional de `/onboarding` garantindo a configuração limpa do Tenant, Business Unit, Location de Estoque Geral e permissão de Admin em uma única query.
- Sistema de Notificações isoladas por Tenant construído (`Notification` model) com endpoints `/notifications`.
- No frontend, o componente interativo `OnboardingWizard` em Next.js e o componente de `NotificationBell` com polling implementados com design aderente. Validação do build do Next.js aprovada.
## 2026-08-16 - Phase 12 Completion (Master Data CRUDs)
- **Phase 12 (Master Data & Equipe):** Implementados serviços e routers no backend FastAPI (`catalog`, `suppliers`, `locations`, `team`) para gerenciar as entidades primárias do restaurante. Adicionado CRUD para Categorias, UOMs, SKUs, Conversões, Locais físicos, e Controle de Acesso por papel (RBAC via TenantMemberships).
- No frontend Next.js, os dashboards visuais foram gerados (`/catalog`, `/suppliers`, `/locations`, `/team`) consumindo os dados sob SSR em componentes `Glassmorphism`. Validação de Typescript 100% OK via build.
## 2026-08-16 - Phase 8 to 11 Completion (Intelligence, Security Hardening & Automation)
- **Phase 8 (Advanced Intelligence):** Implemented Core Intelligence Algorithms (ABC Curve classification, Days of Coverage, Threshold-based Purchase Suggestions). Created `apps/api/routers/intelligence.py` with 5 major endpoints (`/abc`, `/policies`, `/suggestions`, `/alerts`). Validated 67 new tests perfectly isolated via RLS.
- **Phase 9 (Security Hardening & Docker Isolation):** Hard-capped Payload size to 10MB in `upload-nfe` with strict `text/xml` MIME checking. Injected Rate Limiting middleware (`slowapi`) into Authentication, Documents, and Webhooks routers. Strengthened Security HTTP headers (`CSP`, `HSTS`, `X-Frame-Options`). Revalidated `docker-compose.yml` for network segregation and non-root users (`appuser`, `celeryuser`). Added `test_security_hardening.py` suite.
- **Phase 10 (Scheduled Automation via Celery Beat):** Added periodic Celery tasks `schedule_intelligence_for_all_tenants` (runs 02:00 UTC), `cleanup_temporary_files_task` (runs 04:00 UTC), and `process_outbox_messages_task` (runs every 60s). Updated `worker.py` to support `celery.schedules.crontab` and updated `docker-compose.yml` to provision the `beat` container. Tested Celery Beat dispatch rules with 100% success rate.
- **Phase 11 (Frontend Intelligence Dashboards):** Implemented the Intelligence UI in Next.js (`IntelligenceClient.tsx` using `recharts` for Scatter plotting of ABC Curves). Configured Server Actions in `api-server.ts`. Validated the complete app with a 0-error `npm run build` execution.

## 2026-08-15 - Phase 1 Completion: Test Stabilization, POS Integrations & Full Documentation
- Fixed POS webhook ingestion consistency between Celery tasks and native background tasks (`apps/api/routers/pos_integrations.py` and `modules/sales/service.py`).
- Enhanced `SalesService.import_sales` to seamlessly accept both flat item payloads and grouped sale orders with automatic UTC datetime parsing.
- Updated default `JWT_SECRET` key to 32+ bytes across test suites and auth modules, eliminating PyJWT insecure key length warnings.
- Migrated legacy `datetime.utcnow()` occurrences to standard `datetime.now(timezone.utc)`.
- Achieved 100% test pass rate across pytest integration test baseline (50 passed, 0 failures, 1 skipped).
- Authored official base engineering documentation in `docs/` (`PRD.md`, `MVP_SCOPE.md`, `OVERVIEW.md`, `SECURITY.md`, `MULTITENANCY.md`, `GLOSSARY.md`, `INVENTORY_SPEC.md`, `STATE_MACHINES.md`, `TEST_MATRIX.md`).
- Verified Next.js 16 production build (`npm run build`) passing with zero TypeScript and zero lint errors.

## 2026-08-15 - Phase 7 Completion & Integration Testing
- Resolved integration testing issues in `test_intelligence_api.py` regarding PostgreSQL RLS injection and dependency overrides.
- Fixed `get_secure_session` mock dependency to safely override commit/flush lifecycle during test execution using test_db mock injection.
- Re-architected backend routers across `intelligence`, `inventory`, `inventory_sessions`, `purchasing`, and `sales` to safely extract `tenant_id` from standard header, removing ambiguous `get_current_tenant_id` dependency logic.
- Validated `npx tsc --noEmit` and final CI pass metrics for Phase 7 implementation (Inteligência Operacional & ABC).

## 2026-08-15 - NFe XML Ingestion & Purchasing Hub Implementation
- Built real Brazilian SEFAZ NFe XML v4.00 parser in `modules/documents/parser.py` using `xml.etree.ElementTree` with automatic namespace handling.
- Created `apps/api/routers/documents.py` supporting `POST /documents/upload-nfe`, `GET /documents/extractions`, `GET /documents/extractions/{id}`, and `POST /documents/extractions/{id}/approve`.
- Added integration test suite in `tests/integration/test_nfe_upload_api.py` (32/32 tests passing across backend).
- Created TypeScript document definitions in `apps/web/src/types/documents.ts`.
- Implemented `fetchExtractionsServer`, `uploadNFeFile`, `approveExtractionAction`, and client fetchers in `apps/web/src/lib/api-server.ts` and `apps/web/src/lib/api-client.ts`.
- Built Purchasing & NFe Hub UI in `apps/web/src/app/(dashboard)/purchasing/page.tsx` and `PurchasingClient.tsx` featuring Drag & Drop XML uploader, KPI metric cards, and interactive document table with status badges and instant approval action.

- Created `apps/api/routers/inventory.py` providing `GET /inventory/balances` with optional `location_id` filtering and RLS protection.
- Registered `/inventory` router in `apps/api/main.py` with `get_current_user` security dependency.
- Added integration test suite in `tests/integration/test_inventory_api.py` (24/24 passing).
- Created TypeScript contracts in `apps/web/src/types/inventory.ts`.
- Implemented `fetchInventoryBalances` in `apps/web/src/lib/api.ts` reading SSR session and active tenant cookies.
- Built Dark Obsidian Glassmorphism view in `apps/web/src/app/(dashboard)/inventory/page.tsx` featuring KPI summary cards and formatted Data Table.
- Fixed Next.js 16 / Framer Motion type annotations and static analysis warnings across dashboard layout and pages.

- Created `AppUser` model in `packages/security/models.py`.
- Replaced `passlib` with pure `bcrypt` for password hashing to resolve legacy python-bcrypt incompatibility bugs on Windows.
- Added `/auth/login` and `/auth/me` endpoints to FastAPI router.
- Added `get_user_tenants` SECURITY DEFINER function in PostgreSQL to securely bypass RLS restrictions during tenant discovery on login.
- Migrated schema and inserted admin seed data using Alembic migrations (`3267132022e5`, `01cf6be2cc97`, `626585d47080`).
- Implemented frontend API client (`apps/web/src/lib/api.ts`) for secure server-side fetching.
- Created `apps/web/src/app/(auth)/actions.ts` for Next.js Server Actions handling HTTP-Only secure cookies.
- Rebuilt `login` and `select-tenant` pages with premium UI and strict server-side auth validation.
- Validated test suite yielding 100% test pass rate (20/20) resolving `asyncpg` concurrency issues by using `NullPool`.

## 2026-08-14 - Security Audit Fixes
- Replaced mock JWT authentication with `PyJWT`.
- Fixed chicken-and-egg RLS membership check in `dependencies.py` by applying `current_tenant_id` context prior to running the membership query.
- Rewrote `docker-compose.yml` to use isolated networks (`data-net`, `broker-net`), environment variables for credentials, Redis authentication, and memory limits.
- Configured API and Worker Dockerfiles to run as a non-root `appuser`.
- Added CORS, rate limiting (`slowapi`), and security headers to `main.py`.
- Added missing `tenant_id` filters in `inventory/service.py`, `purchasing/service.py`, `recipes/service.py`, and `sales/service.py`.
- Prevented Directory Traversal by normalizing and validating `file_path` in `documents/service.py`.
- Prevented concurrent modifications to `StockBalanceProjection` via `IntegrityError` handling and database-level `UNIQUE` constraints (`tenant_id`, `location_id`, `sku_id`).
- Added `prevent_posted_mutation`, `prevent_closed_mutation`, and `prevent_published_mutation` PostgreSQL triggers via Alembic migration to guarantee Domain Immutability on Stock Movements, Inventory Sessions, and Recipe Versions.
- Upgraded `tenant_isolation_policy` across all RLS-enabled tables to include `WITH CHECK` conditions in Alembic migration, preventing cross-tenant INSERT/UPDATE spoofing.
- Fixed `async_session_maker` import in `tests/conftest.py`.
- Added `tenant_session` context manager in Celery `worker.py` to support RLS in background tasks.
- Improved Mock Auth tests with PyJWT encoding and decoding assertions in `test_auth.py`.
