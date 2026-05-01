# Qwen ERP Natural Business Understanding Mini-Phase Plan

Status: design lock draft for implementation
Date: 2026-04-30
Scope: unified natural business request understanding, governed routing, context resolution, and professional fallback behavior before Phase 4 complex business-question decomposition

## 1. Purpose

This mini-phase exists because manual browser UAT exposed a higher-level problem:

1. the assistant can answer many prepared governed questions
2. but natural human business wording can still fall between routing seams
3. when that happens, the system may return stale-context answers, wrong report families, or internal-looking fallback text

The goal is not to make the assistant answer every possible question with unsupported confidence.

The goal is to make the assistant handle every message professionally:

1. answer from governed ERP evidence when supported
2. execute a fresh governed query when the message is self-contained
3. resolve follow-up/context references when safe
4. requery governed evidence when the current artifact is insufficient but a supported source exists
5. ask a clear clarification when intent or target is ambiguous
6. explain authority/evidence boundaries when recommendations, predictions, approvals, or unsupported analyses are requested
7. respond politely when the request is outside ERP/business scope

## 2. Current Situation

The project already has many of the correct building blocks:

1. lightweight model frontdoor interpretation
2. lightweight model fresh-query interpretation
3. lightweight model follow-up interpretation
4. semantic reasoning activation
5. repair intent interpretation
6. governed metadata registries
7. capability, report, family, composite, KPI, and policy registries
8. recent-focus and artifact-reference support
9. entity-reference and entity-detail support
10. clarification and recovery contracts
11. boundary and authority policy support
12. Phase 3.6 quality-gate matrix

The gap is that these pieces are not yet unified by one natural business understanding control plane.

Current behavior is fragmented across frontdoor, fresh-query, follow-up, composite, reasoning, boundary, and recovery lanes. This makes natural requests vulnerable to precedence drift, stale context, or over-specific deterministic handling.

## 3. Core Enterprise Principle

The lightweight model should be the primary natural-language interpreter.

Deterministic registries and metadata should not replace understanding. They should validate, constrain, and audit the model interpretation.

Bad pattern:

1. if user phrase matches dictionary entry, force route
2. keep adding phrases every time the user says something new

Approved pattern:

1. model proposes ranked business interpretations
2. registry validates whether each interpretation is governed
3. context and evidence validators decide whether the current artifact can answer
4. policy validators decide whether the request is allowed
5. the system chooses a safe action or asks clarification

## 4. Target Architecture

Natural Business Understanding, abbreviated NBU, becomes a shared semantic control plane above existing lanes.

It must not replace existing lanes immediately.

It should first run in observation mode, then progressively govern high-confidence routing decisions.

The target pipeline:

1. receive user message and conversation snapshot
2. build compact NBU context from current artifact, recent focus, pending clarification, capability registry, composite registry, KPI registry, and authority policy
3. ask lightweight model for ranked candidate interpretations
4. validate candidates against metadata, evidence, context, and policy
5. compute system confidence from multiple signals, not raw model confidence alone
6. choose a Conversation Action Decision
7. execute existing lane, requery, clarify, restore, boundary, guidance, or out-of-scope response
8. record decision trace for audit and future improvement

## 5. Shared Contract Shape

The NBU contract should be explicit, serializable, and safe for audit.

Initial contract fields:

1. `request_id`
2. `session_id`
3. `raw_message`
4. `detected_language`
5. `candidate_interpretations`
6. `selected_interpretation`
7. `validation_result`
8. `system_confidence`
9. `conversation_action_decision`
10. `evidence_plan`
11. `authority_plan`
12. `context_resolution`
13. `response_mode`
14. `clarification_question`
15. `boundary_reason`
16. `trace_summary`

Candidate interpretation fields:

