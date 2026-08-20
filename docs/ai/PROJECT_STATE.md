Project: KS FoodOps (ERP Food-Service)
- **Fase Atual**: **ERP CORE & CHAIN-OF-TRUTH HARDENING (P0, P1 & P2 COMPLETED: THEORETICAL PERPETUAL STOCK, DISH CMV DRIFT, SUPPLIER LEAD TIME & AUDITED CHAIN OF TRUTH)**
- **Status Geral**: Módulos funcionais implementados (~85% cobertura funcional, ~85% integração real, ~85% integridade auditável). Camada gerencial de nível comercial ativa: estoque teórico perpétuo por SKU, detecção de desvio de CMV por prato, projeção de ruptura com lead time real e cadeia de verdade blindada.
- **Data de Atualização**: 20/08/2026
- **Testes Backend**: Suítes P0, P1 e P2 validadas com 100% de sucesso (11 testes).
- **Frontend Build**: Next.js 16 App Router com Turbopack.
- **Alembic Head**: `7b8c9d0e1f2a_phase1_ledger_identity_and_sales_location.py`


---

## 🏆 Resumo da Transformação ERP Completa (9 Fases Concluídas)

1. **Pilar 1 — Inteligência Financeira Avançada (Fase 1 a 3):**
   - Ingestão NFe, Conciliação, Rateios de Frete/Impostos, Tolerâncias.
   - Contas a Pagar/Receber, Baixas Parciais/Totais, Formas de Pagamento, RLS.
   - Fluxo de Caixa Projetado vs Real, DRE Gerencial por Competência/Regime de Caixa.
2. **Pilar 2 — Engenharia de Cardápio & Produção Interna (Fase 4 a 6):**
   - Matriz BCG (Estrelas, Cavalos de Batalha, Quebra-cabeças, Cães), Curva ABC de Insumos.
   - Ordens de Produção (OP), Baixa de Insumos & Entrada de Semi-acabados, Multi-estoque e Transferências Internas.
   - Cotações B2B (RFQ), Envio para Fornecedores, Mapa Comparativo de Preços e Conversão Automática em Pedidos de Compra.
3. **Pilar 3 — Frente de Caixa, Salão & Operação em Tempo Real (Fase 7):**
   - Gestão de Mesas e Comandas, PDV Balcão e Delivery Hub integrado.
   - KDS (Kitchen Display System) em tempo real com SLA e tempo de preparo.
4. **Pilar 4 — RH Operacional, Prime Cost & FoodOps Copilot (Fase 8 e 9):**
   - Colaboradores, Escalas por Praça, Ponto Digital, Rateio de Gorjetas (Lei 13.419/2017).
   - Apuração do Prime Cost Real ($\frac{\text{CMV} + \text{CMO}}{\text{Receita Líquida}}$) com termômetro operacional.
   - FoodOps Copilot: IA Agêntica RAG, Auditoria 360° da Operação, Briefings Executivos Diários formatados para WhatsApp com 1-Click Dispatch.

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
- [x] ERP Pilar 1 - Fase 1: Módulo de Contas a Pagar (AP), Plano de Contas (Categorias), Centros de Custo, Contas Bancárias/Caixas, Parcelamentos, PIX Copia-e-Cola, Linhas Digitáveis de Boleto e Baixas com Juros/Multa/Desconto.
- [x] ERP Pilar 1 - Fase 2: Módulo de Contas a Receber (AR), Gestão de Adquirentes & Maquininhas (Stone, Cielo, Rede, iFood,法, Alelo), Cálculo de Taxas MDR, Previsão de Repasses Financeiros (D+1, D+7, D+30), Conciliação de Vendas e Baixas com Crédito Automático em Conta Bancária.
- [x] ERP Pilar 1 - Fase 3: Fluxo de Caixa Diário Projetado (Previsto vs Realizado com alerta de ponto crítico/negativo), DRE Financeira Gerencial Food-Service (Receita Líquida, CMV Real %, Prime Cost %, Opex, EBITDA, Lucro Líquido e Análise Vertical AV%) com comutador Competência/Caixa, e Conciliação de Extratos Bancários OFX.
- [x] ERP Pilar 2 - Fase 4: Gestão de Cardápio & Engenharia de Menu (Matriz BCG 2x2 Kasavana & Smith: Estrelas, Burros de Carga, Quebra-Cabeças, Cães; Cutoff de Popularidade 70% e Margem Média; Vinculação com Fichas Técnicas para Custo Dinâmico por Porção e Simulador de Precificação Inteligente / Meta de CMV %).
- [x] ERP Pilar 2 - Fase 5: Módulo de Mesas & Comandas (Salão/PDV), KDS Kitchen Display System para Cozinha/Bar/Forno/Sobremesas com cálculo de SLA e alertas visuais de tempo, e Delivery Hub Multi-Canal (iFood, WhatsApp, Telefone, QR Code) com Kanban operacional de despacho e fechamento integrado com faturamento AR e baixa em conta bancária.
- [x] ERP Pilar 3 - Fase 6: Central de Produção (Dark Kitchen / Cozinha Central / Commissary), Ordens de Produção (OPs / Bateladas de Semi-Acabados e Porcionados) com cálculo de rendimento real, recálculo de CMP unitário do semi-acabado e movimentação atômica no livro-razão (`PRODUCTION_CONSUMPTION` e `PRODUCTION_RECEIPT`), e Transferências de Estoque entre Locais (`TRANSFER_OUT` e `TRANSFER_IN`).
- [x] ERP Pilar 3 - Fase 7: Cotação Eletrônica B2B de Fornecedores (RFQs), Quadro Comparativo Inteligente de Preços por Item e Fornecedor Global, Cálculo de Economia Estimada, Cenário de Compra Mista (*Split Order*) e Conversão Automatizada em Pedidos de Compra Homologados (`PurchaseOrder`).
- [x] ERP Pilar 4 - Fase 8: RH Operacional para Food-Service (Gestão de Colaboradores, Salários e Pontos de Gorjeta), Escalas & Turnos por Praça, Terminal de Ponto Digital (Clock In/Out), Rateio da Taxa de Serviço / Gorjetas (Lei 13.419/2017) e Apuração de Custo de Mão de Obra (CMO) com consolidação do Prime Cost Real (CMV + CMO % da Receita Líquida).

## Production & ERP Readiness Status
- **Backend**: FastAPI modular monolith com módulos `financial`, `menu`, `orders`, `production`, `purchasing` e `team`/labor 100% completos, PostgreSQL 16 com RLS ativo em 100% das 32 tabelas (incluindo `employees`, `work_shifts`, `time_clock_entries`, `tip_distributions`, `tip_distribution_items`).
- **Frontend**: Next.js 16 com Turbopack compilando 100% das rotas estáticas/dinâmicas (incluindo `/team`, `/team/shifts`, `/team/time-clock`, `/team/tips` e `/team/prime-cost`).
- **Gestão Operacional de Mão de Obra**: Controle de ponto, apuração de horas, cálculo ponderado de gorjetas e monitoramento de Prime Cost com metas do food-service (55-65%).

## Documentation
- `docs/architecture/OVERVIEW.md`: Visão arquitetural geral.
- `docs/ops/PRODUCTION_CHECKLIST.md`: Protocolo oficial de infraestrutura e homologação.
- `docs/ops/OPERATIONAL_MANUAL.md`: Manual operacional de restaurante.
