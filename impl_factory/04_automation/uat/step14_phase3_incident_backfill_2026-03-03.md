# Phase 3 Incident Backfill

Date: 2026-03-03  
Owner: AI Runtime Engineering  
Scope: backfilled major Phase 1 and Phase 2 incidents using the Phase 3 incident model  
Status: initial incident baseline created

## Purpose
This document backfills the major failure families already fixed during Phase 1 and Phase 2.

The goal is to make sure the recent stabilization work is not remembered only through chat history or scattered replay logs. These incidents are now recorded as:

1. failure family
2. violated class invariant
3. risk tier
4. owner
5. fix direction
6. regression assets
7. closure evidence

This is the first baseline for the Phase 3 incident register.

## Summary Table

| Incident ID | Severity | Tier | Behavioral Family | Primary Incident Family | Status |
|---|---|---|---|---|---|
| `INC-P2-001` | P1 | Tier 1 | ranking / core read | resolver/report selection failure | Closed |
| `INC-P2-002` | P1 | Tier 2 | transform follow-up / projection | state carryover / transform-followup failure | Closed |
| `INC-P2-003` | P1 | Tier 1 | latest-record listing | state carryover / latest-record resume failure | Closed |
| `INC-P2-004` | P1 | Tier 1 | finance parity | resolver/report selection failure | Closed |
| `INC-P2-005` | P2 | Tier 1 | ranking correction / warehouse | state carryover / topic authority failure | Closed |
| `INC-P2-006` | P2 | Tier 2 | product projection strict-only | projection/shaping failure | Closed |

## Incident Records

### Incident ID: INC-P2-001
- Date Opened: 2026-02-27
- Severity: `P1`
- Risk Tier: `Tier 1`
- Owner: AI Runtime Engineering
- Status: `Closed`

#### User-Visible Symptom
- Prompt: `Top 10 customers by revenue last month`
- What the user saw: `Payment Terms Status for Sales Order`
- Expected behavior: customer revenue ranking

#### Classification
- Behavioral class: `ranking_top_n`
- Primary incident family: `resolver/report selection failure`

#### Root Cause
- Root-cause summary: deterministic ranking-grain semantics were too weak, and the model-assisted reranking could still override a feasible deterministic winner.
- Violated class invariant: requested primary grain must dominate generic report overlap for ranking reads.
- Shared surfaces impacted:
  - `resolver`
  - `capability metadata`

#### Fix Record
- Fix summary: strengthened deterministic ranking precedence, blocked unsafe reranker override of feasible deterministic winners, and enriched governed report semantics.
- Files changed:
  - [semantic_resolver.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/semantic_resolver.py)
  - [resolver_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/resolver_pipeline.py)
  - [capability_registry_overrides_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/capability_registry_overrides_v1.json)
- Why the fix stays inside contract boundary: report choice is governed by deterministic resolver logic and governed capability semantics, not prompt-to-report maps.

#### Regression Assets Added
- Unit/module regression:
  - [test_v7_semantic_resolver_constraints.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_semantic_resolver_constraints.py)
  - [test_v7_resolver_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_resolver_pipeline.py)
- Replay evidence:
  - [20260303T044153Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260303T044153Z_phase6_manifest_uat_raw_v3.json)
- Browser/manual evidence:
  - recorded in [step13_phase2_closure_report_2026-03-02.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step13_phase2_closure_report_2026-03-02.md)

#### Closure Decision
- Closure date: 2026-03-03
- Closed by: AI Runtime Engineering
- Why this incident is considered closed: replay, browser smoke, and release gate are green on current code.

### Incident ID: INC-P2-002
- Date Opened: 2026-02-28
- Severity: `P1`
- Risk Tier: `Tier 2`
- Owner: AI Runtime Engineering
- Status: `Closed`

#### User-Visible Symptom
- Prompts:
  - `Top 10 customers by revenue last month -> Show as Million`
  - `Top 10 products by sold quantity last month -> with Item Name`
  - restrictive `only` follow-ups
- What the user saw: wrong report reuse, repeated transforms collapsing to KPI, or restrictive projection reintroducing old columns.
- Expected behavior: follow-up should stay on the active result and obey the explicit transform/projection contract.

#### Classification
- Behavioral class: `transform_last_result` / `detail_projection`
- Primary incident family: `state carryover / transform-followup failure`

#### Root Cause
- Root-cause summary: transform/projection authority was distributed across memory, transform, and shaping layers, allowing stale output mode and stale visible payload state to override the true active-result contract.
- Violated class invariant: follow-up transform/projection must operate on the latest active result contract and obey explicit restrictive projection intent.
- Shared surfaces impacted:
  - `memory/state`
  - `transform_last`
  - `response_shaper`
  - `read_engine`

#### Fix Record
- Fix summary: preserved hidden source payloads, hardened transform-followup promotion, enforced restrictive `only` semantics, and prevented repeated transforms from collapsing ranked tables.
- Files changed:
  - [memory.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/memory.py)
  - [read_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_engine.py)
  - [transform_last.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/transform_last.py)
  - [response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/response_shaper.py)
  - [ontology_base_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/ontology_base_v1.json)
