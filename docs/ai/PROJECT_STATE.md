Project: KS FoodOps
Current phase: Fase 15 Concluída — Pronto para Produção & Go-Live (100% dos 4 Pilares Implementados)
Migration head: 626585d47080 (create_get_user_tenants_function)
Last validated commit: HEAD
Tests: 76 passed, 1 skipped, 0 failed
Known failures: None

Implemented:
- [x] Phase 1: Tenant & Base Architecture (PostgreSQL RLS Multi-tenancy)
- [x] Phase 2: Purchasing & Goods Receipt (Immutable Ledger)
- [x] Phase 3: Inventory Engine & Core Ledger (Exact Decimal Math)
- [x] Phase 4: Job System & Transactional Outbox (Celery Worker)
- [x] Phase 5: Recipes, Sales & Purchasing Automation (Theoretical Consumption)
- [x] Phase 6: Financial Closing & Consolidated Reporting (Operational Actual CMV)
- [x] Phase 7: Document Ingestion (OCR/XML SEFAZ v4.00) & AI Proposals
- [x] Phase 8: Advanced Intelligence & Analytics (ABC Curve, Purchase Suggestions)
- [x] Phase 9: Security Hardening & Docker Isolation (CSP, HSTS, Rate Limiting)
- [x] Phase 10: Scheduled Automation via Celery Beat (Restock & Outbox)
- [x] Phase 11: Frontend Intelligence Dashboards (Next.js 16 Glassmorphism)
- [x] Phase 12: Master Data CRUDs & Gestão de Equipe (Pilar A: /catalog, /suppliers, /locations, /team)
- [x] Phase 13: Onboarding Wizard & Central de Notificações (Pilar B: /onboarding, /notifications)
- [x] Phase 14: Relatórios Contábeis & Exportações CMV (Pilar C: /reports/closing, CSV & SPED Bloco H)
- [x] Phase 15: Modo Contagem Mobile & Go-Live (Pilar D: Mobile Count Sheet, Production Checklist & Operational Manual)

## Production Readiness Status
- **Backend**: FastAPI modular monolith rodando com PostgreSQL 16 e RLS ativo.
- **Frontend**: Next.js 16 com Turbopack compilando 100% das 11 rotas estáticas/dinâmicas.
- **Operação Gastronômica**: Suporte integral a fluxo diário de compras, recebimento de NF-e, contagem física mobile e conciliação contábil SPED Bloco H.

## Documentation
- `docs/ops/PRODUCTION_CHECKLIST.md`: Protocolo oficial de infraestrutura e homologação.
- `docs/ops/OPERATIONAL_MANUAL.md`: Manual operacional de restaurante para donos, gerentes, chefs e estoquistas.
