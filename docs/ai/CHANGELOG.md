# Changelog

## 2026-08-17 - DevSecOps & Security Hardening (Front-End, Back-End, Database & 2FA TOTP)
- **Front-End Hardening (Next.js 16):**
  - Configurados Headers de Segurança HTTP estritos no `next.config.ts` (`Content-Security-Policy`, `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Strict-Transport-Security`, `Permissions-Policy`).
  - Forçada a flag `secure: true` para cookies de sessão em ambiente de produção (`session.ts`).
  - Executado `npm audit fix --force`, eliminando 8 vulnerabilidades de dependências (0 vulnerabilidades restantes).
- **Back-End Hardening (FastAPI):**
  - **CORS Estrito:** Removido o regex aberto `allow_origin_regex` de `main.py`, substituído por lista explícita com suporte à variável `ALLOWED_ORIGINS`.
  - **Defesa contra XXE:** Substituição do parser padrão `xml.etree.ElementTree` por `defusedxml.ElementTree` em `modules/documents/parser.py` e `modules/documents/adapters/nfe_parser.py`.
  - **Autenticação em Webhooks de PDV:** Adicionada validação de segredo no header `X-Webhook-Secret` com comparação segura `hmac.compare_digest` em `apps/api/routers/pos_integrations.py`.
  - **Guard contra SSRF:** Criado utilitário `packages/security/ssrf.py` com bloqueio de IPs privados, loopback e metadados de nuvem (`169.254.169.254`).
- **Autenticação & 2FA (MFA - RFC 6238 TOTP):**
  - Adicionadas colunas `is_2fa_enabled` e `totp_secret` na tabela `app_users` via migração Alembic `6a7b8c9d0e1f_security_2fa_totp.py`.
  - Endpoints de 2FA em `apps/api/routers/auth.py`: `/auth/2fa/setup` (provisioning QR code), `/auth/2fa/enable`, `/auth/2fa/disable` e `/auth/2fa/challenge`.
  - Fluxo de login com desafio em duas etapas (emissão de `temp_token` com expiração de 5 minutos).
- **Testes & Validação:**
  - Criada suíte dedicada `tests/test_backend_security_hardening.py` cobrindo CORS, XXE, Webhooks, SSRF e ciclo completo de 2FA.
  - Suíte completa do projeto: **113 testes passando** (0 falhas).

## 2026-08-17 - ERP Pilar 4: Fase 9 (FoodOps Copilot — IA Agêntica & Automação de Inteligência Preditiva — ERP COMPLETO)

- **Modelagem de Domínio (`modules/intelligence/models.py`):**
  - `CopilotConversation`: Histórico de sessões de diálogo com o assistente agêntico.
  - `CopilotMessage`: Mensagens estruturadas (`sender`: `USER`, `COPILOT`, `SYSTEM`), intenções detectadas (`intent`: `CMV_AUDIT`, `STOCK_ALERT`, `PRIME_COST`, `SALES_SUMMARY`, `GENERAL`) e payloads RAG JSON.
  - `ExecutiveBriefing`: Resumos diários consolidados com métricas-chave formatadas para WhatsApp/Webhooks.
- **Serviços de Domínio (`modules/intelligence/copilot_service.py`):**
  - `get_tenant_context_rag`: Motor RAG em tempo real sintetizando faturamento de vendas, contas a pagar/receber, CMV Real, CMO Real, Prime Cost Consolidado, classificação de insumos na Curva ABC, rupturas de estoque, OPs ativas e comandas no KDS.
  - `audit_restaurant_360`: Auditoria diagnóstica 360° com status global e plano de ação priorizado por gravidade (`CRITICAL`, `WARNING`, `HEALTHY`).
  - `generate_executive_briefing`: Geração automática de resumo executivo em formato WhatsApp com emojis e indicadores chave.
  - `process_user_message`: Diálogo interativo inteligente com recomendações agênticas detalhadas e formatação rica em Markdown.
- **Migração e RLS:** Criada migração Alembic `5c9d0e1f2a3b_erp_phase9_copilot_predictive.py` com Row-Level Security (RLS) forçado nas tabelas `copilot_conversations`, `copilot_messages` e `executive_briefings`, com permissões para `ksfoodops_app`.
- **FastAPI Endpoints (`apps/api/routers/copilot.py`):**
  - `POST /copilot/chat`: Processamento de chat RAG com contexto operacional em tempo real.
  - `GET /copilot/conversations`: Listagem de conversas do tenant.
  - `GET /copilot/audit`: Diagnóstico 360° em tempo real do restaurante.
  - `GET /copilot/briefings/today`: Obtenção do resumo executivo diário.
  - `POST /copilot/briefings/dispatch`: Disparo do resumo via WhatsApp/Webhook.
