# Deterministic Inventory Intelligence (Phase 7)

## Forecasting Gate
All intelligence algorithms in this phase are strictly deterministic. No statistical or Machine Learning methods are used to predict future usage.

## 1. ABC Classification
- **Metric**: Total historical consumption value (Quantity * Unit Cost).
- **Bucketing**: Cumulative percentage of total value.
  - **A**: Top 80%
  - **B**: Next 15% (80% - 95%)
  - **C**: Bottom 5% (> 95%)

## 2. Reorder Point (ROP) and Stockout Risk
- **Formula**: `ROP = (Daily Baseline Consumption * Lead Time Days) + Minimum Stock`
- **Alert Trigger**: If `On Hand < ROP`, a `STOCKOUT_RISK` alert is generated.
- **Daily Baseline**: Calculated by averaging the consumption over the last 30 days.

## 3. Purchase Suggestions
- **Formula**: `Suggested Quantity = Target Stock - On Hand - Expected Inbound (Approved PO lines)`
- **Constraint**: If `Suggested Quantity <= 0`, no suggestion is generated.

## 4. Purchase Price Variation (PPV)
- **Check Point**: Triggered against Supplier Invoices.
- **Formula**: Compares the Invoice `unit_price` against the `unit_cost` of the last positive `StockLedgerEntry` for the given SKU.
- **Alert Trigger**: If variance exceeds 10%, a `PRICE_VARIANCE` alert is generated.
