# Inventory Ledger Specification

## Immutability
All `POSTED` stock ledger entries are strictly immutable. They represent the exact truth of what happened at a specific point in time, using the exact conversion versions active at that moment.

## Components
1. **Stock Movements**: Represent a business event (Goods Receipt, Transfer, Adjustment, Reversal).
2. **Stock Ledger Entries**: Detailed lines per SKU showing exact quantity, unit cost, and a snapshot of the conversion version used. Contains `balance_after` as an audit trail.
3. **Stock Balance Projection**: A transactional projection updated synchronously during movement posting via strict database locks (`SELECT ... FOR UPDATE`). This is the only place queried for current stock balances.

## Concurrency
Posting logic uses row-level locking on `StockBalanceProjection` to guarantee race conditions do not corrupt stock balances during concurrent receipts or transfers.

## Physical Inventory Cutoffs
When an inventory session is closed, the *Expected Stock* is calculated strictly by summing all `StockLedgerEntry` values up to the session's `cutoff_at` timestamp. This allows operations to continue business as usual while counting; discrepancies are calculated against the exact historical point in time. Any variance identified generates an `INVENTORY_ADJUSTMENT` movement, posted at the current time.