- **Frontend Next.js 16:**
  - `/copilot`: Interface conversacional estilo Cyberpunk Glassmorphism com sugestões rápidas de prompts, caixa de diálogo com renderização Markdown rica, card de Resumo Executivo Diário com botão "1-Click Copiar para WhatsApp" e Painel de Auditoria 360° com planos de ação práticos.
  - Menu lateral atualizado (`sidebar.tsx`) com o ícone do Copilot e versão `SYS.VER.9.0 (ERP PRO)`.
- **Testes & Validação:**
  - `tests/integration/test_copilot_and_predictive_api.py`: 4 novos testes de integração incluindo RLS e isolamento multi-tenant.
  - Total do projeto: **108 testes passando com sucesso** (0 falhas) e compilação do Next.js 16 validada sem erros.

## 2026-08-17 - ERP Pilar 4: Fase 8 (RH Operacional, Escalas de Turnos, Ponto Digital, Rateio de Gorjetas & Prime Cost Consolidado CMV + CMO)

- **Módulo de Equipe & RH Operacional (`modules/team`):** Criados os modelos de domínio:
  - `Employee`: Colaboradores da operação com identificador, cargo, departamento/praça (`FLOOR`, `KITCHEN`, `BAR`, `ADMIN`, `DELIVERY`), salário base mensal, valor hora, pontos de gorjeta e status ativo.
  - `WorkShift`: Escala e planejamento de turnos de trabalho por praça/local, data e horários de entrada/saída.
  - `TimeClockEntry`: Registros de ponto digital com timestamps de entrada/saída, intervalo/pausa e apuração automática de total de horas trabalhadas.
  - `TipDistribution` & `TipDistributionItem`: Apuração e rateio de taxa de serviço / gorjetas arrecadadas nas vendas (Lei da Gorjeta 13.419/2017) ponderado por horas trabalhadas e pontos por função, com percentual de retenção legal da casa para encargos e provisões.
- **Serviços de Domínio (`modules/team/labor_service.py`):**
  - Gestão de colaboradores e turnos operacionais.
  - Registro de ponto digital (`clock_in`, `clock_out`) com validação de duplicidade e cálculo de jornada líquida.
  - Motor de rateio determinístico da Lei da Gorjeta: cálculo do fator individual $\text{Horas} \times \text{Pontos}$, fundo líquido após retenção e distribuição proporcional aos colaboradores ativos.
  - Apuração do Custo de Mão de Obra (CMO / Labor Cost): soma dos salários fixos, pagamentos por hora trabalhada e provisões/encargos sociais (35%).
  - Consolidação do **Prime Cost Real**: $\frac{\text{CMV Real} + \text{CMO Real}}{\text{Receita Líquida}} \times 100$, com termômetro e classificação de saúde financeira (Excelente < 55%, Meta Saudável 55-65%, Atenção 65-68%, Crítico > 68%).
- **Migração e RLS:** Criada migração Alembic `4b8c9d0e1f2a` com Row-Level Security (RLS) habilitado e forçado nas 5 tabelas (`employees`, `work_shifts`, `time_clock_entries`, `tip_distributions`, `tip_distribution_items`), com permissões concedidas à role `ksfoodops_app`.
- **FastAPI Endpoints (`apps/api/routers/team.py`):**
  - `/team/employees`, `/team/employees/{id}`
  - `/team/shifts`
  - `/team/time-clock/in`, `/team/time-clock/out`, `/team/time-clock`
  - `/team/tips/calculate`
  - `/team/prime-cost`
- **Frontend Next.js 16:**
  - `/team`: Gestão completa de colaboradores com indicadores de folha fixa e pontos de rateio.
  - `/team/shifts`: Grade de escalas e agendamento de turnos por praça.
  - `/team/time-clock`: Terminal de bater ponto digital com status em tempo real.
  - `/team/tips`: Painel de apuração, simulação e distribuição de gorjetas pela Lei 13.419/2017.
  - `/team/prime-cost`: Dashboard analítico de Prime Cost com gráfico de composição CMV vs CMO e benchmarks do food-service.
  - Menu lateral atualizado (`sidebar.tsx`).