- Why the fix stays inside contract boundary: all behavior is driven by ontology-backed ambiguities, stored result contracts, and metadata-backed shaping rules rather than prompt-specific business routing.

#### Regression Assets Added
- Unit/module regression:
  - [test_v7_transform_last.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_transform_last.py)
  - [test_v7_response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_response_shaper.py)
  - [test_v7_memory_context.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_memory_context.py)
- Replay evidence:
  - [20260302T071121Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260302T071121Z_phase6_manifest_uat_raw_v3.json)
- Browser/manual evidence:
  - recorded in [step13_phase2_closure_report_2026-03-02.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step13_phase2_closure_report_2026-03-02.md)

#### Closure Decision
- Closure date: 2026-03-03
- Closed by: AI Runtime Engineering
- Why this incident is considered closed: transform-followup replay is green, restrictive browser projection flows are green, and repeated scale follow-ups are stable.

### Incident ID: INC-P2-003
- Date Opened: 2026-02-27
- Severity: `P1`
- Risk Tier: `Tier 1`
- Owner: AI Runtime Engineering
- Status: `Closed`

#### User-Visible Symptom
- Prompt family:
  - `Show me the latest 7 Invoice`
  - follow-up doctype answers such as `Sales Invoice`, `Purchase Invoice`, `revenue Invoice`
- What the user saw: repeated clarification loops, wrong doctype, stale metric carryover, or unsupported/no-coverage fallback.
- Expected behavior: latest-record doctype clarification should resolve once and execute the correct latest-record query.

#### Classification
- Behavioral class: `list_latest_records`
- Primary incident family: `state carryover / latest-record resume failure`

#### Root Cause
- Root-cause summary: latest-record recovery and planner-clarify resume paths could still carry stale detail-projection state (`invoice details`, broad finance domain, old minimal columns) into a resumed latest-record read.
- Violated class invariant: once a latest-record doctype is selected, the resumed contract must be a clean `list_latest_records` contract.
- Shared surfaces impacted:
  - `resume_policy`
  - `spec_pipeline`
  - `read_engine`
  - `memory/state`

#### Fix Record
- Fix summary: pinned doctype/count from the current message, normalized resume seeds to clean latest-record contracts, and ensured the latest-record doctype resolver received correct class context.
- Files changed:
  - [resume_policy.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/resume_policy.py)
  - [spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/spec_pipeline.py)
  - [read_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_engine.py)
- Why the fix stays inside contract boundary: this is generic latest-record resume-state normalization, not prompt-specific routing.

#### Regression Assets Added
- Unit/module regression:
  - [test_v7_read_engine_clarification.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_read_engine_clarification.py)
  - [test_v7_spec_pipeline.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_spec_pipeline.py)
- Replay evidence:
  - [20260303T083453Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260303T083453Z_phase6_manifest_uat_raw_v3.json)
  - representative targeted case: [20260303T065757Z_phase6_manifest_uat_raw_v3.json](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/logs/20260303T065757Z_phase6_manifest_uat_raw_v3.json)
- Browser/manual evidence:
  - recorded in [step13_phase2_closure_report_2026-03-02.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step13_phase2_closure_report_2026-03-02.md)

#### Closure Decision
- Closure date: 2026-03-03
- Closed by: AI Runtime Engineering
- Why this incident is considered closed: latest-record replay family and browser/manual latest-record flows are green on current code.

### Incident ID: INC-P2-004
- Date Opened: 2026-03-02
- Severity: `P1`
- Risk Tier: `Tier 1`
- Owner: AI Runtime Engineering
- Status: `Closed`

#### User-Visible Symptom
- Prompt: `Show accounts receivable as of today`
- What the user saw: `Supplier Ledger Summary`
- Expected behavior: `Customer Ledger Summary`

#### Classification
- Behavioral class: finance parity read
- Primary incident family: `resolver/report selection failure`

#### Root Cause
- Root-cause summary: finance party-ledger tie-break semantics were not strong enough to distinguish receivables from payables.
- Violated class invariant: finance subject hints must deterministically separate customer receivable reads from supplier payable reads.
- Shared surfaces impacted:
  - `semantic_resolver`
  - `capability metadata`

#### Fix Record
- Fix summary: added governed `subject_hints` to party-ledger capabilities and used them in deterministic resolver scoring.
- Files changed:
  - [capability_registry_overrides_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/capability_registry_overrides_v1.json)
  - [semantic_resolver.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/semantic_resolver.py)
- Why the fix stays inside contract boundary: finance subject disambiguation lives in governed capability metadata and generic deterministic scoring, not in prompt-specific business maps.

#### Regression Assets Added
- Unit/module regression:
  - [test_v7_semantic_resolver_constraints.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_semantic_resolver_constraints.py)
