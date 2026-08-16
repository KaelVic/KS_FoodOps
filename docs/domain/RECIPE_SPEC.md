# Versioned Recipes & Theoretical Consumption

## Recipes
Recipes are defined with versioning to allow historical auditing of consumption.
- **Recipe**: A base entity representing a conceptual item (e.g., "Classic Burger").
- **RecipeVersion**: Immutable snapshots with `valid_from` and `valid_to` timestamps. Editing a recipe automatically creates a new version.
- **RecipeIngredient**: Links a version to specific SKUs.

## POS Sales & Ingestion
- **SalesImport**: Idempotent ingestion batches mapping external POS sales.
- **Sale & SaleLine**: Track individual transaction tickets.
- **POSProductMapping**: Associates a POS item code with an internal KS FoodOps `Recipe`.

## Theoretical Consumption
When a sale is recorded, the system computes the theoretical consumption of raw materials.
- Looks up the active `RecipeVersion` exactly at the time of the `sale_date`.
- Calculates required raw material in base UOM: `(SaleLine Qty * Ingredient Qty) + Loss Percentage`.
- Records `TheoreticalConsumption` for each ingredient to allow "Actual vs Theoretical" variance reporting at the end of an inventory cycle.
