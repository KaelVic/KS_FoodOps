# KS FoodOps Data Model

## Core Tenancy
- **Tenants, Business Units, Locations, Tenant Memberships**: Define the organizational hierarchy.
- **Row Level Security (RLS)**: Enforced via `tenant_id` on all operational tables.

## Catalog
- **UOM (Unit of Measure)**: Base measurement definitions.
- **Category**: Hierarchical grouping of SKUs.
- **SKU**: Internal item definitions linked to a base UOM.
- **SKUConversionVersion**: Point-in-time exact conversion factors between UOMs.

## Suppliers & Purchasing
- **Supplier**: External vendors.
- **SupplierSKU**: Vendor-specific item codes and default conversion paths.
- **SupplierSKUAlias**: OCR/Ingestion matching aliases.
- **PurchaseOrder / PurchaseOrderLine**: Intended purchases representing ordered quantity and price.
- **GoodsReceipt / GoodsReceiptLine**: Inbound physical purchasing documents linked to POs.
- **SupplierInvoice / SupplierInvoiceLine**: Financial documents representing vendor billing.
- **PurchaseReconciliation**: Explicit 3-way line-by-line reconciliation tracking (Ordered vs Received vs Invoiced).

## Recipes & Sales
- **Recipe / RecipeVersion**: Versioned production instructions for menu items.
- **RecipeIngredient**: Links recipe versions to component SKUs with expected loss percentages.
- **POSProductMapping**: Maps external point-of-sale product IDs to internal recipes.
- **SalesImport / Sale / SaleLine**: Idempotent records of external POS sales.

## Document Ingestion (AI/OCR)
- **RawDocument**: Safely stores the uploaded document hash, path, and type without ledger impact.
- **DocumentExtraction / DocumentExtractionLine**: Draft parsing candidates containing raw strings, normalized values, and confidence scores.
- **DocumentExtractionField**: Granular tracing for the source of each extracted field (AI vs OCR vs XML).

## Intelligence & Purchasing Suggestions
- **InventoryPolicy**: Configures baseline parameters like `min_stock`, `target_stock`, `lead_time_days`, and `abc_class`.
- **PurchaseSuggestion**: A deterministic calculation for suggested purchases based on targets, on-hand, and inbound.
- **OperationalAlert**: Records breaches of thresholds (e.g., STOCKOUT_RISK, PRICE_VARIANCE).

## Inventory Ledger
- **StockMovement**: The transactional envelope (RECEIPT, ADJUSTMENT, LOSS, etc.).
- **StockLedgerEntry**: Granular, immutable history of stock and cost changes.
- **StockBalanceProjection**: High-performance read model for current stock quantities and total value per location.
- **LossRecord**: Links to a StockMovement of type LOSS capturing reason and actor.
- **TheoreticalConsumption**: Computes exact ingredient requirements for sales based on historical recipes.

## Physical Inventory
- **InventorySession**: Represents a physical counting event with status workflow (DRAFT, OPEN, COUNTING, REVIEW, CLOSED) and cutoff logic.
- **InventorySessionLocation**: The subset of locations tracked within a specific session.
- **InventoryCountLine**: Discrete user-submitted counting lines.
- **InventoryCloseResult**: The persistent snapshot audit of exactly what the system expected vs what was counted at closure time, preserving variances securely.
