# 🔴 KS FoodOps — Relatório de Auditoria de Segurança Adversarial

**Data**: 2026-08-14  
**Auditor**: Engenheiro Sênior de AppSec (White-Box)  
**Repositório**: KS FoodOps — Multi-tenant SaaS para food-service  
**Escopo**: Codebase completo (backend Python/FastAPI, infra Docker, migrations, testes)  
**Migration head**: `1082c0f19162` (phase7_intelligence)

---

## 1. Sumário Executivo

O KS FoodOps apresenta uma **arquitetura multi-tenant fundamentada** com RLS no PostgreSQL, separação de roles (owner vs app), e invariantes de domínio documentadas. Contudo, a auditoria identifica **vulnerabilidades CRITICAL e HIGH** que impedem qualquer deployment de produção na forma atual. O risco predominante é a **ausência total de autenticação real** (JWT mock) combinada com **infraestrutura de rede completamente aberta** (Redis e PostgreSQL sem autenticação/rede dedicada).

### Nota Geral de Postura de Segurança: **D**

**Justificativa**: Embora as fundações arquiteturais (RLS, Decimal, ledger imutável, separação de concerns) estejam corretas, as camadas de proteção de runtime (autenticação, transporte, rede, observabilidade de segurança) estão ausentes ou são stubs de desenvolvimento. O sistema não pode ser exposto à internet no estado atual sem risco de comprometimento total.

### Top 5 Riscos Imediatos

| # | Risco | Severidade |
|---|-------|-----------|
| 1 | JWT é um mock — qualquer string forja identidade de qualquer usuário | CRITICAL |
| 2 | Membership check RLS chicken-and-egg — consulta sob RLS ativa pode falhar silenciosamente | CRITICAL |
| 3 | Redis exposto em `0.0.0.0:6379` sem autenticação — acesso direto ao broker | HIGH |
| 4 | PostgreSQL exposto em `0.0.0.0:5433` com credenciais hardcoded | HIGH |
| 5 | Ausência total de CORS, rate limiting e security headers | HIGH |

---

## 2. Registro Completo de Vulnerabilidades

---

### [VULN-001] Autenticação JWT é um Mock — Qualquer String Forja Identidade