- Browser/manual evidence:
  - captured in the final Phase 2 manual pack and summarized in [step13_phase2_closure_report_2026-03-02.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step13_phase2_closure_report_2026-03-02.md)

#### Closure Decision
- Closure date: 2026-03-03
- Closed by: AI Runtime Engineering
- Why this incident is considered closed: browser/manual finance parity check is green and release-gate evidence is green.

### Incident ID: INC-P2-005
- Date Opened: 2026-03-02
- Severity: `P2`
- Risk Tier: `Tier 1`
- Owner: AI Runtime Engineering
- Status: `Closed`

#### User-Visible Symptom
- Prompt family:
  - `Lowest 3 warehouses by stock balance`
  - `I mean Top`
  - `Show as Million`
- What the user saw: wrong stale report family, wrong aggregate-row output, or correction not preserving the ranking contract.
- Expected behavior: correction should stay on warehouse ranking and only change direction.

#### Classification
- Behavioral class: `correction_rebind` / ranking correction
- Primary incident family: `state carryover / topic authority failure`

#### Root Cause
- Root-cause summary: low-signal correction could still rebind to stale topic/result state and generic low-signal rebinding could overwrite the ranking correction contract.
- Violated class invariant: ranking correction must preserve subject, metric, group-by, and `top_n`, and change only direction.
- Shared surfaces impacted:
  - `memory/state`
  - `read_engine`
  - `capability metadata`

#### Fix Record
- Fix summary: hardened ranking-direction correction ordering, latest visible report anchoring, and report semantics so non-ranking warehouse detail reports cannot compete.
- Files changed:
  - [memory.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/memory.py)
  - [read_engine.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/read_engine.py)
  - [session_result_state.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/session_result_state.py)
  - [capability_registry_overrides_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/capability_registry_overrides_v1.json)
- Why the fix stays inside contract boundary: the fix is about generic ranking-correction authority and governed report semantics, not warehouse prompt hardcoding.

#### Regression Assets Added
- Unit/module regression:
  - [test_v7_memory_context.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_memory_context.py)
  - [test_v7_read_engine_clarification.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_read_engine_clarification.py)
- Browser/manual evidence:
  - final warehouse correction flow in [step13_phase2_closure_report_2026-03-02.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step13_phase2_closure_report_2026-03-02.md)

#### Closure Decision
- Closure date: 2026-03-03
- Closed by: AI Runtime Engineering
- Why this incident is considered closed: warehouse correction and scale flow is green in the curated browser smoke pack.

### Incident ID: INC-P2-006
- Date Opened: 2026-03-02
- Severity: `P2`
- Risk Tier: `Tier 2`
- Owner: AI Runtime Engineering
- Status: `Closed`

#### User-Visible Symptom
- Prompt family:
  - `Give me Item Name and Sold Qty only`
  - `Give me Item Name Only`
  - customer-only projection variants
- What the user saw: restrictive `only` requests still kept extra columns or relabeled the explicit column back to a generic dimension.
- Expected behavior: restrictive projection should return only the requested visible business columns.

#### Classification
- Behavioral class: `detail_projection`
- Primary incident family: `projection/shaping failure`

#### Root Cause
- Root-cause summary: shaping still reinserted prior group-by columns and collapsed specific projection labels back to generic canonical dimensions.
- Violated class invariant: restrictive projection must keep only explicitly requested columns and preserve specific requested labels.
- Shared surfaces impacted:
  - `response_shaper`
  - `memory/state`
  - `ontology normalization`

#### Fix Record
- Fix summary: added governed `transform_projection:only` semantics, enforced exact restrictive projection behavior, and preserved specific requested projection labels such as `Item Name`.
- Files changed:
  - [ontology_base_v1.json](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/contracts_data/ontology_base_v1.json)
  - [ontology_normalization.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/ontology_normalization.py)
  - [memory.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/memory.py)
  - [response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/response_shaper.py)
- Why the fix stays inside contract boundary: projection behavior is driven by governed transform semantics and explicit output-contract columns, not prompt-specific report logic.

#### Regression Assets Added
- Unit/module regression:
  - [test_v7_response_shaper.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_response_shaper.py)
  - [test_v7_memory_context.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_memory_context.py)
  - [test_v7_ontology_normalization.py](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/bench_scripts/test_v7_ontology_normalization.py)
- Browser/manual evidence:
  - product and customer restrictive projection flows recorded in [step13_phase2_closure_report_2026-03-02.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step13_phase2_closure_report_2026-03-02.md)

#### Closure Decision
- Closure date: 2026-03-03
- Closed by: AI Runtime Engineering
- Why this incident is considered closed: restrictive projection browser flows are green and `core_read` replay is green.

## Notes
This backfill is intentionally not exhaustive. It captures the major resolved failure families from the Phase 1 and Phase 2 stabilization program.

Future incidents should be recorded directly with [step14_incident_register_template.md](/home/deploy/erp-projects/erpai_project1/impl_factory/04_automation/uat/step14_incident_register_template.md) instead of being backfilled later.
