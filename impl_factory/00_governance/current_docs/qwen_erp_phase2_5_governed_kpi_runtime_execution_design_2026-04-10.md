# Qwen ERP Phase 2.5 Governed KPI Runtime Execution Design

Status: 2.5B complete  
Date: 2026-04-10  
Scope: detailed implementation plan for Phase 2.5, Governed KPI Runtime Execution

## 1. Executive Decision

Phase `2` is complete, but the next enterprise move should not be direct expansion into composite artifacts yet.

The correct bridge layer is:

1. governed KPI runtime execution
2. typed KPI value artifacts
3. metadata-owned execution plans
4. blocked-safe KPI answering from live ERP authority

This phase exists because the assistant must be able to answer governed KPI value questions, not only KPI definition questions.

Examples:

1. `what is average order value for sales orders last month`
2. `what is average invoice value this quarter`
3. `what is collection ratio for March 2026`
4. `what is overdue ratio for Zegyo Mobile Supply House as of today`
5. `what is this customer's credit utilization`
6. `show customers above credit limit`

This phase must not be implemented as:

1. keyword-to-report routing
2. one-off KPI handlers
3. prompt-only formula behavior
4. single smoke-driven case branching
5. free-form narrative computation outside governed source authority

## 2. Why Phase 2 Was Necessary But Not Sufficient

Phase `2` solved the semantic problem:

1. KPI meaning is governed
2. formula ownership is governed
3. thresholds and policy bands are governed
4. ambiguous or blocked KPI asks fail closed

But Phase `2` intentionally stopped before live KPI value execution.

That means the assistant currently knows:

1. what `average order value` means
2. what `collection ratio` means
3. what `credit utilization` means
4. what `tenure` means

But it does not yet have a first-class runtime path for:

1. period KPI execution
2. as-of KPI execution
3. governed ranking execution
4. typed KPI value artifacts that carry evidence, scope, and formula basis

If we skip this layer and jump to Phase `3`, the system will risk:

1. composite artifacts built on untyped scalar execution
2. scope drift between KPI meaning and KPI execution
3. code-local execution shortcuts
4. fragile business behavior hidden inside helper logic

So Phase `2.5` is the correct enterprise bridge.

## 3. Enterprise Guideline Constraints For Phase 2.5

This phase must obey the active development guide in:

1. [qwen_erp_enterprise_development_guidelines_2026-04-04.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/current_docs/qwen_erp_enterprise_development_guidelines_2026-04-04.md)

The most important constraints are:

1. contract first
2. metadata owns business policy
3. fail closed
4. explicit authority order
5. no keyword routing
6. no hardcoded single-case fixes
7. no prompt-led business logic

This means:

1. execution shape must be declared in a typed contract before runtime widening
2. KPI execution policy must live in metadata, not in ad hoc Python branches
3. period and as-of scope must come from structured resolution, not prompt heuristics after the fact
4. if a KPI cannot be executed through approved authority, it must block or clarify explicitly

## 4. Current Ecosystem Readiness

The current ecosystem is ready for this phase.

### 4.1 What already exists

The assistant already has:

1. active KPI registries:
   - [business_definition_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_definition_registry.json)
   - [governed_formula_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_formula_registry.json)
   - [business_threshold_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_threshold_registry.json)
   - [business_rule_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_rule_registry.json)
2. active KPI-definition frontdoor behavior
3. governed capability and report metadata
4. active KPI candidates with approved semantics:
   - average order value by sales order
   - average order value by sales invoice
   - customer credit utilization as of date
   - customer overdue ratio as of date
   - customer tenure by customer created date
   - customer tenure by first sales order
   - customer tenure by first sales invoice
   - collection ratio by sales invoice period

### 4.2 What is still missing

The assistant still lacks:

1. a governed KPI execution registry
2. a typed KPI value artifact
3. an execution seam that maps approved KPI formulas to approved report/direct-query authority
4. deterministic blocked-safe behavior for executable versus non-executable KPI value asks
5. governed ranking behavior for KPI-based listings

