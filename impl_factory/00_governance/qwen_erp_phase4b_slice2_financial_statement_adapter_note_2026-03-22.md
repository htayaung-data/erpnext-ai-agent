# Qwen ERP Phase 4B Slice 2 Financial Statement Adapter Note (2026-03-22)

Status: completed  
Scope: Phase 4B Slice 2 from the Semantic Family Layer plan  
Slice goal: implement the governed financial statement family through deterministic adapters, canonical normalized artifacts, and family-level validation for Profit and Loss, Balance Sheet, and Cash Flow.

## Objective

This slice exists to stop major financial statements from depending on raw report semantics and ad hoc answer shaping.

It introduces:

1. governed financial statement coverage in shared metadata
2. deterministic canonical normalization for P&L, Balance Sheet, and Cash Flow
3. family-level validation for normalized statement artifacts
4. compiled-flow integration so statement answers can be checked as governed family outputs, not only as raw reports

This slice does not yet implement aging, ranking/trend, inventory, product profitability, or composite multi-family execution.

## What Was Implemented

### 1. Financial statement family metadata expansion

Updated:

1. [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
2. [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json)
3. [report_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json)

The governed financial statement family now explicitly covers:

1. `Profit and Loss Statement`
2. `Balance Sheet`
3. `Cash Flow`

The metadata now defines:

1. approved report families and report ids for `financial_statement_read`
2. canonical financial metrics across all three statements
3. supported dimensions such as `Account` and `Section`
4. statement-specific semantic tags
5. statement-specific defaultable filters, including fiscal-year defaults for cash flow

### 2. Compiler support for statement defaults

Updated [compiler.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiler.py).

The compiler now supports:

1. governed selection of P&L, Balance Sheet, and Cash Flow
2. default fiscal-year resolution for cash flow
3. financial statement selftests for:
   - P&L
   - Balance Sheet
   - Cash Flow

This preserves the rule that the model may propose business meaning, but the compiler chooses the executable statement path and completes required/defaultable filters.

### 3. Deterministic financial statement adapter

Added [family_adapters.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py).

This adapter layer now builds a governed `NormalizedFamilyArtifactContract` for `financial_statement`.

The normalized artifact includes:

1. family id and source reports
2. canonical period block
3. normalized filters
4. normalized dimensions such as:
   - `statement_type`
   - `currency`
   - `periodicity`
   - `value_column`
5. canonical metrics
6. sectioned statement rows

Statement-specific normalized outputs now include:

1. P&L:
   - `total_income`
   - `total_expense`
   - `net_profit`
   - `income`, `expense`, and `summary` sections
2. Balance Sheet:
   - `total_asset`
   - `total_liability`
   - `total_equity`
   - `provisional_profit_or_loss`
   - `assets`, `liabilities`, `equity`, and `summary` sections
3. Cash Flow:
   - `net_cash_from_operations`
   - `net_cash_from_investing`
   - `net_cash_from_financing`
   - `net_change_in_cash`
   - `operations`, `investing`, `financing`, and `summary` sections

The adapter logic stays deterministic and transparent. It normalizes ERP truth and derives canonical metrics, but it does not introduce hidden policy or free-form business reasoning.

### 4. Family-level validator for financial statements

Added [family_validator.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_validator.py).

The validator now checks financial statement artifacts for:

1. required canonical metric presence by statement type
2. required section presence by statement type
3. time-scope consistency
4. family schema consistency

It produces a governed `FamilyValidationContract` with explicit outcomes:

1. `pass`
2. `clarify`
3. `reject_family_inconsistent`

### 5. Compiled-flow integration

Updated:

1. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
2. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)

The compiled first-turn helper now performs:

1. compiler selection
2. compiled runtime execution
3. normalized family artifact construction
4. family validation
5. semantic intent-to-result validation

The service layer now persists the normalized financial artifact and family validation outcome in the compiled attempt trail, and it can block presentation if family validation does not pass.

## What Was Intentionally Not Done Yet

This slice does **not** yet implement:

1. aging family adapters
2. ranking/trend family adapters
3. inventory snapshot adapters
4. product profitability adapters
5. composite read planning across multiple families
6. family-tool routing for Qwen-Agent

Those belong to later Phase 4B slices.

## Verification Performed

Verified:

1. JSON validation passed for:
   - [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
   - [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json)
   - [report_family_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json)
2. Python compile passed for:
   - [compiler.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiler.py)
   - [family_adapters.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py)
   - [family_validator.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_validator.py)
   - [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
   - [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
3. ERP report availability verified for:
   - `Profit and Loss Statement`
   - `Balance Sheet`
   - `Cash Flow`
4. compiler selftests passed for all three statements
5. real end-to-end financial statement family smoke passed through:
   - compiler
   - compiled runtime execution
   - normalized family artifact generation
   - family validation

## Architectural Result

The financial statement family is now a governed first-class execution unit.

The system can now answer major statement requests through:

1. compiler-approved statement selection
2. deterministic normalized financial artifacts
3. family-level validation
4. grounded explanation over normalized business structure instead of only raw report output

This is the first real proof that Phase 4B can broaden enterprise coverage without drifting into report-by-report answer shaping.

## Exit Decision

Slice 4B.2 is:

- `completed`

## Next Slice

The next Slice 4B.3 work should implement the governed aging family:

1. AR aging artifact
2. AP aging artifact
3. normalized overdue buckets
4. canonical totals and ratios
5. family-level validation for aging outputs
