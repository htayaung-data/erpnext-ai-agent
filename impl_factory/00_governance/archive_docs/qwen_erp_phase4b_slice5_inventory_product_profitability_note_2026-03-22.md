# Qwen ERP Phase 4B Slice 5 Inventory and Product Profitability Adapter Note (2026-03-22)

Status: completed  
Scope: Phase 4B Slice 5 inventory snapshot and product profitability family adapters  
Goal: normalize governed stock and product-performance ERP reads into canonical family artifacts so inventory and product questions no longer depend on raw report semantics.

## 1. Why This Slice Was Needed

After Slice 4B.4, the family layer still had a major gap:

1. inventory questions still depended on raw `Stock Balance` / `Warehouse Wise Stock Balance` semantics
2. product-performance questions still depended on raw `Gross Profit` / `Item-wise Sales History` semantics
3. the same capability surface covered both snapshot-style and profitability-style business reads, but there was no canonical normalized artifact for either family

This slice closes that gap by making inventory and product business reads first-class governed families.

## 2. What Was Implemented

### 2.1 `inventory_snapshot` Family Adapter

Governed normalized inventory artifacts now exist for:

1. `Stock Balance`
2. `Warehouse Wise Stock Balance`

The adapter now supports two different ERP report shapes:

1. item-level stock snapshot rows from `Stock Balance`
2. warehouse-tree snapshot rows from `Warehouse Wise Stock Balance`

The normalized inventory artifact now exposes:

1. canonical snapshot rows
2. canonical item totals
3. canonical warehouse totals
4. summary metrics such as:
   - `balance_qty`
   - `balance_value`
   - `item_count`
   - `warehouse_count`

Important governed behavior:

1. `Warehouse Wise Stock Balance` is treated as a warehouse-value tree, not as item rows
2. when the warehouse report does not expose quantity, the artifact keeps `balance_qty = 0.0` and uses `stock_balance` as the governed value metric
3. inventory snapshot periods default to current-date semantics when the ERP report does not carry an explicit report date

### 2.2 `product_profitability` Family Adapter

Governed normalized product profitability artifacts now exist for:

1. `Gross Profit`
2. `Item-wise Sales History`

The normalized product artifact now exposes:

1. canonical product rows
2. canonical product summary metrics such as:
   - `gross_profit`
   - `gross_profit_percent`
   - `sales_amount`
   - `quantity`
3. deterministic primary-metric selection for product-family output

Important governed behavior:

1. `Gross Profit` normalizes grouped profitability rows, totals, and overall gross-margin posture
2. `Item-wise Sales History` normalizes sales-history rows into canonical item totals rather than leaving runtime to infer item performance from raw order history

### 2.3 Metadata Alignment

Metadata was aligned so family coverage matches governed intent coverage:

1. `stock_read` and stock reports now explicitly support `financial_summary` as well as `inventory_summary`
2. `product_performance_read` and product reports now explicitly support `trend_analysis` where governed family coverage already allowed it

This prevents the family layer from being broader than the compiler metadata.

### 2.4 Family Validation

Family validation now supports:

1. `inventory_snapshot`
2. `product_profitability`

Validation checks now include:

1. canonical metric presence
2. snapshot-row presence for inventory artifacts
3. product-row presence for product profitability artifacts
4. family schema completeness
5. time-scope consistency

## 3. Verification

The following checks passed:

1. Python compile / `py_compile`
2. JSON validation for enterprise metadata
3. `run_phase4_compiler_selftests`
4. `run_phase4b_inventory_product_family_probe`
5. `run_phase4b_inventory_product_family_smoke`
6. post-restart `run_phase4b_inventory_product_family_smoke`
7. regression smokes:
   - `run_phase4b_financial_statement_family_smoke`
   - `run_phase4b_ranking_trend_family_smoke`

Representative successful governed outputs now include:

1. current inventory value by warehouse -> normalized `inventory_snapshot`
2. stock balance by item -> normalized `inventory_snapshot`
3. which products are performing well last month -> normalized `product_profitability`
4. item sales history this fiscal year -> normalized `product_profitability`

## 4. Enterprise Assessment

This slice keeps the project in the correct enterprise direction because it:

1. expands business coverage through family adapters rather than prompt-only behavior
2. keeps the compiler and validator boundary intact
3. normalizes multiple ERP report shapes into canonical business artifacts
4. reduces dependence on report-specific schema knowledge inside Qwen-Agent

## 5. Important Residual Risk

One important boundary still remains:

1. normalized family artifacts are now correct and validated
2. but runtime answer rendering is still not fully constrained to those normalized artifacts

That means the live natural-language answer can still:

1. mix ranking criteria
2. phrase summary emphasis differently from the canonical artifact
3. occasionally present top-item order that is not identical to the normalized family output

So the remaining gap is no longer adapter normalization.  
It is family-grounded rendering policy.

## 6. Next Step

The next implementation step is Slice 4B.6:

1. composite read planning
2. compiler-approved multi-family execution
3. governed company-health / working-capital style composite reads
