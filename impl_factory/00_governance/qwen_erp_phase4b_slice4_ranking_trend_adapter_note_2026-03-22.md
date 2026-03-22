# Qwen ERP Phase 4B Slice 4 Ranking and Trend Adapter Note (2026-03-22)

Status: completed  
Scope: Phase 4B Slice 4 ranking and trend analytics family adapters  
Goal: normalize governed ranking and time-series ERP reads into canonical family artifacts, with explicit family routing when one approved report can support multiple business families.

## 1. Why This Slice Was Needed

After Slice 4B.3, a clear multi-family routing problem remained:

1. `Sales Analytics` can support both ranking and trend questions
2. AR/AP summary reports can support both aging and ranking questions
3. `Gross Profit` can support both ranking analytics and later product profitability work

So report name alone was no longer enough to choose the correct governed family.

This slice corrects that boundary by making family adaptation use business intent as a deterministic routing hint rather than guessing from report name only.

## 2. What Was Implemented

### 2.1 Family-Hinted Adapter Routing

The family adapter layer now accepts business intent as a routing hint and resolves the target family deterministically from:

1. approved family coverage for the selected report
2. preferred family if explicitly supplied
3. intent-class family preference order

This prevents shared reports from drifting into the wrong adapter path.

### 2.2 `ranking_analytics` Family Adapter

Governed normalized ranking artifacts now exist for:

1. `Sales Analytics`
2. `Accounts Receivable Summary`
3. `Accounts Payable Summary`
4. `Gross Profit`
5. `Item-wise Sales History`
6. `Stock Balance`
7. `Warehouse Wise Stock Balance`

The normalized ranking artifact now exposes:

1. canonical entity dimension
2. canonical primary metric key
3. ranked rows with deterministic rank order
4. family summary metrics

### 2.3 `trend_analytics` Family Adapter

Governed normalized trend artifacts now exist for:

1. `Sales Analytics`
2. `Item-wise Sales History`

The normalized trend artifact now exposes:

1. canonical time grain
2. canonical period series
3. family summary metrics

For `Sales Analytics`, this slice uses the governed total-period series from the ERP report output.

For `Item-wise Sales History`, this slice can deterministically aggregate row history into monthly series.

### 2.4 Family Validation

Family validation now supports:

1. `ranking_analytics`
2. `trend_analytics`

Validation checks now include:

1. canonical metric presence
2. ranked-row presence for ranking artifacts
3. period-series presence for trend artifacts
4. family schema completeness
5. time-scope consistency

### 2.5 Compiler / Metadata Hardening

`Sales Analytics` metadata was corrected so compiled execution now uses governed defaults for:

1. `tree_type = Customer`
2. `value_quantity = Value`
3. `range = Monthly`
4. existing `doc_type = Sales Invoice`

Compiler filter filling was also hardened so supported dimensions and metrics are matched canonically instead of copying raw user wording directly into ERP report filters.

## 3. Verification

The following checks passed:

1. Python compile / `py_compile`
2. JSON validation for enterprise metadata
3. `run_phase4_compiler_selftests`
4. `run_phase4b_ranking_trend_family_probe`
5. `run_phase4b_ranking_trend_family_smoke`
6. regression smokes:
   - `run_phase4b_financial_statement_family_smoke`
   - `run_phase4b_aging_family_smoke`

Representative successful governed outputs now include:

1. top customers by revenue -> normalized `ranking_analytics`
2. monthly sales trend -> normalized `trend_analytics`
3. top products by gross profit -> normalized `ranking_analytics`

## 4. Enterprise Assessment

This slice keeps the project in the correct enterprise direction because it:

1. does not add phrase-specific hacks
2. does not bypass compiler governance
3. does not let the model choose family behavior freely
4. reduces report-by-report drift by normalizing shared reports into business families

## 5. Important Residual Risk

One important boundary is still not fully closed:

1. normalized family artifacts are now produced and validated
2. but the runtime answer stage is not yet fully forced to render from those normalized artifacts

So a runtime answer can still occasionally phrase or rank details inconsistently with the canonical family artifact, even when the artifact itself is correct.

That should be tightened in later Phase 4B work through:

1. family-level rendering policy
2. family tool surface reduction
3. stronger runtime grounding on normalized artifacts rather than raw report output

## 6. Next Step

The next implementation step is Slice 4B.5:

1. inventory snapshot adapters
2. product profitability adapters
3. governed normalized inventory / product business artifacts
