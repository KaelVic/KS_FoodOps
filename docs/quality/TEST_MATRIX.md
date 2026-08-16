# Matriz de Testes & Qualidade — KS FoodOps

## 1. Pirâmide e Cobertura de Testes
O projeto adota uma matriz de testes rigorosa com foco em regras financeiras, RLS multi-tenant e ledger imutável.

| Tipo de Teste | Localização | Foco Principal | Ferramentas |
| :--- | :--- | :--- | :--- |
| **Unit & Integration** | `tests/integration/` | RLS, Ledger, Fechamento de Inventário, Fichas Técnicas, Reconciliação 3-Way, Ingestão de NF-e, Inteligência ABC | `pytest`, `pytest-asyncio`, `httpx` |
| **Imutabilidade DB** | Triggers PostgreSQL | Bloqueio de UPDATE/DELETE em registros `POSTED`, `CLOSED` e `PUBLISHED` | Migrations Alembic + Integration Tests |
| **E2E Web** | `apps/web/tests/` | Fluxos completos de tela (Login, Upload de NF-e, Contagem de Inventário) | `playwright` |
| **Frontend Static** | `apps/web/` | Tipagem estrita e linting de componentes e Server Actions | `tsc --noEmit`, `eslint` |

## 2. Testes Críticos Obrigatórios
1. `test_rls.py`: Isolamento cruzado entre inquilinos via RLS.
2. `test_inventory_ledger.py`: Imutabilidade e cálculo exato de Custo Médio Ponderado.
3. `test_inventory_session.py`: Fechamento com geração atômica de ajustes.
4. `test_nfe_upload_api.py`: Parsing e aprovação de NF-e sem perda de precisão fiscal.
5. `test_intelligence.py`: Cálculo determinístico de Curva ABC e Ponto de Pedido.