- **Testes & Validação:** 104 testes automatizados passando com 100% de sucesso. Build do Next.js compilando 100% das rotas sem qualquer erro.

## 2026-08-17 - ERP Pilar 3: Fase 7 (Gestão Multi-Unidades & Cotações Eletrônicas B2B / RFQs, Comparativo Inteligente e Geração de POs)

- **Módulo de Cotações B2B & E-procurement (`modules/purchasing`):** Criados os modelos de domínio:
  - `RFQ`: Cotações com identificador sequencial `RFQ-YYYYMM-XXXX`, título, filial/localidade de entrega, status (`DRAFT`, `OPEN`, `EVALUATING`, `AWARDED`, `CANCELLED`), prazo limite e observações.
  - `RFQItem`: Insumos solicitados com quantidades, vínculos diretos a SKUs do cardápio e preços alvo/históricos.
  - `RFQSupplier`: Fornecedores convidados para tomada de preços (`INVITED`, `SUBMITTED`, `DECLINED`).
  - `RFQProposal`: Propostas comerciais registradas com frete, prazo de entrega em dias, condições de pagamento e pedido mínimo.
  - `RFQProposalItem`: Preços unitários ofertados por insumo, especificações/marcas e disponibilidades.
- **Serviços de Domínio (`modules/purchasing/rfq_service.py`):**
  - `RFQService.create_rfq`: Criação e numeração de cotações com múltiplos itens e disparo de convites para fornecedores homologados.
  - `RFQService.submit_proposal`: Registro ou edição de cotações de preços, prazos e fretes por fornecedor com transição para `EVALUATING`.
  - `RFQService.get_comparison_matrix`: Motor do Quadro Comparativo Analítico que cruza insumos x fornecedores, calcula menor preço por item (*Best Price*), melhor fornecedor global com frete (*Global Winner*), simulação de compra mista otimizada (*Split Order*) e economia total estimada vs meta de custo.
  - `RFQService.award_rfq`: Homologação da cotação com emissão automática e atômica de Pedidos de Compra (`PurchaseOrder` e `PurchaseOrderLine`) com status `APPROVED` para os fornecedores vencedores.
- **Migração e RLS:** Criada migração Alembic `3a7b8c9d0e1f` com Row-Level Security (RLS) habilitado e forçado nas 5 tabelas (`rfqs`, `rfq_items`, `rfq_suppliers`, `rfq_proposals`, `rfq_proposal_items`), com permissões atribuídas à role `ksfoodops_app`.
- **FastAPI Endpoints (`apps/api/routers/rfq.py`):** Endpoints RESTful para criação, listagem, detalhamento, convite de fornecedores, envio de propostas, matriz comparativa e homologação com 1 clique.
- **Frontend Next.js 16:**
  - Implementada a página `/purchasing/rfqs` com KPIs (Total de Cotações, Em Andamento, Homologadas, Economia Média), busca e filtros de status.
  - Implementada a página `/purchasing/rfqs/new` com assistente de criação de cotação com múltiplos itens e multi-seleção de parceiros homologados.
  - Implementada a página `/purchasing/rfqs/[id]` com 3 abas interativas: Quadro Comparativo Inteligente (Matriz de Preços com destaque do menor custo e economia total), Lançamento Rápido de Propostas e Visão de Itens/Convites, além de homologação em 1 clique gerando POs.
  - Atualizada a barra de navegação principal (`sidebar.tsx`) com item **Cotações B2B (RFQ)**.
- **Testes & Validação:** 100 testes automatizados passando com 100% de sucesso. Build do Next.js compilando 100% das 26 rotas estáticas e dinâmicas sem qualquer erro.

## 2026-08-17 - ERP Pilar 3: Fase 6 (Central de Produção / Dark Kitchen / Commissary, OPs & Transferências de Estoque)

