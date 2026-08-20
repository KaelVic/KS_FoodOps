# Next Task — ERP Hardening & Chain of Truth

**Status Atual: P0, P1 e P2 (Hardening do ERP e Camada Gerencial) 100% Concluídos** ✅

---

## 🎯 Prioridades de Hardening do ERP KS FoodOps

### P0 — Bloqueadores Críticos (CONCLUÍDOS ✅)
- [x] **P0.1**: Adicionar `commit()` explícito e tratamento transacional com rollback nos routers (`recipes.py`, `team.py`, `locations.py`, `suppliers.py`, `catalog.py`, `menu.py`).
- [x] **P0.2**: Aplicar RBAC com `require_permission` em todos os endpoints sensíveis (`inventory_sessions.py`, `inventory.py`, `purchasing.py`, `recipes.py`, `team.py`, `menu.py`, `catalog.py`, `locations.py`, `suppliers.py`).
- [x] **P0.3**: Validação de roles em memberships e proteção contra demotion do único admin (`packages/tenant/service.py`).
- [x] **P0.4**: Eliminação de fallbacks arbitrários (R$ 10) e criação de autoridade única de custo (`modules/costing/engine.py`).
- [x] **P0.5**: Correção de case sensitivity de status de PO (`APPROVED`, `SENT`, `PARTIAL_RECEIPT`) e join de localidade via `StockMovement` no Intelligence (`modules/intelligence/service.py`).
- [x] **P0.6**: Documentação honesta e atualizada em `PROJECT_STATE.md` e `NEXT_TASK.md`.

---

### P1 — Fechar Cadeia de Verdade do ERP (CONCLUÍDOS ✅)
- [x] **P1.1**: Adicionar identidade do autor (`actor_user_id`), `reason_code` e `notes` no `StockMovement` via migração Alembic (`7b8c9d0e1f2a`).
- [x] **P1.2**: Implementar fluxo de estorno/reversal de movimentos (`reverse_movement` em `InventoryService` e endpoint `POST /inventory/movements/{id}/reverse`).
- [x] **P1.3**: Fiação transversal do `AuditService.log_action()` em todas as operações de escrita críticas (fechamento de inventário, perda, recebimento de PO, aprovação de PO, reversão, publicação de receita, convites e alteração de papéis de equipe).
- [x] **P1.4**: Adicionar `location_id` nas vendas (`sales`) e ajustar relatório consolidado (`modules/reporting/consolidated.py`) para escopo consistente por unidade.

---

### P2 — Camada Gerencial de Nível Comercial (CONCLUÍDOS ✅)
- [x] **P2.1**: Estoque teórico perpétuo e divergência operacional por SKU (`modules/inventory/service.py` e endpoint `GET /inventory/theoretical-balances`).
- [x] **P2.2**: Insights gerenciais acionáveis (alertas de desvio de CMV por prato `GET /intelligence/dishes/cmv-drift`, projeção de ruptura com lead time real `GET /intelligence/stockout-risks` e Curva ABC com consumo teórico de vendas).
- [x] **P2.3**: Suíte de testes automatizados `test_p2_managerial_layer.py` 100% validada (11 testes no total entre P0, P1 e P2).