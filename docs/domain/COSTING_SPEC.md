# Costing Specification

## Exact Arithmetic
All costing calculations use exactly precise decimals (`NUMERIC(24,12)` in PostgreSQL, `Decimal` in Python).
Floating-point values (`float`, `DOUBLE PRECISION`) are strictly prohibited in the inventory and financial domains to prevent precision loss.

## Weighted Average Cost
The `StockBalanceProjection.total_value` is incremented by the exact receipt line value (`quantity * unit_price`). The unit cost of the SKU is logically `total_value / quantity`.

## Historical Accuracy
`StockLedgerEntry` records the exact `unit_cost` at the moment of the transaction. This ensures that historical reporting remains stable even if a supplier's future price or a recipe's composition changes.

## Operational Actual CMV
The Operational Actual CMV tracks the exact cost variance consumed by operations over a timeframe. 
It is strictly defined transactionally as:
`Actual Operational CMV = Opening Inventory Value + Net Receipts - Closing Inventory Value`
Negative adjustments from physical counts implicitly increase the CMV by reducing the Closing Inventory Value, correctly attributing lost stock to operational cost.