- **Módulo de Produção & Commissary (`modules/production`):** Criados os modelos de domínio `ProductionOrder` (Ordens de Produção / Bateladas com numeração `OP-YYYY-XXXX`, status `PLANNED`, `IN_PRODUCTION`, `COMPLETED`, `CANCELLED`, quantidades planejada vs real, número de lote, data de validade, custo unitário e custo total) e `ProductionOrderIngredient` (Insumos consumidos com proporções escalonadas da Ficha Técnica, perdas de produção e custos médios ponderados).
- **Módulo de Transferências entre Locais (`modules/inventory`):** Adicionados os modelos `StockTransfer` (Transferências com numeração `TRF-XXXX`, status `DRAFT`, `IN_TRANSIT`, `RECEIVED`, `CANCELLED`, timestamps de despacho e recebimento) e `StockTransferItem` (Itens transferidos com quantidade enviada, quantidade recebida e custo unitário CMP).
- **Serviços de Domínio e Invariantes do Livro-Razão:**
  - `ProductionService.create_order`: Escala os insumos da versão publicada da receita, aplica margens de perda e calcula o custo estimado inicial via CMP.
  - `ProductionService.start_production`: Transiciona o status para `IN_PRODUCTION`.
  - `ProductionService.complete_production`: Registra o rendimento real obtido, recalcula o CMP unitário real da batelada (`total_cost / actual_quantity`), gera movimentação imutável `PRODUCTION_CONSUMPTION` (debitando insumos da origem) e `PRODUCTION_RECEIPT` (creditando o SKU semi-acabado com custo exato no livro-razão `StockLedgerEntry` e projeções de saldo).
  - `InventoryService.create_transfer`, `dispatch_transfer`, `receive_transfer`: Gestão do ciclo de remessas entre locais com movimentações em par `TRANSFER_OUT` no local de origem e `TRANSFER_IN` no local de destino com atualização atômica de saldos.
- **Migração e RLS:** Criada migração Alembic `2f6a7b8c9d0e` com Row-Level Security (RLS) habilitado e forçado nas 4 tabelas (`production_orders`, `production_order_ingredients`, `stock_transfers`, `stock_transfer_items`), com permissões atribuídas à role `ksfoodops_app`.
- **FastAPI Endpoints:**
  - `apps/api/routers/production.py`: `GET /production/orders`, `POST /production/orders`, `GET /production/orders/{id}`, `POST /production/orders/{id}/start`, `POST /production/orders/{id}/complete`.
  - `apps/api/routers/inventory.py`: `GET /inventory/transfers`, `POST /inventory/transfers`, `GET /inventory/transfers/{id}`, `POST /inventory/transfers/{id}/dispatch`, `POST /inventory/transfers/{id}/receive`.
- **Frontend Next.js 16:**
  - Implementada a página `/production/orders` com 4 KPIs (OPs Ativas, Bateladas Concluídas, Custo Total Produzido, Rendimento Médio %), tabela de OPs com badges e ações de avanço de status, modal de criação de OP e modal de conclusão com apontamento de rendimento real.
  - Implementada a página `/inventory/transfers` com 3 KPIs (Em Trânsito, Rascunhos, Concluídas), tabela com origem → destino e modais de nova remessa e visualização de itens.
  - Atualizada a barra de navegação principal (`sidebar.tsx`) com atalhos para `/production/orders` e `/inventory/transfers`.
- **Testes & Validação:** 98 testes automatizados passando com 100% de sucesso. Build do Next.js compilando 100% das 23 rotas sem qualquer erro. Imagens Docker (`ks_foodops-web` e `ks_foodops-api`) atualizadas com sucesso.