### 4.3 What should remain blocked even during Phase 2.5

This phase should not widen into:

1. composite multi-metric artifacts
2. management recommendations
3. predictive scoring
4. HR, payroll, or headcount KPIs
5. user-facing overdue severity labels if policy remains unapproved
6. user-facing collection-ratio health labels if policy remains unapproved

## 5. Authority Model For KPI Runtime Execution

KPI value execution must use explicit authority order.

Primary authority:

1. approved KPI definition
2. approved governed formula
3. approved KPI execution metadata
4. approved capability and report metadata
5. live ERP/Frappe output

Supporting authority:

1. threshold metadata when user-facing activation is approved
2. customer or entity context when already grounded and current

Never authoritative:

1. raw chat text after structured interpretation exists
2. prompt examples
3. ad hoc code-local formula constants that bypass the registries
4. narrative convenience answers without typed evidence

## 6. New Contracts And Metadata For Phase 2.5

### 6.1 `GovernedKpiExecutionRegistry`

Phase `2.5` should add a new metadata home:

1. `governed_kpi_execution_registry.json`

Its job is to own execution policy, not KPI meaning.

Recommended fields:

1. `execution_id`
2. `definition_id`
3. `formula_id`
4. `label`
5. `execution_shape`
6. `scope_type`
7. `time_scope_type`
8. `source_mode`
9. `source_capabilities`
10. `source_reports`
11. `supported_filters`
12. `required_dimensions`
13. `value_metric_mapping`
14. `activation_state`
15. `blocked_reason`

### 6.2 `GovernedKpiValueArtifactContract`

This should be the typed runtime artifact for executed KPI values.

Recommended fields:

1. `artifact_type`
2. `definition_id`
3. `formula_id`
4. `execution_id`
5. `label`
6. `execution_shape`
7. `entity_grain`
8. `scope`
9. `as_of_date`
10. `period_start`
11. `period_end`
12. `value`
13. `display_value`
14. `unit_type`
15. `numerator_label`
16. `numerator_value`
17. `denominator_label`
18. `denominator_value`
19. `source_evidence`
20. `threshold_state`
21. `status`
22. `blocked_reason`

### 6.3 Required execution states

The runtime must distinguish:

1. `active_value`
2. `blocked_missing_policy`
3. `blocked_missing_data`
4. `clarify_scope`
5. `clarify_basis`
6. `unsupported_execution_shape`

## 7. Scope For Phase 2.5

### 7.1 In scope

1. KPI value artifact contract
2. KPI execution metadata
3. period KPI execution
4. as-of KPI execution
5. entity-scoped KPI execution
6. governed KPI rankings for single metrics
7. deterministic and live verification
8. docs and closure note

### 7.2 Explicitly out of scope

1. composite multi-metric artifacts
2. multi-step decomposition
3. advisory decisioning
4. write actions
5. new KPI definitions not already governed unless separately approved
6. user-facing threshold labels still blocked by policy

## 8. Detailed Mini-Phase Plan

### 8.1 `2.5A` KPI Value Artifact Contract

Goal:

1. create the execution metadata and typed artifact seam before any runtime widening

Implementation ownership:

1. metadata:
   - add `governed_kpi_execution_registry.json`
2. runtime:
   - add typed artifact normalization helpers
   - add execution-state resolution helpers
3. docs:
   - record what counts as scalar KPI execution versus future composite execution

Acceptance:

1. execution policy is metadata-owned
2. runtime can tell whether a KPI is executable for:
   - company-period scope
   - entity-as-of scope
   - ranking scope
3. blocked or unsupported execution shapes are explicit

Current `2.5A` checkpoint:

1. governed KPI execution metadata now exists in:
   - [governed_kpi_execution_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/governed_kpi_execution_registry.json)
2. metadata loader and accessor support now exists in:
   - [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py)
