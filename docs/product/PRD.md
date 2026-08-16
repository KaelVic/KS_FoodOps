# Product Requirements Document (PRD) — KS FoodOps

## 1. Visão Geral do Produto
O **KS FoodOps** é um SaaS multi-tenant especializado na gestão operacional, controle de estoque, inteligência de compras, apuração de CMV (Custo da Mercadoria Vendida) e ficha técnica para o setor de **Food Service** (restaurantes, bares, dark kitchens e franquias).

## 2. Proposta de Valor
- **Eliminação de Alucinação Financeira**: Toda movimentação e apuração de custos é sustentada por um **Stock Ledger append-only** com matemática decimal exata (`Decimal` / `NUMERIC`).
- **Automação Fiscal e de Compras**: Ingestão determinística de NF-e (SEFAZ XML v4.00), reconciliação 3-Way (*Pedido vs Nota vs Recebimento Físico*) e sugestão de compras orientada por ponto de ressuprimento e curva ABC.
- **Engenharia de Cardápio & CMV em Tempo Real**: Fichas técnicas versionadas e imutáveis integradas a PDVs para apuração contínua do consumo teórico versus inventário real.

## 3. Personas de Usuário
1. **Diretor / Sócio-Operador**: Acompanha painéis executivos de CMV Real vs Teórico, divergências financeiras e lucratividade por categoria.
2. **Gerente de Loja / Operações**: Abre e fecha inventários físicos, supervisiona perdas operacionais e recebe pedidos de fornecedores.
3. **Comprador / Suprimentos**: Emite ordens de compra, avalia variações de preços de fornecedores e gerencia cotações baseadas na Curva ABC.
4. **Estoquista / Operador de Bar/Cozinha**: Realiza contagens cegas (*blind counts*) e efetua recebimento físico de mercadorias.

## 4. Requisitos Funcionais Principais
- **Multi-Tenancy Rígido**: Isolamento por Row-Level Security (RLS) no PostgreSQL por `tenant_id`.
- **Ledger Imutável de Estoque**: Registros `POSTED` não podem ser alterados ou deletados. Correções são efetuadas por novos lançamentos de estorno.
- **Inventário Físico com Contagem Cega**: Bloqueio de consulta a saldos teóricos durante a contagem para garantir acurácia de campo.
- **Ingestão Inteligente de NF-e**: De-para automatizado com revisão humana obrigatória (*Human-in-the-Loop*).
- **Consumo Teórico por Vendas**: Baixa automática de ingredientes com base na versão da ficha técnica ativa na data/hora do cupom fiscal.
