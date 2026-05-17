# Qwen ERP Phase 4B Slice 6 Composite Read Planning Note (2026-03-22)

Status: completed  
Scope: Phase 4B Slice 6  
Goal: introduce compiler-approved composite read planning so cross-family ERP questions can execute through governed multi-family plans instead of report-by-report or model-only synthesis.

## What Was Implemented

Slice 4B.6 added a governed composite planning layer for the first composite read class:

1. `working_capital_health`
   - governed AR/AP company-health and working-capital analysis
   - compiler-approved multi-step execution
   - deterministic summary rendering from normalized family artifacts

Implemented components:

1. composite profile metadata in `composite_read_registry.json`
2. ontology extension for `working_capital`
3. metadata helpers for composite profile loading and concept detection
4. composite planner/executor in `composite_reads.py`
5. compiled-path integration in `fresh_query_interpreter.py`
6. service artifact persistence updates in `service.py`

## Governing Behavior

The composite path now works as:

1. fresh-query proposal returns business meaning
2. composite planner checks governed ontology concepts and composite profile metadata
3. compiler approves a `CompositeReadPlanContract`
4. each governed step is compiled through the existing single-family compiler
5. each step executes through the constrained runtime path
6. each step is normalized and family-validated
7. deterministic composite summary is rendered from the normalized artifacts
8. composite audit and validation payloads are persisted

Important rule preserved:

- Qwen-Agent does not invent the composite plan
- the compiler approves the plan
- adapters normalize each family result
- the composite summary is grounded in normalized artifacts

## First Governed Composite Profile

Current profile:

1. `working_capital_health`
   - concepts required: `receivable` + `payable`
   - supported intent classes: `financial_summary`, `aging_analysis`
   - governed steps:
     - `Accounts Receivable Summary`
     - `Accounts Payable Summary`

This supports questions in the class of:

- AR/AP analysis
- company health from AR/AP posture
- working-capital pressure from receivable/payable balances

## Operational Design Note

Composite execution is currently **serialized intentionally**.

Reason:

- Frappe configuration is thread-local in the current worker/runtime arrangement
- parallel child threads lost runtime base URL/auth state during verification
- enterprise correctness and governed execution were prioritized over speculative parallelism

So:

- metadata may allow parallel execution
- actual execution is currently sequential by design
- this is the safe posture until runtime config propagation is made thread-safe

## Verification

Verified successfully:

1. `python3 -m py_compile` for updated modules
2. metadata JSON validation
3. `run_phase4b_composite_read_probe`
4. `run_phase4b_composite_read_smoke`
5. `run_first_turn_regression_suite` for:
   - `Analyze AR / AP amount and evaluate the company health`
6. `run_phase4_compiler_selftests`
7. `run_phase4b_aging_family_smoke`

Observed live result:

- the AR/AP company-health question now executes through `compiled_first_turn`
- a governed composite plan is persisted
- normalized AR and AP family artifacts are persisted
- composite validation and audit payloads are persisted

## Next Step

Next implementation slice:

1. Slice 4B.7 family-level validation and rendering

That slice should tighten:

1. composite completeness validation
2. canonical family/composite response structures
3. rendering so runtime/user-visible answers stay closer to normalized artifacts