3. deterministic registry validation now exists in:
   - [governed_kpi_execution_registry.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_execution_registry.py)
4. typed execution-state and KPI-value artifact contracts now exist in:
   - [governed_kpi_execution_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_execution_state.py)
5. active execution coverage now includes:
   - company-period scalar execution
   - customer as-of scalar execution
   - customer as-of ranking execution
6. deterministic coverage now includes:
   - [test_governed_kpi_execution_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_kpi_execution_state.py)
7. callable seam verification now exists through:
   - `run_governed_kpi_execution_registry_probe`
   - `run_governed_kpi_execution_contract_probe`

### 8.2 `2.5B` Period KPI Execution

Goal:

1. support governed period-based KPI value questions

Initial KPI coverage:

1. average order value by sales order
2. average order value by sales invoice
3. collection ratio by sales invoice period

Supported question types:

1. scalar value:
   - `what is average order value for sales orders last month`
2. company-period explanation:
   - `how was collection ratio calculated for March 2026`
3. bounded clarification:
   - `what is average order value`
   - clarify sales order versus sales invoice basis before execution

Required rule:

1. period scope must come from structured date resolution
2. if period scope is missing and policy requires it, runtime must clarify

Acceptance:

1. period KPI answers return typed value artifacts
2. numerator and denominator evidence are visible
3. no KPI value is fabricated when period scope or basis is unclear

Current `2.5B` checkpoint:

1. governed period KPI runtime execution is now active through:
   - [governed_kpi_runtime_execution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_kpi_runtime_execution.py)
   - [frontdoor_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/frontdoor_lane.py)
2. the governed frontdoor now distinguishes KPI definition asks from KPI value asks without introducing a keyword-routed business branch
3. active period KPI runtime coverage now includes:
   - average order value by sales order
   - average order value by sales invoice
   - collection ratio by sales invoice period
4. bounded clarification is now active for:
   - ambiguous document basis
   - missing required period scope
5. period clarification continuation now re-enters the governed KPI runtime path instead of falling through to transaction listing execution
6. deterministic coverage now includes:
   - [test_governed_kpi_runtime_execution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_kpi_runtime_execution.py)
7. live/site verification is now green through:
   - `run_phase2_5_governed_kpi_period_execution_probe`
   - `run_phase2_5_governed_kpi_period_execution_smoke`
8. current site-backed proof is:
   - `Average Order Value by Sales Order` for last month (`2026-03-01` to `2026-03-31`) = `1,473,000 MMK`
   - `Collection Ratio by Sales Invoice Period` for last month (`2026-03-01` to `2026-03-31`) = `68.52%`
9. explicit document-basis asks now resolve without unnecessary clarification when the user already names the governed source surface:
   - `sales orders`
   - `sales invoices`
10. missing-period KPI asks now fail closed to period clarification and do not silently reuse the prior period from an earlier KPI turn
11. governed clarification signals now carry alias-aware option metadata, so bounded shorthand replies such as `Sales Order` and `Sales Invoice` resolve as approved basis choices instead of breaking out into unrelated listing execution
12. `2.5B` is now complete
13. `2.5C` is now complete:
   - active customer-scoped KPI runtime coverage now includes:
     - customer credit utilization as of date
     - customer overdue ratio as of date
     - customer tenure by customer created date
     - customer tenure by first sales order
     - customer tenure by first sales invoice
     - single-metric customer ranking by credit utilization
   - shared customer KPI runtime support now lives in:
     - [customer_kpi_runtime_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/customer_kpi_runtime_support.py)
   - entity detail and direct-evidence follow-ups now reuse the same governed customer snapshot support instead of maintaining page-local KPI logic
   - scalar-vs-ranking detection is now fail-closed:
     - `show customer tenure by first sales order as of today` asks for customer scope
     - `show top 5 customers by credit utilization as of today` stays on the governed ranking path
   - deterministic coverage is active in:
     - [test_customer_kpi_runtime_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_customer_kpi_runtime_support.py)
     - [test_governed_kpi_runtime_execution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_governed_kpi_runtime_execution.py)
     - [test_entity_detail_contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_entity_detail_contracts.py)
   - live/site verification is now green through:
     - `run_phase2_5_governed_kpi_customer_execution_probe`
     - `run_phase2_5_governed_kpi_customer_execution_smoke`
   - current site-backed proof is:
     - `Customer Credit Utilization as of Date` for `Zegyo Mobile Supply House` on `2026-04-10` = `4.95%`
     - `Customer Tenure by Customer Created Date` for `Zegyo Mobile Supply House` on `2026-04-10` = `11 days`
     - top customer by credit utilization on `2026-04-10` = `35th Street Mobile Wholesale` at `98.5%`