1. `intent_scope`: fresh_query, followup, context_reference, policy_boundary, capability_question, out_of_scope
2. `business_domain`: financial_statement, ar, ap, customer_risk, inventory, master_data, transaction_listing, sales, purchase, supplier, customer, item, working_capital
3. `requested_action`: show, explain, detail, compare, requery, recommend, predict, approve, restore, cancel, clarify
4. `target_reference`: current_artifact, previous_artifact, rank_n, named_entity, selected_entity, candidate_list, unclear
5. `target_entity`: entity type, key, label when known
6. `candidate_route`: frontdoor_composite, governed_kpi, fresh_query, local_followup, entity_detail, boundary, clarification, recovery
7. `candidate_capability_ids`
8. `candidate_report_names`
9. `candidate_composite_family_ids`
10. `requested_metrics`
11. `requested_dimensions`
12. `requested_time_scope`
13. `evidence_need`: current_artifact_ok, needs_governed_requery, unsupported_policy, needs_clarification, out_of_scope
14. `authority_class`: safe_read, safe_explanation, governed_requery, recommendation, prediction, approval_action, unsupported_analysis
15. `model_confidence`
16. `model_reason`

## 6. System Confidence

The system must not rely only on model confidence.

System confidence should combine:

1. model confidence
2. registry match strength
3. capability or composite availability
4. current artifact compatibility
5. row/entity reference clarity
6. evidence availability
7. authority/policy state
8. context conflict score

If signals disagree, the system should either clarify or choose a safe boundary, not silently execute a low-trust route.

## 7. Conversation Action Decisions

Every turn should end with exactly one action decision:

1. `answer_from_current_artifact`
2. `execute_fresh_governed_query`
3. `execute_governed_requery`
4. `ask_clarification`
5. `show_supported_options`
6. `restore_previous_context`
7. `clear_pending_context`
8. `reject_with_boundary`
9. `answer_capability_question`
10. `out_of_scope_response`

This is stronger than fresh-query versus follow-up because it handles natural business actions, corrections, cancellation, row references, and policy boundaries.

## 8. Context Priority Rules

The NBU layer must enforce context priority consistently:

1. explicit new self-contained request beats pending clarification
2. explicit user correction beats previous interpretation
3. `forget that`, `ignore that`, and similar language clears pending ambiguity
4. `that customer` uses latest selected customer only if unambiguous
5. `first customer`, `rank 2`, and `second position` use the current visible ranked/list artifact
6. `above table` uses the current artifact
7. `go back` restores previous compatible focus only when the target is clear
8. unsupported recommendation/prediction/approval wording triggers authority boundary even when evidence exists
9. current artifact can answer only if the requested fields/rows are actually present
10. missing fields should trigger governed requery only when a supported source exists

## 9. Mini-Phase Slices

### NBU-0: Baseline And Failure Inventory

Status: complete for current baseline

Purpose:

Capture current natural-language failures as shared-seam test cases, not prompt-specific fixes.

Deliverables:

1. failure inventory from manual browser UAT
2. classification by seam: understanding, context, evidence, authority, requery, fallback, presentation
3. expected behavior for each failure
4. mapping to existing reusable modules

Exit gate:

1. all known Group 2 failures are represented as scenarios
2. no scenario is framed as a single-case keyword patch

Implementation note:

1. baseline inventory recorded in `qwen_erp_nbu_0_failure_inventory_and_contract_fit_2026-04-30.md`
2. current failures are classified by shared seam and required NBU contract fields

### NBU-1: Contract And Trace Skeleton

Status: initial skeleton complete

Purpose:

Add the shared NBU contract and decision trace without changing production routing.

Deliverables:

1. NBU dataclasses/builders
2. candidate interpretation payload shape
3. validation/result payload shape
4. conversation action decision payload
5. audit/observability payload
6. tests for serialization and required fields

Exit gate:

1. contract can be appended to tool payloads
2. existing tests remain green
3. no behavior change yet

Implementation note:

1. initial contract skeleton implemented in `qwen_chat/natural_business_understanding_contracts.py`
2. focused tests added in `tests/test_natural_business_understanding_contracts.py`
3. skeleton defaults to shadow/observe-only behavior and does not alter routing

### NBU-2: Lightweight Model Interpretation In Shadow Mode

Status: in progress; NBU-2A shadow schema/runtime/client wrapper complete

Purpose:

Use the existing lightweight runtime as the natural-language interpreter for ranked candidate interpretations.

Deliverables:

