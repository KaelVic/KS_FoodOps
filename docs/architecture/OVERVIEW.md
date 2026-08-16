# Visão Geral da Arquitetura — KS FoodOps

## 1. Princípio Arquitetural
O KS FoodOps é estruturado como um **Monólito Modular** (Modular Monolith) em Python (FastAPI/Celery) e TypeScript (Next.js), utilizando PostgreSQL como a única fonte da verdade e Redis exclusivamente como broker assíncrono e cache transitório.

## 2. Estrutura de Diretórios
```text
apps/
  api/       # FastAPI REST API, routers e dependências de autenticação/RLS
  web/       # Next.js App Router (SSR, Server Actions, Glassmorphism UI)
  worker/    # Celery Worker para tarefas de fundo (recalculo de inteligência, NF-e)

modules/
  catalog/       # SKUs, Categorias, Unidades de Medida e Conversões
  suppliers/     # Fornecedores e De-Para de Produtos
  purchasing/    # Pedidos de Compra e Reconciliação 3-Way
  inventory/     # Stock Movements, Ledger Entries, Balances e Sessões de Inventário
  costing/       # Motor de apuração de Custo Médio Ponderado e CMV
  recipes/       # Fichas Técnicas Versionadas e Ingredientes
  sales/         # Ingestão de Vendas de PDVs e Consumo Teórico
  documents/     # Ingestão e Parsing de NF-e v4.00
  intelligence/  # Curva ABC, Ponto de Ressuprimento e Sugestão de Compras
  reporting/     # Relatórios consolidados e exportação contábil

packages/
  tenant/        # RLS, Database sessions e modelos de inquilinos
  security/      # JWT, RBAC, Hashes e proteção de rotas
  audit/         # Trilha de auditoria transacional imutável
  notifications/ # Despacho de notificações e alertas operacionais
  integrations/  # Adapters de webhook para PDVs externos
  observability/ # Structured JSON logging e rastreamento
```
