# Máquinas de Estados do Domínio — KS FoodOps

## 1. Sessão de Inventário Físico (`InventorySession`)
```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> OPEN : Iniciar Sessão (Define cutoff_at)
    OPEN --> COUNTING : Iniciar Digitação Cega
    COUNTING --> REVIEW : Submeter Contagens
    REVIEW --> CLOSED : Fechar & Gerar Ajustes no Ledger
    REVIEW --> COUNTING : Recontar Itens Divergentes
    CLOSED --> [*]
```

## 2. Ordem de Compra (`PurchaseOrder`)
```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> APPROVED : Aprovação Gerencial
    APPROVED --> SENT : Envio ao Fornecedor
    SENT --> PARTIAL_RECEIPT : Recebimento Parcial
    PARTIAL_RECEIPT --> FULLY_RECEIVED : Recebimento Total
    SENT --> FULLY_RECEIVED : Recebimento Total
    DRAFT --> CANCELLED : Cancelar
    APPROVED --> CANCELLED : Cancelar
    FULLY_RECEIVED --> [*]
```

## 3. Ficha Técnica / Receita (`RecipeVersion`)
```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> PUBLISHED : Publicar Versão (Imutável)
    PUBLISHED --> ARCHIVED : Substituída por Nova Versão
    ARCHIVED --> [*]
```

## 4. Documento NF-e Ingerido (`DocumentExtraction`)
```mermaid
stateDiagram-v2
    [*] --> PENDING_REVIEW : Upload XML/OCR
    PENDING_REVIEW --> APPROVED : Revisão Humana de De-Para
    APPROVED --> PROCESSED : Gerada Nota de Entrada / GoodsReceipt
    PENDING_REVIEW --> REJECTED : Rejeitado pelo Operador
    PROCESSED --> [*]
```
