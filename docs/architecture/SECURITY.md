# Arquitetura de Segurança — KS FoodOps

## 1. Princípios de Segurança
1. **Autenticação Server-Side Rígida**: Validação de tokens JWT assinados via PyJWT (HMAC-SHA256 ou RS256). Nunca confiar em informações de tenant vindas no corpo da requisição.
2. **Defesa em Profundidade para Multi-Tenancy**:
   - Camada 1: Dependência de autorização no FastAPI (`get_current_tenant_id` / `get_secure_session`).
   - Camada 2: PostgreSQL Row Level Security (`FORCE ROW LEVEL SECURITY`) com a role `ksfoodops_app` (sem permissão de `BYPASSRLS`).
3. **Imutabilidade Garantida por Triggers de Banco**:
   - `prevent_posted_mutation`: Impede `UPDATE` ou `DELETE` em movimentações de estoque com status `POSTED`.
   - `prevent_closed_mutation`: Impede alterações em sessões de inventário `CLOSED`.
   - `prevent_published_mutation`: Impede alterações em versões de receita `PUBLISHED`.
4. **Proteção contra Injeção de Documentos / Prompt-Injection**:
   - Textos de NF-e e PDFs são tratados estritamente como DADOS estruturados, nunca como instruções de sistema.