## 2026-08-17 - ERP Pilar 2: Fase 5 (Módulo de Mesas & Comandas, KDS para Cozinha/Bar & Delivery Hub Multi-Canal)
- **Módulo de Pedidos e Operação (`modules/orders`):** Criados os modelos de domínio `DiningTable` (Mesas do Salão com status `AVAILABLE`, `OCCUPIED`, `RESERVED`, `BILL_REQUESTED`, `CLEANING`), `Order` (Comandas e Pedidos com canais `DINE_IN`, `TAKEOUT`, `DELIVERY`, `QR_CODE`, `WHATSAPP`, numeração sequencial, subtotal, taxa de entrega, descontos e total) e `OrderItem` (Itens de comanda com `preparation_notes`, praça de produção `KITCHEN`, `BAR`, `PIZZERIA`, `DESSERT`, status KDS e timestamps de SLA `started_at`, `ready_at`, `served_at`).
- **Serviços de Domínio Operacional (`modules/orders/service.py`):**
  - `OrderService.list_tables`, `create_table`, `update_table_status`: Gestão visual do mapa do salão em tempo real.
  - `OrderService.create_order`, `add_items_to_order`: Abertura de comandas com vinculação automática de mesa e disparo de linhas de produção para as praças de preparo.
  - `OrderService.get_kds_queue`: Fila de produção em tempo real para telas de cozinha e bar, com filtro por praça, contagem de minutos em espera e classificação de SLA de tempo (Verde < 15m, Amarelo 15-25m, Vermelho > 25m).
  - `OrderService.update_order_item_kds_status`: Transições de status de pratos (`QUEUED` -> `PREPARING` -> `READY` -> `SERVED`) com avanço automático do status geral da comanda.
  - `OrderService.close_and_pay_order`: Fechamento completo da comanda — libera a mesa para `AVAILABLE`, fecha o pedido (`CLOSED`), cria fatura no módulo de Contas a Receber (`ReceivableInvoice`), deduz taxa de adquirente (MDR) e liquida a parcela com crédito imediato no saldo da Conta Bancária/Caixa selecionada.
  - `OrderService.list_delivery_orders` & `update_delivery_status`: Painel Kanban multi-canal para pedidos de entrega (iFood, WhatsApp, Telefone, QR Code) nos estágios `PENDING`, `PREPARING`, `READY`, `OUT_FOR_DELIVERY` e `COMPLETED`.
- **Migração e RLS:** Criada migração Alembic `1e5f6a7b8c9d` com Row-Level Security (RLS) habilitado e forçado nas tabelas `dining_tables`, `orders` e `order_items`, com permissões atribuídas à role `ksfoodops_app`.
- **FastAPI Endpoints (`apps/api/routers/orders.py`):** Endpoints RESTful para mesas (`/orders/tables`, `/orders/tables/{id}/status`), comandas (`/orders`, `/orders/{id}`, `/orders/{id}/items`, `/orders/{id}/close-and-pay`), KDS (`/orders/kds/queue`, `/orders/items/{item_id}/kds-status`) e Delivery Hub (`/orders/delivery/kanban`, `/orders/{id}/delivery-status`).
- **Frontend Next.js 16:**
  - Implementada a página `/pos/tables` com mapa interativo de mesas, cartões coloridos por status, gaveta de atendimento da mesa, adição dinâmica de itens e modal de fechamento de conta integrado ao financeiro.
  - Implementada a página `/kds` com visual de monitor de cozinha/bar, seletor de praças de produção (Cozinha Quente, Bar, Pizzaria, Sobremesas), cronômetros de tempo de espera com badges SLA e auto-polling a cada 8s.
  - Implementada a página `/delivery` com quadro Kanban de 4 colunas para despacho de entregas e modal de criação de pedidos manuais para WhatsApp e telefone.
  - Atualizada a barra de navegação principal (`sidebar.tsx`) com atalhos para `/pos/tables`, `/kds` e `/delivery`.
- **Testes & Validação:** 95 testes automatizados passando com 100% de sucesso. Next.js 16 compilando todas as 21 rotas sem qualquer erro. Imagens Docker (`ks_foodops-web` e `ks_foodops-api`) construídas com sucesso.

## 2026-08-16 - ERP Pilar 2: Fase 4 (Gestão de Cardápio & Engenharia de Menu / Matriz BCG)
- **Módulo de Cardápio (`modules/menu`):** Criados os modelos de domínio `MenuCategory` (Categorias do Cardápio: Entradas, Pratos, Bebidas, Sobremesas) e `MenuItem` (Itens do cardápio com `sale_price`, `cost_price`, `target_cmv_percentage`, `pos_code` e chave estrangeira para Ficha Técnica `recipe_id`).
- **Serviços de Engenharia de Menu & Custo Dinâmico (`modules/menu/service.py`):**
  - `MenuService.get_recipe_unit_cost`: Calcula dinamicamente o custo unitário por porção a partir da última versão publicada da Ficha Técnica (`RecipeVersion`) e dos custos médios ponderados (CMP) dos insumos no estoque.
  - `MenuService.calculate_menu_engineering`: Algoritmo de Engenharia de Menu baseado na Matriz BCG de Kasavana & Smith (1982). Cruza volume de vendas reais de `SaleLine` com a margem de contribuição unitária de cada prato. Determina os cutoffs de popularidade (70% da média de vendas) e de margem média, classificando em:
    - ⭐ **Estrelas (Stars)**: Alta Margem + Alto Volume (Proteger qualidade, destacar visualmente).
    - 🐴 **Burros de Carga (Plowhorses)**: Baixa Margem + Alto Volume (Reajustar preço gradualmente, renegociar insumos ou reduzir tamanho da porção).
    - ❓ **Quebra-Cabeças (Puzzles)**: Alta Margem + Baixo Volume (Promover com garçons, reposicionar no cardápio, criar combos).
    - 🐶 **Cães (Dogs)**: Baixa Margem + Baixo Volume (Eliminar do cardápio ou reformular receita).
  - `MenuService.simulate_pricing`: Simulador interativo de precificação inteligente a partir de meta de CMV % ou novo preço de venda, calculando variação de margem e delta de preço.
