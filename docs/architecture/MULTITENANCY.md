# Arquitetura Multi-Tenancy — KS FoodOps

## 1. Modelo de Isolamento
O KS FoodOps utiliza isolamento lógico baseado em **PostgreSQL Row Level Security (RLS)** em todas as tabelas contendo dados de inquilinos.

## 2. Injeção de Contexto Transacional
O contexto do tenant é injetado a cada transação via variável de sessão PostgreSQL:
```sql
SELECT set_config('app.current_tenant_id', :tenant_id, true);
```
O terceiro parâmetro (`is_local = true`) garante que o contexto exista apenas no escopo da transação SQL atual, prevenindo vazamentos de contexto entre conexões reutilizadas no connection pool (`NullPool` ou `QueuePool`).

## 3. Política de RLS com WITH CHECK
Todas as políticas de RLS contêm cláusulas `USING` e `WITH CHECK`:
```sql
CREATE POLICY tenant_isolation_policy ON <tabela>
  FOR ALL
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```
Isso impede consultas cross-tenant e bloqueia tentativas de inserção ou atualização onde um atacante tente falsificar o `tenant_id`.
