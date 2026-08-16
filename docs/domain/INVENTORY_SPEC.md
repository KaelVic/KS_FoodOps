# Especificação de Inventário Físico & Sessões — KS FoodOps

## 1. Ciclo de Vida da Sessão de Inventário
Uma sessão de inventário físico segue a máquina de estados:
```text
DRAFT -> OPEN -> COUNTING -> REVIEW -> CLOSED
```

## 2. Invariantes de Inventário
1. **Cutoff Timestamp**: Ao abrir a sessão, registra-se `cutoff_at`. O saldo esperado do sistema é congelado deterministicamente na data/hora do cutoff.
2. **Contagem Cega (Blind Counting)**: Durante o status `COUNTING`, operadores não visualizam a quantidade teórica esperada.
3. **Imutabilidade de Sessão Fechada (`INV-004`)**: Uma sessão com status `CLOSED` é 100% imutável no banco de dados, protegida por trigger PostgreSQL.
4. **Geração de Movimentos de Ajuste (`INV-005`)**: Ao fechar a sessão, o sistema calcula a divergência (`counted_quantity - expected_quantity`) e gera movimentações do tipo `INVENTORY_ADJUSTMENT` no Stock Ledger para igualar a projeção de saldo ao valor real apurado.
5. **Ajustes Pós-Fechamento**: Caso seja identificada falha em inventário já fechado, é proibido reabrir a sessão fechada. Uma nova sessão ou lançamento de ajuste individual deve ser efetuado.