1. runtime schema for NBU interpretation
2. prompt using compact current-artifact, recent-focus, capability, composite, KPI, and policy context
3. app-side runtime client call
4. candidate interpretation validator
5. shadow-mode trace appended without altering routing

Exit gate:

1. NBU shadow payload appears for representative turns
2. raw model output is schema-validated
3. invalid or low-confidence output does not affect routing

Implementation note:

1. runtime schema and `/interpret-business-understanding` endpoint added in the Qwen runtime app
2. runtime engine added as `semantic_business_understanding_engine.py`
3. app-side runtime client call added as `call_qwen_runtime_business_understanding_interpretation`
4. app-side observe-only wrapper added in `qwen_chat/natural_business_understanding_runtime.py`
5. focused contract/runtime wrapper tests pass in the backend container
6. route activation and automatic trace append remain intentionally deferred until NBU-3/NBU-4 gates are ready

### NBU-3: Governed Validation And System Confidence

Status: complete for NBU validation contract; activation consumption deferred to NBU-4/NBU-7

Purpose:

Validate model candidates against enterprise metadata and compute system confidence.

Deliverables:

1. registry/capability validation
2. report/composite/KPI validation
3. artifact row/field compatibility validation
4. authority/policy validation
5. context conflict detection
6. system confidence calculation

Exit gate:

1. model-only confidence is never used as the sole execution basis
2. disagreements produce clarify or boundary decisions
3. validation result is auditable

Implementation note:

1. validation module added in `qwen_chat/natural_business_understanding_validation.py`
2. validation checks registry anchors, context-reference clarity, artifact compatibility, evidence availability, and authority policy state
3. shadow wrapper now includes validation and system-confidence contracts instead of zero-confidence placeholders
4. policy-gated authority classes are blocked even when model confidence is high
5. future domains are warned and preserved instead of rejected, supporting HR/CRM/future family onboarding
6. report, composite family, and governed KPI execution compatibility are validated using generic metadata specs
7. current-artifact field compatibility detects missing requested metrics/dimensions before local artifact answers are allowed
8. context-family conflict detection prevents stale-context errors such as answering customer-risk follow-ups from a Balance Sheet artifact
9. focused NBU contract/runtime/validation test coverage is green in the backend container

### NBU-4: Conversation Action Decision Layer

Status: in progress; NBU-4B shadow trace decision integration complete

Purpose:

Convert validated interpretation into exactly one action decision.

Deliverables:

1. action decision builder
2. priority rules for fresh query, follow-up, requery, clarification, restore, cancel, and boundary
3. safe action matrix
4. tests for conflicting-context decisions

Exit gate:

1. self-contained fresh requests are not blocked by stale pending clarification
2. follow-ups do not override explicit new requests
3. boundary requests are recognized before unsafe reasoning

Implementation note:

1. standalone action decision builder added in `qwen_chat/natural_business_understanding_decision.py`
2. decisions are derived from validated candidates, validation results, system confidence, evidence plan, and authority plan
3. boundary and out-of-scope decisions take precedence over query execution
4. context conflicts become clarification decisions instead of stale-context answers
5. safe current-artifact answers and governed requery/fresh-query decisions are represented but not yet wired into live routing
6. focused NBU decision tests are green in the backend container
7. shadow wrapper now records the proposed action decision, evidence plan, and authority plan in the NBU trace
8. shadow decision payloads explicitly include `shadow_mode`, `runtime_execution_enabled=false`, and `execution_not_performed=true`
9. live chat routing remains unchanged

### NBU-5: Generic Context And Row Reference Resolver

Status: in progress; NBU-5A generic row/candidate reference contract integration complete; NBU-5B conversation-control evidence bridge complete; NBU-5C recent-focus resolution bridge complete

Purpose:

Resolve natural references generically across artifacts.

Deliverables:

1. row reference parser for first, second, rank N, position N, No. N, above table
2. entity reference resolver for that customer, that supplier, that product, that invoice
3. candidate-list resolver for show me the list, that one, choose option
4. previous-focus resolver for go back to the customer/supplier/product
5. cancellation resolver for forget that/ignore that

Exit gate:

1. works across customer risk, AR aging, product ranking, master-data lists, inventory, and transaction listings
2. ambiguous references ask clarification
3. no family-specific row-reference branches are needed for each new artifact