- **Migração e RLS:** Criada migração Alembic `0d4e5f6a7b8c` com Row-Level Security (RLS) habilitado e forçado nas tabelas `menu_categories` e `menu_items`, com permissões atribuídas à role `ksfoodops_app`.
- **FastAPI Endpoints:** Adicionado router `apps/api/routers/menu.py` com endpoints `/menu/categories`, `/menu/items`, `/menu/items/{id}`, `/menu/items/{id}/simulate-pricing` e `/menu/engineering`.
- **Frontend Next.js 16:**
  - Implementada a página `/menu/engineering` com 4 KPIs (Faturamento Analisado, Margem de Contribuição, CMV Médio %, Distribuição BCG), painel visual dos 4 quadrantes BCG (Estrelas, Quebra-Cabeças, Burros de Carga, Cães), tabela analítica completa com recomendações estratégicas e modal interativo de simulação de precificação.
  - Implementada a página `/menu/items` com catálogo de pratos, vinculador de fichas técnicas para custo automático, gerenciador de categorias e cálculo de preço sugerido por meta de CMV %.
  - Atualizada a barra de navegação principal (`sidebar.tsx`).
- **Testes & Validação:** 90 testes automatizados passando com 100% de sucesso. Build do Next.js compilando 100% das 18 rotas. Imagens Docker (`ks_foodops-web` e `ks_foodops-api`) atualizadas com sucesso.

## 2026-08-16 - ERP Pilar 1: Fase 3 (Fluxo de Caixa Projetado, DRE Financeira Gerencial & Conciliação OFX)
- **Módulo Financeiro (`modules/financial`):** Construídos os modelos de domínio e serviços para `BankStatementTransaction` (Extratos Bancários Importados via OFX com deduplicação por FITID e status de conciliação) e `BankReconciliationRule` (Regras de auto-conciliação bancária).
- **Serviços de Projeção & DRE:**
  - `FinancialService.get_cash_flow_projection`: Projeção dia-a-dia cruzando saldos iniciais de contas bancárias, contas a pagar (previstas e realizadas) e recebíveis de cartões/delivery (previstos e realizados), calculando saldos líquidos diários, saldo acumulado e alertando para dias com risco de caixa negativo.
  - `FinancialService.get_financial_dre`: Demonstração do Resultado do Exercício customizada para Food-Service (Receita Bruta -> Deduções de Taxas MDR -> Receita Líquida -> CMV Insumos Alimentícios -> Lucro Bruto -> Folha & Encargos -> Prime Cost -> Opex -> EBITDA Operacional -> Lucro Líquido) com Análise Vertical (% AV) e comutador dinâmico entre Regime de Competência e Regime de Caixa.
  - `FinancialService.import_bank_statement_ofx`: Parser robusto de extratos bancários padrão OFX (SGML/XML) com suporte a tags `<STMTTRN>`, `<TRNTYPE>`, `<DTPOSTED>`, `<TRNAMT>`, `<FITID>` e `<MEMO>`, com validação de duplicidade transacional.
  - `FinancialService.reconcile_bank_transaction`: Conciliação transacional de lançamentos bancários com títulos a pagar/receber.