14. the next active slice should now be `2.5D`

### 8.3 `2.5C` As-Of And Entity KPI Execution

Goal:

1. support governed as-of and entity-level KPI execution

Initial KPI coverage:

1. customer credit utilization as of date
2. customer overdue ratio as of date
3. customer tenure by approved basis
4. customer credit-limit exceedance
5. ranking by governed KPI for a single metric

Supported question types:

1. entity scalar:
   - `what is Zegyo Mobile Supply House overdue ratio as of today`
2. deictic entity follow-up:
   - `what is this customer's credit utilization`
3. ranking:
   - `show customers above credit limit`
   - `show top customers by credit utilization`

Required rule:

1. ranking is allowed only for a single governed metric with a single approved scope basis
2. if ranking requires composite joins, it belongs to Phase `3`, not here

Acceptance:

1. entity KPI asks stay grounded and typed
2. ranking output remains single-metric and auditable
3. blocked threshold labels still do not leak into user-facing runtime

### 8.4 `2.5D` KPI Runtime Closure

Goal:

1. close the KPI execution bridge phase cleanly before composite expansion

Required closure outcomes:

1. execution metadata exists and validates
2. KPI value artifact contract exists and is runtime-active
3. live executable KPI questions work for both period and as-of shapes
4. blocked-safe behavior remains intact
5. release-gate coverage is promoted
6. docs and baseline references are updated

## 9. Recommended First Execution Shapes

The runtime should start with only these execution shapes:

1. `company_period_scalar`
2. `customer_as_of_scalar`
3. `customer_as_of_ranking`

Do not start with:

1. multi-metric ranking
2. cross-grain joins
3. decomposition-driven KPI chaining

Those belong later.

## 10. Verification Strategy

Minimum deterministic coverage should include:

1. execution-registry validation
2. artifact normalization validation
3. period KPI execution validation
4. entity KPI execution validation
5. ranking-scope validation
6. blocked-safe behavior when threshold labels remain unapproved
7. clarify behavior when basis or period is missing

Live or site-backed verification should include:

1. `what is average order value for sales orders last month`
2. `what is average invoice value this quarter`
3. `what is collection ratio for March 2026`
4. `what is overdue ratio for Zegyo Mobile Supply House as of today`
5. `what is this customer's credit utilization`
6. `show customers above credit limit`

## 11. Stop Rule

Stop Phase `2.5` when:

1. governed KPI values can be executed for the approved KPI set
2. period and as-of shapes are typed and auditable
3. ranking remains single-metric and governed
4. blocked-safe policy handling still holds
5. release gates are green

Do not widen Phase `2.5` into:

1. composite artifacts
2. decomposition planning
3. recommendation behavior
4. multilingual UX expansion
5. dashboard generation

## 12. Current Recommendation

The approved next implementation order should be:

1. `2.5A` KPI Value Artifact Contract
2. `2.5B` Period KPI Execution
3. `2.5C` As-Of And Entity KPI Execution
4. `2.5D` KPI Runtime Closure

Only after that should the roadmap move into:

1. `Phase 3` Composite Governed Artifact Expansion

That is the correct enterprise-grade sequence.