Implementation note:

1. generic context resolver added in `qwen_chat/natural_business_understanding_context_resolution.py`
2. resolver supports visible artifact row references such as first, second, rank N, row N, No. N, and last
3. resolver supports generic candidate-list references such as ambiguous possible matches and selected option positions
4. resolver preserves direct named-entity target payloads when the NBU candidate already identifies the entity
5. resolver reuses existing artifact/entity helper seams instead of adding customer-risk-specific or item-specific branches
6. shadow NBU runtime now records `context_resolution` for selected candidates without changing live routing
7. NBU shadow context now carries compact evidence from the existing conversation-control classifier for option-list, discard, cancellation, and prior-branch restore wording
8. NBU does not duplicate the mature conversation-control classifier; it records that evidence for validation/activation readiness
9. previous-artifact references can now resolve the current recent-focus contract when focus kind, grain, label, and key are available
10. focused NBU context-resolution and runtime trace tests are green in the backend container
11. remaining NBU-5 work: activation consumption after broader replay confidence

### NBU-6: Governed Requery Planner

Status: in progress; NBU-6A shadow governed requery plan contract complete; NBU-6B strict proof and nearest-supported alternative planning complete

Purpose:

When current evidence is insufficient, decide whether a supported governed requery can answer.

Deliverables:

1. current-artifact field availability check
2. entity-detail requery plan
3. customer credit/detail requery plan
4. item stock/detail requery plan
5. supplier payable/detail requery plan
6. unsupported-requery boundary when no governed source exists
7. nearest-supported alternatives when the exact requested metric/dimension is not proven
8. unverified candidate-anchor fallback only when metadata is genuinely absent

Exit gate:

1. credit-limit follow-up from AR/customer-risk context can requery only if governed source exists
2. missing fields no longer produce ugly internal fallback
3. unsupported requery explains nearest supported options
4. candidate report/capability names alone do not become execution-ready when metadata disproves the requested fields
5. future-family onboarding can still shadow-plan from candidate anchors, but the trace marks that metadata support is unverified

Implementation note:

1. governed requery plan contract added to the NBU trace as `qwen_nbu_governed_requery_plan_contract`
2. standalone planner added in `qwen_chat/natural_business_understanding_requery_planner.py`
3. planner uses selected NBU candidate, validation result, evidence plan, context resolution, and metadata specs
4. planner supports shadow-ready entity-detail, capability/report, composite, and governed-KPI requery targets
5. planner blocks when context is ambiguous or out of range instead of executing against the wrong row/entity
6. planner blocks policy-gated candidates even when a governed source exists
7. planner is metadata-driven and does not add phrase-specific business mappings
8. live execution remains disabled; existing execution lanes remain the future activation owners
9. NBU-6B tightened readiness so requested metrics/dimensions must be supported by active metadata specs before a plan becomes `ready_shadow`
10. NBU-6B adds governed alternatives into the requery plan for unsupported exact requests, so a renderer can explain what nearby governed sources are available
11. NBU-6B preserves extensibility for future HR/CRM/family onboarding by allowing candidate-anchor shadow plans only when metadata specs are absent, with an explicit `metadata_context_absent_candidate_targets_unverified` warning
12. backend verification passed for 45 NBU shadow tests on 2026-04-30, including contracts, runtime, validation, decision, context resolution, and requery planner coverage

### NBU-7: Professional Response And Fallback Renderer

Status: in progress; NBU-7A shared shadow professional response renderer complete; NBU-7B evidence-missing and nearest-supported wording polish complete; NBU-7C capability/out-of-scope polish and user-visible leakage guard complete

Purpose:

Make every fallback business-natural and professional.

Deliverables:

1. clarification renderer
2. evidence-missing renderer
3. policy-boundary renderer
4. unsupported-scope renderer
5. out-of-scope renderer
6. capability-guidance renderer
7. technical detail hidden by default but kept in trace
8. safe-to-show gating so shadow direct-answer traces do not replace mature artifact renderers
9. capability and out-of-scope wording that guides users back to governed ERP context
10. user-showable text quality guard for internal implementation terms

Exit gate:

1. no user-facing fallback uses internal contract language by default
2. responses offer a clear next step where possible
3. boundaries are polite, short, and business understandable

Implementation note:

1. NBU-7A added `qwen_chat/natural_business_understanding_response_renderer.py` as a pure renderer over the existing NBU trace
2. the renderer produces `qwen_nbu_professional_response_contract` payloads with `title`, `answer_text`, `next_steps`, `boundary_class`, `safe_to_show`, and compact audit details
3. clarification, supported-options, policy-boundary, governed-requery, out-of-scope, capability-guidance, unsupported-evidence, and default shadow cases are covered without family-specific phrase mapping
4. `interpret_natural_business_understanding_shadow` now attaches `professional_response` to the trace, but live runtime response behavior remains unchanged
5. direct current-artifact answers remain owned by mature artifact renderers; NBU marks those shadow response drafts as not user-showable
6. backend verification passed for 50 NBU shadow tests on 2026-04-30, including renderer, runtime, contracts, validation, decision, context resolution, and requery planner coverage
7. NBU-7B gives unsupported governed-evidence cases priority over generic clarification when the requery planner has already proven that exact evidence is not supported
8. NBU-7B renders nearest-supported alternatives as business options and names missing evidence such as requested metrics/dimensions without exposing internal contract terms
9. NBU-7B keeps true ambiguity in the clarification path while routing unsupported evidence to `Nearest Governed Options` or `Missing Governed Evidence`
10. backend verification passed for 51 NBU shadow tests on 2026-04-30 after the NBU-7B renderer refinement
11. NBU-7C removes live-activation wording from governed-source drafts and uses `Governed Source Available` instead of implementation-facing requery language
12. NBU-7C adds capability guidance from candidate report/composite/capability anchors without family-specific phrase dictionaries
13. NBU-7C improves out-of-scope guidance by asking the user to rephrase with an ERP report, entity, metric, or period when appropriate
14. NBU-7C adds `quality_warnings` to the professional response payload so future activation can block user-showable responses that contain internal implementation terms
15. backend verification passed for 53 NBU shadow tests on 2026-04-30 after the NBU-7C renderer refinement

### NBU-8: Controlled Routing Activation

Status: in progress; NBU-8A shadow activation-readiness assessment complete

Purpose:

Enable NBU decisions gradually for high-value, high-confidence lanes.

Activation order:

1. customer risk and AR/AP health fresh query routing
2. ranked-row explanation from current artifact
3. artifact-local aging breakdown and metric explanation
4. entity-detail requery from selected customer/supplier/product
5. context cancellation and fresh request override
6. unsupported recommendation/prediction/approval boundaries

Exit gate:

1. Group 2 manual browser failures pass
2. Group 1 finance flows remain stable
3. master-data and inventory context flows remain stable
4. transaction listing fresh queries remain stable

Implementation note:

1. NBU-8A added `qwen_chat/natural_business_understanding_activation.py` as a pure controlled-activation assessment layer
2. NBU-8A does not enable live behavior; it records whether an NBU trace is eligible for future presentation-only activation
3. presentation-only eligible actions currently include clarification, supported options, policy/evidence boundary, out-of-scope, and capability guidance responses
4. direct current-artifact answers remain delegated to mature artifact renderers and are blocked from NBU presentation activation
5. governed requery/fresh-query execution remains blocked behind `requires_execution_lane_activation` until a later activation slice owns execution routing
6. professional-response `safe_to_show` and `quality_warnings` are hard gates for future presentation activation
7. `interpret_natural_business_understanding_shadow` now attaches `activation_assessment` alongside `professional_response`
8. backend verification passed for 57 NBU shadow tests on 2026-04-30 after NBU-8A

NBU-8B update:

1. Status: implemented and backend-verified on 2026-04-30
2. Added `qwen_chat/natural_business_understanding_service_activation.py` as the first service-level controlled activation seam
3. Wired `service.py` to try NBU only after the mature front-door, clarification, reasoning, direct artifact, entity-detail, and local evidence lanes have had priority
4. Activation is limited to presentation-only responses that passed `activation_assessment`, `safe_to_show`, and zero `quality_warnings`
5. NBU-8B does not execute governed requery plans, does not answer from current artifacts, and does not override delegated artifact renderers
6. If NBU is not eligible, the existing assistant flow continues unchanged
7. Backend verification passed for 61 NBU tests plus a Frappe-context service import/governance selftest
8. This is the first narrow live NBU rescue lane; governed requery execution remains a later NBU slice

