# Qwen ERP Phase 4B Slice 3 Aging Adapter Note (2026-03-22)

Status: completed  
Scope: Phase 4B Slice 3 from the Semantic Family Layer plan  
Slice goal: implement the governed aging family through deterministic adapters, canonical overdue artifacts, and family-level validation for Accounts Receivable and Accounts Payable aging reads.

## Objective

This slice exists to stop outstanding and overdue analysis from depending only on raw AR/AP report semantics.

It introduces:

1. governed aging-family canonical metrics
2. deterministic normalization for receivable and payable aging outputs
3. family-level validation for normalized aging artifacts
4. compiled-flow integration so aging reads are validated as governed family outputs

This slice does not yet implement ranking/trend, inventory, product profitability, or composite multi-family execution.

## What Was Implemented

### 1. Aging family metadata expansion

Updated [report_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json).

The governed `aging` family now carries canonical metrics for:

1. `outstanding_total`
2. `total_due`
3. `invoiced_total`
4. `paid_total`
5. `credit_note_total`
6. `future_bucket_total`
7. `current_bucket_total`
8. `bucket_31_60_total`
9. `bucket_61_90_total`
10. `bucket_91_120_total`
11. `bucket_121_above_total`
12. `overdue_total`
13. `overdue_ratio`
14. `party_count`

The family dimensions now explicitly include:

1. `party`
2. `bucket`
3. `period`
4. `aging_type`

### 2. Deterministic aging adapter

Updated [family_adapters.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py).

The adapter now normalizes:

1. `Accounts Payable Summary`
2. `Accounts Payable`
3. `Accounts Receivable Summary`
4. `Accounts Receivable`

into a governed `NormalizedFamilyArtifactContract` for `aging`.

The normalized artifact now contains:

1. family id and source report
2. normalized period and filters
3. dimensions such as:
   - `aging_type`
   - `currency`
   - `party_dimension_label`
   - `source_grain`
   - governed bucket labels
4. canonical aging metrics
5. `parties` section
6. `bucket_totals` section
7. `summary` section

The adapter derives:

1. outstanding totals
2. due totals
3. overdue totals
4. overdue ratio
5. governed bucket totals
6. party-level aging rows

from live ERP report fields such as:

1. `outstanding`
2. `total_due`
3. `future_amount` / `range0`
4. `range1` to `range5`
5. party group and territory fields where available

### 3. Family-level validator for aging artifacts

Updated [family_validator.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_validator.py).

The aging validator now checks:

1. required canonical metric presence
2. required section presence
3. party-row presence
4. full governed bucket exposure
5. time-scope consistency
6. family schema consistency

It produces explicit outcomes:

1. `pass`
2. `clarify`
3. `reject_family_inconsistent`

### 4. Probe and smoke helpers

Updated [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py).

Added:

1. `run_phase4b_aging_family_probe`
2. `run_phase4b_aging_family_smoke`

These helpers execute governed compiled reads for:

1. payable aging
2. receivable aging

and verify that:

1. runtime execution succeeds
2. the aging adapter produces a normalized artifact
3. family validation passes

## What Was Intentionally Not Done Yet

This slice does **not** yet implement:

1. ranking and trend family adapters
2. inventory snapshot adapters
3. product profitability adapters
4. composite read planning
5. family-tool routing for Qwen-Agent

Those belong to later Phase 4B slices.

## Verification Performed

Verified:

1. JSON validation passed for:
   - [report_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json)
2. Python compile passed for:
   - [family_adapters.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py)
   - [family_validator.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_validator.py)
   - [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
3. live ERP report shapes were inspected directly for:
   - `Accounts Payable Summary`
   - `Accounts Receivable Summary`
   - `Accounts Payable`
   - `Accounts Receivable`
4. real end-to-end probe passed for:
   - payable aging
   - receivable aging
5. real end-to-end smoke passed through:
   - compiler
   - compiled runtime execution
   - normalized aging family artifact generation
   - family validation
6. runtime and backend were restarted, and the post-restart aging smoke passed again

## Architectural Result

The aging family is now a governed first-class execution unit.

The system can now normalize outstanding and overdue analysis into deterministic business artifacts rather than depending only on raw report headers and row shapes.

This provides a stable family-layer base for:

1. AR/AP overdue analysis
2. bucket-level follow-up explanations
3. later composite working-capital and company-health analysis

## Residual Design Note

Accounts Receivable and Accounts Payable reports can participate in more than one business family.

This slice intentionally normalizes them for the governed `aging` family first.  
The next ranking/trend slice should tighten multi-family routing further so the family layer stays explicit when one report can support more than one business view.

## Exit Decision

Slice 4B.3 is:

- `completed`

## Next Slice

The next Slice 4B.4 work should implement ranking and trend adapters:

1. ranking family artifact
2. trend family artifact
3. canonical time-grain handling
4. canonical dimension and metric normalization