- **Severity**: CRITICAL
- **CVSS estimado**: 9.8
- **Categoria**: Broken Authentication (CWE-287)
- **Superfície**: 1 — Autenticação
- **CWE**: CWE-287 (Improper Authentication)
- **Arquivos e linhas**: [`auth.py:17-24`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/packages/security/auth.py#L17-L24)
- **Invariantes afetadas**: Todas — acesso total ao sistema
- **Pré-condições**: Atacante pode enviar requests HTTP à API

**Descrição**: A função `decode_jwt()` não valida assinaturas, expiração, issuer ou audience. Ela retorna `TokenPayload(sub=token)` diretamente — qualquer string enviada como Bearer token é aceita como user_id.

**Prova de conceito**:
```http
GET /any-endpoint HTTP/1.1
Authorization: Bearer admin-user-id-here
X-Tenant-Id: <target-tenant-uuid>
```
O atacante precisa apenas conhecer (ou adivinhar) um `user_id` válido que tenha membership no tenant alvo.

**Impacto**: Impersonação de qualquer usuário. Se o atacante descobrir um user_id com role `admin`, obtém controle total sobre os dados do tenant.

**Evidência de código**:
```python
# auth.py L17-24
def decode_jwt(token: str) -> TokenPayload:
    return TokenPayload(sub=token)  # Aceita QUALQUER string
```

**Contraevidências/limitações**: O código contém comentários indicando que é um mock para desenvolvimento (L18-20). O membership check em `dependencies.py:41-46` ainda requer que o `sub` corresponda a um `user_id` real com membership. Portanto, um atacante precisa de um user_id válido, não apenas qualquer string.

**Remediação específica**: Implementar validação JWT real usando `python-jose` ou `PyJWT`:
- Validar assinatura com chave pública do IDP
- Verificar `exp`, `iss`, `aud`
- Rejeitar tokens expirados
- Adicionar `python-jose[cryptography]` ao `requirements.txt`
- Arquivo: `packages/security/auth.py`

**Testes de regressão recomendados**:
- Token expirado → 401
- Token com assinatura inválida → 401
- Token sem campo `sub` → 401
- Token válido com user inexistente → 403

**Prioridade**: Immediate

---

### [VULN-002] Membership Check Sob RLS — Chicken-and-Egg Problem

- **Severity**: CRITICAL
- **CVSS estimado**: 9.1
- **Categoria**: Broken Access Control (CWE-284)
- **Superfície**: 2 — Multi-tenant / RLS
- **CWE**: CWE-284 (Improper Access Control)
- **Arquivos e linhas**: [`dependencies.py:29-71`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/packages/security/dependencies.py#L29-L71)
- **Invariantes afetadas**: INV-012, INV-013
- **Pré-condições**: RLS ativa na tabela `tenant_memberships`

**Descrição**: Em `get_secure_session()`, a verificação de membership (L41-46) ocorre **antes** do `set_config` (L59-62). Contudo, a session já foi criada via `get_db()` que usa `async_session_maker` conectado ao engine do **app role** (`ksfoodops_app`). A tabela `tenant_memberships` tem RLS FORCE habilitado (migration `313a6cd2aed7` L90-92). Como o `set_config` ainda não foi executado, `current_setting('app.current_tenant_id', true)` retorna `''` (vazio) → `NULLIF('', '')` = `NULL` → a condição `tenant_id = NULL` é **sempre falsa** → **nenhuma row é retornada** → o membership check falha para todos.

**Prova de conceito**: Qualquer request autenticada com a role `ksfoodops_app` deveria falhar com 403 porque a query de membership retorna 0 rows sob RLS sem contexto definido.

**Impacto**: Se este é o comportamento real em runtime, **nenhum usuário legítimo consegue acessar a API** (denial of service por design). Se algum workaround existe (como o engine usar a role owner), então a RLS está sendo bypassed na camada de membership, o que abre um vetor de escalação.

**Evidência de código**:
```python
# dependencies.py L41-46 — membership query ANTES do set_config
stmt = select(TenantMembership).where(
    TenantMembership.user_id == user.sub,
    TenantMembership.tenant_id == tenant_id
)
# Sob RLS da tabela tenant_memberships, sem contexto: 0 rows retornadas

# L59-62 — set_config SÓ ACONTECE DEPOIS
await session.execute(
    text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
    {"tenant_id": str(tenant_id)}
)
```

**Contraevidências/limitações**: Se o `DATABASE_URL` default em `database.py:9-12` apontar para o owner role em vez do app role por erro de configuração, as queries funcionariam mas sem proteção RLS. Verificar qual engine é realmente usado em runtime é necessário — o default fallback é `ksfoodops_app`, mas `docker-compose.yml` L32 injeta `ks_owner`. **ISTO É OUTRA VULNERABILIDADE** (ver VULN-003).

**Remediação específica**: 
1. Executar a query de membership com uma connection/session separada que usa o owner role, OU
2. Remover RLS da tabela `tenant_memberships` (a query já filtra por user_id + tenant_id), OU  
3. Fazer `set_config` com um valor de "lookup" antes da membership query, e re-configurar depois.

**Testes de regressão recomendados**:
- Membership check funciona com app role e RLS
- Request com tenant_id válido + user válido → 200
- Request com tenant_id válido + user inválido → 403

**Prioridade**: Immediate

---

### [VULN-003] Docker Compose Injeta Owner Role no API Container

- **Severity**: CRITICAL
- **CVSS estimado**: 9.0
- **Categoria**: Privilege Escalation / Misconfiguration (CWE-250)
- **Superfície**: 2 — Multi-tenant / RLS + 8 — Segredos
- **CWE**: CWE-250 (Execution with Unnecessary Privileges)
- **Arquivos e linhas**: [`docker-compose.yml:32`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/docker-compose.yml#L32), [`database.py:9-12`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/packages/tenant/database.py#L9-L12)
- **Invariantes afetadas**: INV-014 (Runtime role não possui BYPASSRLS)
- **Pré-condições**: Docker Compose em uso

**Descrição**: O `docker-compose.yml` L32 define `DATABASE_URL=postgresql+asyncpg://ks_owner:ks_password@db:5432/ks_foodops` para o serviço `api`. O role `ks_owner` é o **owner das tabelas** e migrations. Na migration `313a6cd2aed7` L68, `ksfoodops_app` é criado com `NOBYPASSRLS`, mas `ks_owner`, sendo o dono das tabelas, **bypassa RLS automaticamente** (PostgreSQL: table owners bypass their own RLS policies a menos que FORCE ROW LEVEL SECURITY esteja ativo. Com FORCE, o owner também é filtrado, MAS o owner pode fazer `ALTER TABLE ... DISABLE ROW LEVEL SECURITY`). 

O comportamento exato depende de se FORCE está configurado:
- FORCE ROW LEVEL SECURITY **está** ativo em todas as tabelas ✓ — portanto o owner também é filtrado pelas policies
- Mas o owner pode **desabilitar** RLS a qualquer momento, e qualquer SQLi ou code injection permitiria isso

O problema principal é que o runtime usa o owner role em vez do app role, violando o princípio do menor privilégio e a invariante INV-014.

**Evidência de código**:
```yaml
# docker-compose.yml L32
DATABASE_URL=postgresql+asyncpg://ks_owner:ks_password@db:5432/ks_foodops
```
```python
# database.py L9-12 — fallback usa o app role, mas docker-compose sobrescreve
DATABASE_URL = os.environ.get("DATABASE_URL", 
    "postgresql+asyncpg://ksfoodops_app:app_password@localhost:5433/ks_foodops")
```

**Impacto**: Em caso de SQL injection, o atacante pode desabilitar RLS e acessar dados de todos os tenants.

**Remediação específica**: Alterar `docker-compose.yml` L32 para usar `ksfoodops_app`:
```yaml
DATABASE_URL=postgresql+asyncpg://ksfoodops_app:app_password@db:5432/ks_foodops
```
E resolver VULN-002 antes (chicken-and-egg do membership check).

**Prioridade**: Immediate

---

### [VULN-004] Redis Exposto Sem Autenticação

- **Severity**: HIGH
- **CVSS estimado**: 8.6
- **Categoria**: Security Misconfiguration (CWE-306)
- **Superfície**: 9 — Containers e Infraestrutura
- **CWE**: CWE-306 (Missing Authentication for Critical Function)
- **Arquivos e linhas**: [`docker-compose.yml:20-23`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/docker-compose.yml#L20-L23), [`worker.py:4`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/apps/worker/worker.py#L4)
- **Invariantes afetadas**: N/A (Redis não é fonte de verdade, mas broker de tarefas)
- **Pré-condições**: Acesso à rede onde Docker está executando

**Descrição**: Redis é exposto em `0.0.0.0:6379` sem senha (`requirepass` não configurado) e sem bind a localhost. Qualquer host na rede pode conectar.

**Prova de conceito**:
```bash
redis-cli -h <host-ip> -p 6379 KEYS "*"
redis-cli -h <host-ip> -p 6379 FLUSHALL  # DoS - apaga todas as tasks
```

**Impacto**: 
- DoS via FLUSHALL (limpar queue de tarefas Celery)
- Injeção de tarefas Celery maliciosas
- Se Celery `accept_content` incluísse `pickle`, permitiria RCE (atualmente limitado a JSON ✓)
- Exfiltração de resultados de tarefas

**Remediação específica**: 
1. Adicionar `command: redis-server --requirepass <strong-password>` ao serviço redis
2. Remover mapeamento de porta `6379:6379` (containers se comunicam pela rede interna Docker)
3. Atualizar `CELERY_BROKER_URL` e `REDIS_URL` com password

**Prioridade**: Immediate

---

### [VULN-005] PostgreSQL Exposto com Credenciais Hardcoded

- **Severity**: HIGH
- **CVSS estimado**: 8.6
- **Categoria**: Security Misconfiguration (CWE-798)
- **Superfície**: 8 — Segredos + 9 — Infra
- **CWE**: CWE-798 (Use of Hard-coded Credentials)
- **Arquivos e linhas**: [`docker-compose.yml:7-9`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/docker-compose.yml#L7-L9), [`docker-compose.yml:32-33`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/docker-compose.yml#L32-L33), [`database.py:9-17`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/packages/tenant/database.py#L9-L17), [`313a6cd2aed7:68`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/alembic/versions/313a6cd2aed7_initial_tenant_models_with_rls.py#L68)
- **Invariantes afetadas**: Todas
- **Pré-condições**: Acesso à rede onde Docker está executando

**Descrição**: 
1. PostgreSQL exposto em `0.0.0.0:5433` com senha `ks_password` (owner) e `app_password` (app role)
2. Essas senhas estão hardcoded em 4 locais diferentes no código-fonte
3. A senha do app role está hardcoded na migration SQL (`CREATE ROLE ... PASSWORD 'app_password'`)
4. Não existe arquivo `.env` no backend (apenas o Next.js tem `.gitignore` com `.env*`)
5. Não existe `.gitignore` no diretório raiz do backend

**Impacto**: Acesso direto ao banco de dados com todas as permissões do owner (DDL, DML, DROP).

**Remediação específica**: 
1. Criar `.gitignore` na raiz com `.env*`
2. Criar `.env` com variáveis sensíveis
3. Remover senhas do `docker-compose.yml` (usar `${DB_PASSWORD}`)
4. Remover porta exposta do PostgreSQL (manter comunicação apenas via rede Docker interna)
5. Alterar senha do app role criada na migration

**Prioridade**: Immediate

---

### [VULN-006] Ausência de CORS, Rate Limiting e Security Headers

- **Severity**: HIGH
- **CVSS estimado**: 7.5
- **Categoria**: Security Misconfiguration (CWE-942, CWE-770)
- **Superfície**: 7 — API
- **CWE**: CWE-942 (Overly Permissive CORS), CWE-770 (Allocation without Limits)
- **Arquivos e linhas**: [`main.py:1-20`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/apps/api/main.py#L1-L20)
- **Pré-condições**: API acessível pela internet

**Descrição**: Nenhuma configuração de CORS, rate limiting ou security headers foi encontrada em todo o codebase.

**Prova de conceito**:
```javascript
// De qualquer origin, via browser
fetch("http://api.ksfoodops.com/health")
  .then(r => r.json())
  .then(console.log) // Funciona de qualquer domínio
```
```bash
# Rate limiting inexistente — brute force de user_ids
for i in $(seq 1 10000); do
  curl -H "Authorization: Bearer user-$i" -H "X-Tenant-Id: <uuid>" http://api/endpoint
done
```

**Impacto**: 
- **CORS**: CSRF-like attacks de qualquer origin
- **Rate limiting**: Brute force, DoS, enumeração
- **Headers**: Clickjacking (sem X-Frame-Options), MIME sniffing, sem HSTS

**Remediação específica**: Em `apps/api/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["https://app.ksfoodops.com"], ...)
# + slowapi ou similar para rate limiting
# + middleware de security headers
```

**Prioridade**: Immediate

---

### [VULN-007] Swagger/Redoc Expostos em Produção

- **Severity**: MEDIUM
- **CVSS estimado**: 5.3
- **Categoria**: Information Disclosure (CWE-200)
- **Superfície**: 7 — API
- **CWE**: CWE-200 (Information Exposure)
- **Arquivos e linhas**: [`main.py:10`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/apps/api/main.py#L10)
- **Pré-condições**: API acessível

**Descrição**: FastAPI gera automaticamente `/docs` (Swagger UI) e `/redoc`. O código não desabilita estas rotas para produção.

**Impacto**: Atacante mapeia todos os endpoints, parâmetros, schemas de request/response — reduz drasticamente o esforço de reconhecimento.

**Remediação**: `FastAPI(docs_url=None, redoc_url=None)` em produção, habilitado condicionalmente via variável de ambiente.

**Prioridade**: Next Sprint

---

### [VULN-008] Container Roda como Root

- **Severity**: MEDIUM
- **CVSS estimado**: 6.7
- **Categoria**: Privilege Escalation (CWE-250)
- **Superfície**: 9 — Containers
- **CWE**: CWE-250 (Execution with Unnecessary Privileges)
- **Arquivos e linhas**: [`apps/api/Dockerfile:1-14`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/apps/api/Dockerfile#L1-L14), [`apps/worker/Dockerfile:1-14`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/apps/worker/Dockerfile#L1-L14)

**Descrição**: Ambos os Dockerfiles não contêm diretiva `USER`. O processo roda como root dentro do container.

**Impacto**: Em caso de RCE via vulnerability na app ou dependência, o atacante tem root no container, facilitando container escape.

**Remediação**: Adicionar ao final dos Dockerfiles:
```dockerfile
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

**Prioridade**: Next Sprint

---

### [VULN-009] Ausência de Imutabilidade Enforced no Banco para Movimentos POSTED

- **Severity**: HIGH
- **CVSS estimado**: 7.5
- **Categoria**: Business Logic Flaw (CWE-284)
- **Superfície**: 5 — Invariantes de Domínio
- **CWE**: CWE-284 (Improper Access Control)
- **Arquivos e linhas**: Todas as migrations — nenhuma contém `CHECK` constraints, `TRIGGER` ou `RULE` que impeça `UPDATE`/`DELETE` em rows com `status = 'POSTED'`
- **Invariantes afetadas**: INV-001, INV-002, INV-003, INV-004, INV-020

**Descrição**: As invariantes INV-001 (movimentos POSTED imutáveis), INV-003 (nunca deletar POSTED), INV-004 (CLOSED imutável) e INV-020 (receita PUBLISHED imutável) são enforced **apenas no application code** (`service.py` verifica status antes de operar). Não existe nenhum `CHECK constraint`, `TRIGGER` ou `RULE` no PostgreSQL que impeça `UPDATE` ou `DELETE` diretamente no banco.

**Prova de conceito**: Se um atacante obtiver acesso SQL direto (via VULN-005), ou se existir um bug no application code que permita bypass:
```sql
UPDATE stock_movements SET status = 'DRAFT' WHERE id = '<posted-movement-id>';
DELETE FROM stock_ledger_entries WHERE movement_id = '<posted-movement-id>';
```

**Impacto**: Adulteração do ledger financeiro, destruição de audit trail, manipulação de custos e estoque.

**Remediação**: Criar triggers no PostgreSQL:
```sql
CREATE FUNCTION prevent_posted_mutation() RETURNS TRIGGER AS $$
BEGIN
  IF OLD.status = 'POSTED' THEN
    RAISE EXCEPTION 'Cannot modify a POSTED movement';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_stock_movements_immutable 
  BEFORE UPDATE OR DELETE ON stock_movements 
  FOR EACH ROW EXECUTE FUNCTION prevent_posted_mutation();
```
Similar para `inventory_sessions` (CLOSED) e `recipe_versions` (PUBLISHED).

**Prioridade**: Immediate

---

### [VULN-010] Ausência de Logging e Auditoria de Eventos de Segurança

- **Severity**: MEDIUM
- **CVSS estimado**: 5.0
- **Categoria**: Insufficient Logging & Monitoring (CWE-778)
- **Superfície**: 11 — Exposição de Dados
- **CWE**: CWE-778 (Insufficient Logging)
- **Arquivos e linhas**: Nenhum arquivo no codebase contém `import logging` ou `logger`
- **Invariantes afetadas**: N/A

**Descrição**: Não há nenhuma forma de logging estruturado em todo o backend. Nenhuma chamada de `logging.info/warning/error` existe. O OpenTelemetry está no `requirements.txt` mas não está instrumentado no `main.py`.

**Impacto**: 
- Impossível detectar ataques em andamento
- Sem audit trail de operações sensíveis (login, membership changes, posting, inventory close)
- Sem capacidade de forensics pós-incidente

**Remediação**: Implementar structured logging com:
- Request ID middleware
- Log de tentativas de autenticação falhas
- Log de violações de autorização
- Log de operações críticas de domínio (post, close, reverse)

**Prioridade**: Next Sprint

---

### [VULN-011] RLS Policy Tipo USING-Only — Permite Inserção Cross-Tenant

- **Severity**: HIGH  
- **CVSS estimado**: 8.1
- **Categoria**: Broken Access Control (CWE-863)
- **Superfície**: 2 — Multi-tenant / RLS
- **CWE**: CWE-863 (Incorrect Authorization)
- **Arquivos e linhas**: Todas as migrations que criam policies RLS (e.g., [`313a6cd2aed7:82`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/alembic/versions/313a6cd2aed7_initial_tenant_models_with_rls.py#L82))
- **Invariantes afetadas**: INV-012, INV-013

**Descrição**: Todas as policies RLS usam apenas cláusula `USING`:
```sql
CREATE POLICY tenant_isolation_policy ON <table> 
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```
Sem cláusula `WITH CHECK`, o PostgreSQL usa a mesma expressão `USING` para `INSERT` e `UPDATE`. Porém, isto significa que um `INSERT` com um `tenant_id` **diferente** do contexto RLS será bloqueado pelo `USING` (que também serve como `WITH CHECK` implícito quando não especificado). Até aqui OK.

**MAS**: O `tenant_id` na cláusula USING é avaliado contra o **row sendo inserido**. Se o atacante definir `set_config('app.current_tenant_id', 'TENANT_A')` mas enviar um INSERT com `tenant_id = 'TENANT_A'`, passa. Se enviar com `tenant_id = 'TENANT_B'`, falha. Este é o comportamento correto.

**Risco real**: O risco está no `UPDATE`. Com `USING` only:
- `USING` filtra quais rows o role pode VER e ATUALIZAR
- Um UPDATE que MUDA o `tenant_id` de uma row para outro valor passaria a `USING` (a row original pertence ao tenant correto), mas escreveria um `tenant_id` diferente — efetivamente "roubando" a row para outro tenant

**Prova de conceito**:
```sql
SET app.current_tenant_id = '<tenant-a-id>';
-- A row pertence a Tenant A, então USING permite
UPDATE skus SET tenant_id = '<tenant-b-id>' WHERE id = '<sku-id>';
-- Sem WITH CHECK, o UPDATE passa! A row agora pertence a Tenant B
```

**Impacto**: Corrupção de dados cross-tenant. Uma row pode ser movida de um tenant para outro.

**Remediação**: Adicionar `WITH CHECK` explícito em todas as policies:
```sql
CREATE POLICY tenant_isolation_policy ON <table>
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
```

**Prioridade**: Immediate

---

### [VULN-012] `tenants` Table Sem RLS

- **Severity**: MEDIUM
- **CVSS estimado**: 5.5
- **Categoria**: Broken Access Control (CWE-862)
- **Superfície**: 2 — Multi-tenant / RLS
- **CWE**: CWE-862 (Missing Authorization)
- **Arquivos e linhas**: [`313a6cd2aed7:24-30`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/alembic/versions/313a6cd2aed7_initial_tenant_models_with_rls.py#L24-L30) — `tenants` table criada sem RLS
- **Invariantes afetadas**: INV-013

**Descrição**: A tabela `tenants` não tem RLS habilitado em nenhuma migration. O runtime role pode ler/escrever em TODOS os registros de tenants.

**Impacto**: Enumeração de todos os tenants do sistema (nomes, IDs). Potencial criação ou modificação de tenants por qualquer usuário autenticado.

**Contraevidências**: `tenants` não tem `tenant_id` (é a raiz), então RLS convencional não se aplica. Contudo, o acesso deveria ser restrito a admins do sistema.

**Remediação**: Implementar restrição de acesso à tabela `tenants` (GRANT mais restritivo, ou RLS baseada em role) ou garantir que nenhum endpoint exponha queries sobre `tenants` sem autorização admin.

**Prioridade**: Next Sprint

---

### [VULN-013] Stubs Não Implementados em `rls.py`

- **Severity**: LOW
- **CVSS estimado**: 3.0
- **Categoria**: Incomplete Implementation (CWE-1188)
- **Superfície**: 2 — Multi-tenant / RLS
- **CWE**: CWE-1188 (Insecure Default Initialization)
- **Arquivos e linhas**: [`rls.py:25-49`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/packages/tenant/rls.py#L25-L49)
- **Invariantes afetadas**: INV-013

**Descrição**: `set_tenant_context_in_db()` e `apply_rls_to_connection()` estão implementados como `pass`. O mecanismo real de RLS está em `dependencies.py` via `set_config` direto na session, tornando estes stubs dead code. O risco é que um desenvolvedor futuro use estas funções esperando que elas funcionem.

**Remediação**: Remover as funções ou implementá-las. Adicionar docstrings indicando que são deprecated/unused.

**Prioridade**: Backlog

---

### [VULN-014] Queries de Service Sem Tenant Filter em Algumas Paths

- **Severity**: MEDIUM
- **CVSS estimado**: 6.5
- **Categoria**: Broken Access Control (CWE-863)
- **Superfície**: 2 — Multi-tenant / RLS
- **CWE**: CWE-863 (Incorrect Authorization)
- **Arquivos e linhas**: 
  - [`inventory/service.py:46`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/inventory/service.py#L46) — `GoodsReceiptLine` query sem `tenant_id`
  - [`inventory/service.py:157`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/inventory/service.py#L157) — `InventoryCountLine` query sem `tenant_id`
  - [`purchasing/service.py:80-93`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/purchasing/service.py#L80-L93) — `PurchaseOrderLine` e `GoodsReceiptLine` sums sem `tenant_id`
  - [`recipes/service.py:123-126`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/recipes/service.py) — `RecipeIngredient` query sem `tenant_id`
  - [`sales/service.py:92-95`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/sales/service.py#L92-L95) — `TheoreticalConsumption` query sem `tenant_id`
- **Invariantes afetadas**: INV-012

**Descrição**: Diversas queries ORM nos services filtram por ID de entidade (e.g., `receipt_id`, `session_id`) mas omitem o filtro `tenant_id`. A defesa em profundidade depende inteiramente do RLS ativo. Se RLS falhar (ver VULN-003), estas queries retornariam dados cross-tenant.

**Contraevidências**: O RLS no banco **é** a defesa. Estas queries são executadas dentro de uma session com `set_config` ativo. Desde que o RLS esteja funcionando e o engine use o app role, os dados estão protegidos. Porém, é uma violação do princípio de defense-in-depth.

**Remediação**: Adicionar `.where(Table.tenant_id == tenant_id)` em todas as queries de service como segunda camada de proteção.

**Prioridade**: Next Sprint

---

### [VULN-015] Ausência de Validação de Input nos Services

- **Severity**: MEDIUM
- **CVSS estimado**: 6.3
- **Categoria**: Improper Input Validation (CWE-20)
- **Superfície**: 7 — API + 5 — Lógica de Negócio
- **CWE**: CWE-20 (Improper Input Validation)
- **Arquivos e linhas**: Todos os services (nenhum usa Pydantic schemas de input)
- **Invariantes afetadas**: INV-011

**Descrição**: Os services recebem dados como `Dict[str, Any]` ou `List[Dict]` sem validação Pydantic:
- `purchasing/service.py:22` — `receipt_lines_data: List[Dict]`
- `sales/service.py:18` — `sales_data: List[Dict[str, Any]]`
- `documents/service.py:39` — `xml_content: str`

Valores negativos, zeros, strings em campos numéricos, ou tipos inesperados não são validados antes de chegarem ao banco.

**Prova de conceito**: Um atacante pode enviar `quantity: -1000` em um goods receipt, criando estoque negativo (bypass da invariante INV-006/INV-007).

**Impacto**: 
- Estoque negativo
- Valores financeiros negativos ou zerados
- Potential division by zero em cálculos de custo médio (`balance.total_value / balance.quantity`)

**Remediação**: Criar Pydantic models para todos os inputs de service. Validar `quantity > 0`, `unit_price >= 0`, etc. Nenhum Pydantic model de input existe além de `TokenPayload`.

**Prioridade**: Next Sprint

---

### [VULN-016] Docker Network — Sem Segmentação

- **Severity**: MEDIUM
- **CVSS estimado**: 5.5
- **Categoria**: Network Segmentation (CWE-923)
- **Superfície**: 9 — Containers
- **CWE**: CWE-923 (Improper Restriction of Communication Channel)
- **Arquivos e linhas**: [`docker-compose.yml:1-76`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/docker-compose.yml#L1-L76)

**Descrição**: Todos os 4 serviços (db, redis, api, worker) compartilham a mesma rede Docker default. Não há redes separadas (e.g., `frontend`, `backend`, `data`). O container `web` pode acessar diretamente o PostgreSQL e o Redis.

**Remediação**: Criar redes separadas no `docker-compose.yml`:
- `data-net`: db + api + worker
- `broker-net`: redis + api + worker
- `web-net`: web + api

**Prioridade**: Next Sprint

---

### [VULN-017] Sem Limites de Recursos nos Containers

- **Severity**: LOW
- **CVSS estimado**: 4.0
- **Categoria**: Denial of Service (CWE-400)
- **Superfície**: 9 — Containers
- **CWE**: CWE-400 (Uncontrolled Resource Consumption)
- **Arquivos e linhas**: [`docker-compose.yml`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/docker-compose.yml)

**Descrição**: Nenhum container tem `mem_limit`, `cpus`, ou `deploy.resources` configurado. Um memory leak ou OOM pode derrubar o host.

**Prioridade**: Backlog

---

### [VULN-018] NFE Adapter é Stub — Não Parseia XML Real

- **Severity**: INFORMATIONAL (condicional a HIGH quando implementado)
- **CVSS estimado**: N/A (stub)
- **Categoria**: Potential XXE / Injection (CWE-611)
- **Superfície**: 12 — Documentos e IA
- **CWE**: CWE-611 (Improper Restriction of XML External Entity Reference)
- **Arquivos e linhas**: [`documents/service.py:13-32`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/documents/service.py#L13-L32)

**Descrição**: O `NFEAdapter.parse()` é um stub que retorna dados hardcoded. Quando a implementação real for feita, o parsing de XML de NF-e **deve** desabilitar DTD e external entities para evitar XXE.

**Remediação futura**: Usar `defusedxml` ou configurar `lxml` com `resolve_entities=False`.

**Prioridade**: Backlog (quando implementação real começar)

---

### [VULN-019] `file_path` no RawDocument — Potencial Path Traversal

- **Severity**: MEDIUM (condicional)
- **CVSS estimado**: 6.0
- **Categoria**: Path Traversal (CWE-22)
- **Superfície**: 12 — Documentos e IA
- **CWE**: CWE-22 (Improper Limitation of a Pathname)
- **Arquivos e linhas**: [`documents/models.py:12`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/documents/models.py#L12), [`documents/service.py:43`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/documents/service.py#L43)

**Descrição**: O campo `file_path` em `RawDocument` é um `String(500)` sem validação. Se o valor vier de input do usuário, um path como `../../etc/passwd` poderia ser armazenado e potencialmente usado para ler arquivos do sistema.

**Contraevidências**: No código atual, `file_path` é passado pelo caller (`ingest_nfe_xml`), não diretamente do request body. Depende da implementação do endpoint.

**Remediação**: Validar e sanitizar `file_path` — rejeitar `..`, paths absolutos, e caracteres especiais. Usar presigned URLs (conforme AGENTS.md).

**Prioridade**: Next Sprint

---

### [VULN-020] Balance Projection Race Condition em Criação

- **Severity**: MEDIUM
- **CVSS estimado**: 5.9
- **Categoria**: Race Condition (CWE-362)
- **Superfície**: 6 — Concorrência
- **CWE**: CWE-362 (Concurrent Execution Using Shared Resource)
- **Arquivos e linhas**: [`inventory/service.py:90-105`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/inventory/service.py#L90-L105)

**Descrição**: No `post_goods_receipt`, quando o `StockBalanceProjection` não existe (L90), o código cria um novo e imediatamente re-busca com lock (L101-105). Contudo, entre duas requisições concorrentes para o mesmo SKU/location, ambas podem ver `balance = None`, ambas criam um novo balance (gerando duplicatas), e o re-fetch por ID não detecta o conflito.

**Contraevidências**: O `flush()` em L99 pode causar um `IntegrityError` se houver uma UNIQUE constraint em `(tenant_id, location_id, sku_id)` — mas **não existe tal constraint** nas migrations. Portanto, duplicatas são possíveis.

**Impacto**: Saldo duplicado para o mesmo SKU/location, levando a cálculos de estoque incorretos.

**Remediação**: Adicionar constraint UNIQUE em `stock_balance_projections (tenant_id, location_id, sku_id)`. Usar `INSERT ... ON CONFLICT DO UPDATE` ou advisory locks.

**Prioridade**: Next Sprint

---

### [VULN-021] `conftest.py` Usa `async_session_maker` Não Importado

- **Severity**: LOW
- **CVSS estimado**: 2.0
- **Categoria**: Code Quality (CWE-1188)
- **Superfície**: N/A (testes)
- **Arquivos e linhas**: [`tests/conftest.py:34`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/tests/conftest.py#L34)

**Descrição**: O fixture `db_session` referencia `async_session_maker` que não está importado no `conftest.py` (importa `OWNER_DATABASE_URL` e `DATABASE_URL`, mas usa `TestingSessionLocal` em L20-22 e `async_session_maker` em L34 que é undefined).

**Impacto**: Qualquer teste que use `db_session` fixture falha com `NameError`.

**Prioridade**: Backlog

---

### [VULN-022] Division by Zero em Custo Médio Ponderado

- **Severity**: MEDIUM
- **CVSS estimado**: 5.0
- **Categoria**: Business Logic (CWE-369)
- **Superfície**: 5 — Invariantes de Domínio
- **CWE**: CWE-369 (Divide By Zero)
- **Arquivos e linhas**: [`inventory/service.py:195`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/modules/inventory/service.py#L195)

**Descrição**: No `close_inventory_session`, o custo unitário é calculado como `balance.total_value / balance.quantity` (L195). Embora exista guard `balance.quantity > 0`, se por algum motivo (race condition, ajuste) o balance for exatamente 0 após operações parciais, a divisão por zero causará uma exceção não tratada.

**Contraevidências**: O guard `if balance and balance.quantity > 0` na L194 protege contra 0 no caso normal. Mas o `total_value` pode ser negativo, e `quantity` pode ser negativo por erros cumulativos.

**Remediação**: Usar `Decimal('0')` como fallback explícito quando `quantity <= 0`.

**Prioridade**: Backlog

---

### [VULN-023] Dependências Sem Lock File e Potencialmente Vulneráveis

- **Severity**: MEDIUM
- **CVSS estimado**: 5.0
- **Categoria**: Vulnerable Components (CWE-1104)
- **Superfície**: 10 — Dependências
- **CWE**: CWE-1104 (Use of Unmaintained Third Party Components)
- **Arquivos e linhas**: [`apps/api/requirements.txt`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/apps/api/requirements.txt), [`apps/worker/requirements.txt`](file:///c:/Users/pg287/Desktop/CARREIRA/KS_FoodOps/apps/worker/requirements.txt)

**Descrição**: 
1. Não existe `requirements.lock` ou `pip freeze` output
2. Dependências críticas ausentes: `python-jose` ou `PyJWT` (autenticação real), `python-multipart` (file uploads), `httpx` (HTTP client)
3. Pydantic não está explicitamente listado (vem como dependência do FastAPI)
4. Sem ferramenta de scanning de vulnerabilidades (safety, pip-audit, dependabot)

**Remediação**: 
1. Criar `requirements.lock` com `pip freeze`
2. Configurar GitHub Dependabot ou `pip-audit` no CI
3. Adicionar dependências ausentes para features de produção

**Prioridade**: Next Sprint

---

## 3. Tabela de Cobertura das 12 Superfícies

| # | Superfície | Status | Achados |
|---|-----------|--------|---------|
| 1 | Autenticação/JWT | ✅ Coberta | VULN-001 (CRITICAL) |
| 2 | Multi-tenant/RLS | ✅ Coberta | VULN-002, -003, -011, -012, -013, -014 |
| 3 | Autorização/RBAC | ✅ Coberta | Parcial — RBAC hardcoded funciona mas sem endpoint-level enforcement verificável (não há endpoints além de health) |
| 4 | SQL Injection/ORM | ✅ Coberta | Sem achados comprovados — todas as queries usam parameterized ORM ou `text()` com binds |
| 5 | Invariantes de Domínio | ✅ Coberta | VULN-009 (imutabilidade não enforced no DB), VULN-015 (validação), VULN-022 |
| 6 | Concorrência | ✅ Coberta | VULN-020 (balance race), locking adequado com `with_for_update()` na maioria |
| 7 | API Surface | ✅ Coberta | VULN-006 (CORS/rate/headers), VULN-007 (docs expostos) |
| 8 | Segredos/Config | ✅ Coberta | VULN-005 (hardcoded passwords) |
| 9 | Containers/Infra | ✅ Coberta | VULN-004, -008, -016, -017 |
| 10 | Dependências | ✅ Coberta | VULN-023 |
| 11 | Data Exposure | ✅ Coberta | VULN-010 (sem logging), VULN-007 (info disclosure) |
| 12 | Documentos/IA | ✅ Coberta | VULN-018 (XXE futuro), VULN-019 (path traversal) |

---

## 4. Árvore de Ataque — Encadeamentos Mais Perigosos

```mermaid
flowchart TD
    A["Atacante Externo"] --> B["Forja JWT Token<br/>(VULN-001: qualquer string = user_id)"]
    B --> C{"Conhece user_id válido?"}
    C -->|Sim| D["Impersona usuário com membership"]
    C -->|Não| E["Enumera user_ids via<br/>timing attack (VULN-006:<br/>sem rate limiting)"]
    E --> D
    
    D --> F["Acessa API como usuário legítimo"]
    F --> G{"Docker usa ks_owner?<br/>(VULN-003)"}
    
    G -->|Sim| H["RLS bypass pelo owner role<br/>→ Acesso a TODOS os tenants"]
    G -->|Não| I["RLS ativa mas membership<br/>check falha (VULN-002)"]
    
    H --> J["Exfiltração total de dados"]
    H --> K["Modifica POSTED movements<br/>(VULN-009: sem DB trigger)"]
    H --> L["Move rows entre tenants<br/>(VULN-011: sem WITH CHECK)"]
    
    A --> M["Acessa Redis direto<br/>(VULN-004: porta aberta,<br/>sem auth)"]
    M --> N["Injeta Celery tasks maliciosas"]
    M --> O["FLUSHALL → DoS"]
    
    A --> P["Acessa PostgreSQL direto<br/>(VULN-005: porta aberta,<br/>senhas hardcoded)"]
    P --> J
    P --> K

    style A fill:#e74c3c,color:#fff
    style H fill:#e74c3c,color:#fff
    style J fill:#e74c3c,color:#fff
    style K fill:#c0392b,color:#fff
    style L fill:#c0392b,color:#fff
    style P fill:#e74c3c,color:#fff
```

---

## 5. Checklist de Hardening

### 🔴 STOP THE BLEEDING — Bloquear antes de qualquer produção

- [ ] **Implementar JWT real** com validação de assinatura, expiration, issuer (VULN-001)
- [ ] **Resolver chicken-and-egg do membership check** sob RLS (VULN-002)
- [ ] **Alterar `docker-compose.yml`** para usar `ksfoodops_app` no API, não `ks_owner` (VULN-003)
- [ ] **Adicionar `WITH CHECK` em todas as RLS policies** (VULN-011)
- [ ] **Remover portas expostas** de Redis e PostgreSQL no docker-compose (VULN-004, VULN-005)
- [ ] **Adicionar autenticação ao Redis** (VULN-004)
- [ ] **Mover credenciais para `.env` / secrets manager** (VULN-005)
- [ ] **Adicionar DB triggers de imutabilidade** para POSTED/CLOSED/PUBLISHED (VULN-009)
- [ ] **Configurar CORS restritivo** (VULN-006)

### 🟠 HIGH PRIORITY — Corrigir no primeiro sprint

- [ ] **Adicionar rate limiting** (slowapi ou similar) (VULN-006)
- [ ] **Adicionar security headers** (X-Frame-Options, HSTS, CSP, X-Content-Type-Options) (VULN-006)
- [ ] **Desabilitar `/docs` e `/redoc` em produção** (VULN-007)
- [ ] **Adicionar `USER appuser` nos Dockerfiles** (VULN-008)
- [ ] **Adicionar tenant_id filter em todas as queries de service** como defense-in-depth (VULN-014)
- [ ] **Criar Pydantic models de input** para todos os services (VULN-015)
- [ ] **Adicionar UNIQUE constraint em `stock_balance_projections`** (VULN-020)

### 🟡 MEDIUM PRIORITY — Corrigir em 30 dias

- [ ] **Implementar structured logging** (VULN-010)
- [ ] **Criar redes Docker separadas** (VULN-016)
- [ ] **Validar `file_path` contra path traversal** (VULN-019)
- [ ] **Adicionar `pip-audit` / Dependabot ao CI** (VULN-023)
- [ ] **Adicionar `.gitignore` na raiz do backend** com `.env*`, `__pycache__`, etc.

### 🟢 DEFENSE IN DEPTH — Melhoria contínua

- [ ] **Limitar recursos dos containers** (mem_limit, cpus) (VULN-017)
- [ ] **Usar `defusedxml` quando implementar NF-e parser real** (VULN-018)
- [ ] **Corrigir conftest.py** (VULN-021)
- [ ] **Adicionar guard explícito para division by zero em CMV** (VULN-022)
- [ ] **Remover ou implementar stubs em `rls.py`** (VULN-013)
- [ ] **Restringir acesso à tabela `tenants`** (VULN-012)

---

## 6. Recomendações Arquiteturais

### 6.1 Autenticação
Adotar OIDC completo (Auth0, Cognito, Keycloak). O JWT mock é aceitável para dev local, mas deve ser feature-flagged e nunca deployado.

### 6.2 Defense-in-Depth para Multi-Tenancy
Implementar 3 camadas:
1. **Application layer**: membership check + tenant_id em toda query
2. **Database layer**: RLS com USING + WITH CHECK
3. **Network layer**: Separação de rede, TLS intra-serviço

### 6.3 Immutability at Database Layer
Criar triggers PostgreSQL que enforcem INV-001/003/004/020 no banco. Application code pode falhar; database constraints não.

### 6.4 Observabilidade de Segurança
Implementar structured logging + OpenTelemetry + alertas para:
- Tentativas de auth falha > N/minuto
- Mudanças de membership/role
- Operações de posting/closing
- Queries que retornam 0 rows inesperadamente (possível RLS block)

### 6.5 Secrets Management
Adotar Docker Secrets, HashiCorp Vault, ou AWS SSM Parameter Store. Zero credenciais em código-fonte.

---

## 7. Itens que Exigem Confirmação em Staging/Produção

| Item | Razão |
|------|-------|
| Qual role o engine realmente usa em runtime? | docker-compose injeta owner, mas env pode ser overridden |
| O membership check funciona com app role + RLS na tabela tenant_memberships? | Precisa teste end-to-end real |
| Existe network policy / firewall / VPC no ambiente de deploy? | docker-compose expõe portas mas deploy real pode ter proteção |
| Qual IDP será usado e qual é o JWKS endpoint? | Necessário para implementar VULN-001 fix |
| Existem backups e WAL archiving configurados? | Não verificável no codebase |

---

## 8. Apêndice

### 8.1 Arquivos Inspecionados (45 arquivos)

**Packages:**
- `packages/security/auth.py`
- `packages/security/dependencies.py`
- `packages/security/rbac.py`
- `packages/tenant/database.py`
- `packages/tenant/models.py`
- `packages/tenant/rls.py`

**Apps:**
- `apps/api/main.py`
- `apps/api/Dockerfile`
- `apps/api/requirements.txt`
- `apps/worker/worker.py`
- `apps/worker/tasks.py`
- `apps/worker/Dockerfile`
- `apps/worker/requirements.txt`

**Modules (models + services):**
- `modules/catalog/models.py`
- `modules/suppliers/models.py`
- `modules/purchasing/models.py`
- `modules/purchasing/service.py`
- `modules/inventory/models.py`
- `modules/inventory/service.py`
- `modules/recipes/models.py`
- `modules/recipes/service.py`
- `modules/sales/models.py`
- `modules/sales/service.py`
- `modules/documents/models.py`
- `modules/documents/service.py`
- `modules/intelligence/models.py`
- `modules/intelligence/service.py`
- `modules/costing/` (vazio)
- `modules/reporting/` (vazio)

**Migrations:**
- `alembic/env.py`
- `alembic.ini`
- `alembic/versions/313a6cd2aed7_initial_tenant_models_with_rls.py`
- `alembic/versions/cb34f9ef3350_phase2_inventory_slice.py`
- `alembic/versions/8fb1e626f7b0_phase3_inventory_sessions.py`
- `alembic/versions/167956c9214c_phase4_purchasing_reconciliation.py`
- `alembic/versions/215abd7f4dfc_phase5_recipes_and_sales.py`
- `alembic/versions/b809285d5d9f_phase6_document_ingestion.py`
- `alembic/versions/1082c0f19162_phase7_intelligence.py`
- `alembic/versions/265297f2f58c_fix_goods_receipt_line_fk.py`

**Tests:**
- `tests/conftest.py`
- `tests/test_health.py`
- `tests/integration/test_auth.py`
- `tests/integration/test_rls.py`

**Config:**
- `docker-compose.yml`
- `AGENTS.md`
- `docs/domain/INVARIANTS.md`
- `docs/ai/PROJECT_STATE.md`
- `docs/product/PRD.md`
- `docs/product/MVP_SCOPE.md`
- `docs/architecture/SECURITY.md` (vazio)
- `docs/architecture/MULTITENANCY.md` (vazio)

### 8.2 Buscas Executadas

- `grep -r "CORS"` → 0 resultados
- `grep -r "rate.limit|throttl|RateLimi"` → 0 resultados
- `grep -r "presigned|signed_url|upload"` → 0 resultados
- `grep -r "logging|logger"` (em apps/) → 0 resultados
- `grep -r "SECRET|KEY|PASSWORD|TOKEN"` → credenciais hardcoded encontradas
- `grep -r "ENABLE ROW LEVEL SECURITY"` → verificação de cobertura RLS
- `grep -r "get_db()"` → apenas definição em `database.py` (não usado diretamente por endpoints)
- `grep -r "CHECK|CONSTRAINT|TRIGGER"` → nenhum trigger ou check constraint customizado

### 8.3 Limitações da Auditoria

1. **Sem execução de testes**: Auditoria estática apenas. Os testes de integração não foram executados (requerem PostgreSQL real).
2. **Frontend não auditado em profundidade**: O Next.js app (`apps/web/`) não foi coberto pois está em estado inicial e não há endpoints de API expostos para analisar o fluxo completo.
3. **Sem scan de vulnerabilidades de dependências**: Não foi possível executar `pip-audit` ou `npm audit` de forma segura sem ambiente de runtime.
4. **Sem teste de penetração de rede**: Apenas análise de configuração Docker. O ambiente de deploy real pode ter camadas adicionais de proteção.
