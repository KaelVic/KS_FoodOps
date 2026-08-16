# Intelligent Supplier Document Ingestion Pipeline

## Safety Boundary
The ingestion pipeline is designed with a strict physical separation between **Extractions** and **Business Records**. AI, OCR, or XML adapters only create `DocumentExtraction` objects. Only a human via `DocumentApprovalService` can convert these extractions into ledger-affecting `SupplierInvoice` or `GoodsReceipt` records.

## Pipeline Steps
1. **Raw Document Storage**: Original files are saved and hashed for deduplication in `RawDocument`.
2. **Deterministic Parsing**: An adapter parses the XML or structured data, returning a standard dictionary payload.
3. **Extraction & Tracking**: The payload is stored in `DocumentExtraction` and `DocumentExtractionLine`. Each field extracted has its lineage recorded in `DocumentExtractionField`.
4. **SKU Matching**: The `SKUMatchingService` attempts to resolve `SupplierSKU`s based on `SupplierSKUAlias` or item codes. Matches can be `EXACT_ALIAS`, `FUZZY_MATCH`, `AMBIGUOUS`, or `UNMATCHED`.
5. **Approval Workflow**: A human reviews any ambiguous lines, fixes them, and approves. The system generates the final records idempotently.
