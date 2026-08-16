# Glossário de Domínio — KS FoodOps

- **SKU (Stock Keeping Unit)**: Unidade mínima rastreável em estoque (ex: Filé Mignon, Tomate Longa Vida, Vodka Absolut 1L).
- **UOM (Unit of Measure)**: Unidade de medida (ex: KG, UN, L, ML, G).
- **Fator de Conversão Versionado**: Relação de conversão entre a unidade de compra/fornecedor e a unidade base de estoque (ex: 1 Caixa = 12 Garrafas).
- **Stock Movement**: Evento físico de movimentação de estoque (`PURCHASE_RECEIPT`, `INVENTORY_ADJUSTMENT`, `THEORETICAL_CONSUMPTION`, `LOSS`, `TRANSFER`).
- **Stock Ledger**: Livro-razão transacional e imutável (append-only) de entradas e saídas valorizadas.
- **CMP (Custo Médio Ponderado)**: Método contábil de apuração do custo do estoque atualizado a cada recebimento físico.
- **CMV (Custo da Mercadoria Vendida)**:
  - *CMV Real Operacional*: `Estoque Inicial + Compras Líquidas ± Transferências - Estoque Final`.
  - *CMV Teórico*: Soma do custo projetado de todos os ingredientes das fichas técnicas baixadas pelas vendas.
- **Contagem Cega (Blind Count)**: Processo de inventário físico onde o operador conta os itens sem ter acesso à quantidade teórica esperada pelo sistema.
- **3-Way Reconciliation**: Conferência cruzada entre o que foi pedido (`ordered`), o que foi entregue fisicamente (`received`) e o que foi faturado na nota fiscal (`invoiced`).
- **Curva ABC**: Classificação de itens por relevância de consumo financeiro (A: ~80% do valor, B: ~15%, C: ~5%).