NBU-8B polish update:

1. Status: implemented and backend-verified on 2026-04-30 after manual browser UAT feedback
2. Live NBU clarification and supported-options responses are now deferred to existing mature ERP routing because they can wrongly block normal queries such as supplier lists
3. User-facing NBU response language was changed from internal governance wording to business-natural language such as "Decision Not Available Yet", "ERP facts", and "Available ERP Options"
4. Added a gated current-artifact row/rank answer activation for cases where NBU resolves a visible row and evidence is already present in the current ERP result
5. Direct row/rank activation does not execute reports, does not predict, and does not recommend; it only summarizes visible row facts
6. Backend NBU verification passed for 63 tests after the polish changes

### NBU-9: Quality Gate And Regression Expansion

Status: final slice for this mini-phase

Purpose:

Lock the behavior with automated and manual coverage before moving further toward Phase 4.

Deliverables:

1. contract tests for NBU contract, validator, and action decision
2. replay tests for current browser failures
3. cross-family row-reference tests
4. stale-context and cancellation tests
5. professional fallback tests
6. manual browser checklist updates

Exit gate:

1. Phase 3.6 A-gate scenarios pass or have approved documented exceptions
2. no internal-error behavior remains in tested paths
3. no severe stale-context leakage remains
4. unsupported authority requests remain blocked
5. Phase 4 remains blocked until this quality gate is accepted

## 10. Implementation Guardrails

This mini-phase must follow these guardrails:

1. do not add phrase-by-phrase patches as the primary solution
2. do not duplicate existing frontdoor/fresh/follow-up/reasoning engines
3. do not put large new logic directly into `service.py`
4. keep new business logic in dedicated NBU modules
5. run in shadow mode before changing production routing
6. keep deterministic metadata as validation, not as the main brain
7. preserve existing working behavior unless a change is explicitly covered by tests
8. log low-confidence unknowns for future improvement instead of hardcoding each one

## 11. Proposed Module Map

Recommended new module family:

1. `qwen_chat/natural_business_understanding_contracts.py`
2. `qwen_chat/natural_business_understanding_runtime.py`
3. `qwen_chat/natural_business_understanding_validator.py`
4. `qwen_chat/natural_business_understanding_decision.py`
5. `qwen_chat/natural_business_understanding_context.py`
6. `qwen_chat/natural_business_understanding_requery.py`
7. `qwen_chat/natural_business_understanding_response.py`

Recommended runtime addition:

1. `experimental/qwen_agent_runtime/app/semantic_business_understanding_engine.py`
2. request/response schemas in `experimental/qwen_agent_runtime/app/schemas.py`
3. endpoint in runtime service/main as needed

## 12. First Implementation Recommendation

Start with NBU-0 and NBU-1 only.

Reason:

1. they are low-risk
2. they do not change live behavior
3. they create the shared shape needed for all later slices
4. they prevent us from drifting back into scattered one-off routing fixes

After NBU-1 passes, implement NBU-2 in shadow mode.

Do not activate behavior changes until NBU-3 and NBU-4 exist.

## 13. Required Companion Guide

The implementation must follow the companion onboarding guide:

`qwen_erp_nbu_integration_and_new_family_onboarding_guide_2026-04-30.md`

That guide defines how current and future business families plug into NBU without hardcoding family-specific behavior.

The companion guide is required because NBU must become a project-wide semantic control layer, not a patch for the current finance, customer-risk, inventory, or master-data failures.

## 14. Definition Of Success

The mini-phase is successful when a user can ask practical ERP/business questions in varied natural wording and the assistant consistently does one safe, professional thing:

1. answer correctly
2. ask a useful clarification
3. requery governed evidence
4. explain a governed boundary
5. show supported alternatives
6. politely reject out-of-scope requests

The assistant should not appear to be a template machine, but it also must not pretend to know unsupported facts.