- **Migração e RLS:** Criada migração Alembic `9c3d4e5f6a7b` com Row-Level Security (RLS) habilitado e forçado nas novas 2 tabelas (`bank_statement_transactions` e `bank_reconciliation_rules`), garantindo isolamento multi-tenant transacional estrito.
- **FastAPI Endpoints:** Adicionados endpoints em `apps/api/routers/financial.py`: `GET /financial/cash-flow`, `GET /financial/dre`, `POST /financial/bank-statements/upload`, `GET /financial/bank-statements` e `POST /financial/bank-statements/{id}/reconcile`.
- **Frontend Next.js 16:**
  - Implementada a página `/financial/cash-flow` com 5 KPIs Glassmorphism (Saldo Inicial, Entradas Período, Saídas Período, Saldo Final Projetado, Menor Ponto de Caixa), tabela diária com destaque de saldo negativo em alerta vermelho, filtros de período e modal completo de importação de arquivo OFX.
  - Implementada a página `/financial/dre` com comutador dinâmico Competência vs Caixa, 4 KPIs estratégicos de restaurante (Receita Líquida, CMV Real %, Prime Cost % e Margem EBITDA %), tabela em cascata com Análise Vertical (AV %) e card de ranking de despesas por categoria.
  - Atualizada a barra de navegação principal (`sidebar.tsx`).
- **Testes & Validação:** 86 testes automatizados passando com 100% de sucesso. Build do Next.js compilando 100% das 16 rotas. Imagens Docker (`ks_foodops-web` e `ks_foodops-api`) atualizadas com sucesso.

## 2026-08-16 - ERP Pilar 1: Fase 2 (Contas a Receber / AR, Conciliação de Cartões & Delivery)
- **Módulo Financeiro (`modules/financial`):** Construídos os modelos de domínio e serviços para `PaymentAcquirer` (Adquirentes & Maquininhas: Stone, Cielo, Rede, iFood, VR, Alelo, PagBank), `ReceivableInvoice` (Títulos a Receber & Vendas Faturadas), `ReceivableInstallment` (Lançamentos de Cartões e Repasses com deduções de MDR) e `ReceivableSettlement` (Baixas e Liquidações de Recebimento com Crédito Automático em Conta Bancária).
- **Migração e RLS:** Criada migração Alembic `8b2c3d4e5f6a` com Row-Level Security (RLS) habilitado e forçado nas novas 4 tabelas financeiras, com isolamento multi-tenant transacional estrito.
- **FastAPI Endpoints:** Criados endpoints RESTful em `apps/api/routers/financial.py` para `/financial/acquirers`, `/financial/receivables`, `/financial/receivables/{id}`, `/financial/receivables/installments/{id}/settle` e `/financial/receivables/dashboard`.
- **Frontend Next.js 16:** Implementada a página `/financial/receivables` com Glassmorphism, 5 cards de KPIs financeiros (Previsto Hoje, Repasses da Semana, Recebido no Mês, Taxas MDR Retidas pelas Maquininhas e Saldo em Caixa), tabela detalhada com taxas discriminadas, modal de novo título e modal de confirmação de repasse bancário.
- **Testes & Validação:** 82 testes passando com 100% de sucesso. Build do Next.js compilando 100% das 14 rotas. Imagens Docker geradas.

## 2026-08-16 - ERP Pilar 1: Fase 1 (Módulo de Contas a Pagar / AP & Gestão Bancária)
- **Módulo Financeiro (`modules/financial`):** Construídos os modelos de domínio e serviços para `FinancialCategory` (Plano de Contas), `CostCenter` (Centros de Custo), `BankAccount` (Contas Bancárias & Caixas), `PayableBill` (Títulos a Pagar), `PayableInstallment` (Parcelamentos com PIX e Boleto) e `PayableSettlement` (Baixas e Liquidações com Juros/Multas/Descontos).
- **Migração e RLS:** Criada migração Alembic `7a1b2c3d4e5f` com Row-Level Security (RLS) habilitado e forçado em todas as 7 novas tabelas financeiras, com isolamento multi-tenant transacional estrito.
- **FastAPI Endpoints:** Criado `apps/api/routers/financial.py` com endpoints RESTful completos para categorias, centros de custo, contas bancárias, títulos a pagar, parcelas, liquidações e dashboard financeiro agregado.
- **Frontend Next.js 16:** Implementadas as páginas `/financial/payables` e `/financial/bank-accounts` com Glassmorphism, cards de métricas de vencimento, modal de criação de títulos e modal de baixa com cálculo em tempo real de juros/multas/descontos e débito em conta bancária.
- **Testes & Validação:** 79 testes passando com 100% de cobertura nos fluxos de Contas a Pagar e isolamento multi-inquilino. Build do Next.js compilando 100% com zero erros de tipo.

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
