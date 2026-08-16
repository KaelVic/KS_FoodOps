# Purchasing & 3-Way Reconciliation

## Purchase Orders
Purchase orders (POs) track intended purchases from external suppliers.
- **States**: `DRAFT` -> `APPROVED` -> `SENT` -> `PARTIAL_RECEIPT` -> `FULLY_RECEIVED` -> `CANCELLED`.
- **Lines**: `PurchaseOrderLine` tracks the `ordered_quantity` and agreed `unit_price`.

## Receiving & Stock Impact
Physical receiving is the *only* mechanism that increases inventory levels.
- Generating a `GoodsReceipt` against a PO automatically creates receiving lines linked to the PO lines.
- Receipt quantities update `StockLedgerEntry` using the `post_goods_receipt` idempotent inventory service.
- Supplier invoices do not affect inventory.

## 3-Way Reconciliation
To prevent overpaying or mismatching stock, KS FoodOps enforces line-by-line reconciliation.
- **`PurchaseReconciliation`**: A specialized table linking a `PurchaseOrderLine`, a `GoodsReceiptLine`, and a `SupplierInvoiceLine`.
- **Status Computation**:
  - `MATCHED`: ordered quantity == received quantity == invoiced quantity, AND ordered price == invoiced price.
  - `QUANTITY_DISCREPANCY`: ordered != received OR ordered != invoiced.
  - `PRICE_DISCREPANCY`: ordered price != invoiced price.
- **Historical Prices**: Prices on historical invoices and receipts are immutable and are never overwritten by new supplier catalog price updates.
