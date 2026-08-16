# Escopo do MVP — KS FoodOps

## 1. Módulos do MVP
O MVP do KS FoodOps é composto por 8 blocos funcionais rigorosamente integrados:

1. **Fundação Multi-Tenant & Segurança (Fase 1)**:
   - PostgreSQL RLS, RBAC por permissões `module.action`, autenticação JWT e isolamento transacional.
2. **Catálogo & Ledger de Estoque (Fase 2)**:
   - SKUs, UOMs, fatores de conversão versionados, movimentações append-only e cálculo de CMP (Custo Médio Ponderado).
3. **Inventário Físico & CMV Real (Fase 3)**:
   - Sessões de contagem com cutoff, fechamento imutável, apuração de divergências e geração automática de ajustes no Ledger.
4. **Purchasing & Reconciliação 3-Way (Fase 4)**:
   - Pedidos de compra, faturas de fornecedores, recebimento físico e conciliação de quantidades (`ordered`, `received`, `invoiced`).
5. **Ficha Técnica, Vendas & Teórico vs Real (Fase 5)**:
   - Receitas versionadas com fator de rendimento/perda, ingestão idempotente de PDVs e apuração de consumo teórico.
6. **Ingestão de NF-e & Documentos (Fase 6)**:
   - Parser SEFAZ XML v4.00, extração com retenção do arquivo original e sugestão de de-para com aprovação humana obrigatória.
7. **Inteligência Operacional Determinística (Fase 7)**:
   - Curva ABC, ponto de ressuprimento, dias de cobertura e alertas operacionais.
8. **Plataforma Web & Experiência de Usuário**:
   - Command Center, Inventário Radar, Purchasing Hub, Fichas Técnicas e Telas de Configuração em Next.js.
