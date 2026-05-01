# Qwen ERP NBU Front Controller Mini-Phase Plan

Status: active implementation plan; FC0 through FC5 complete
Date: 2026-05-01
Scope: promote Natural Business Understanding from downstream rescue layer to governed semantic turn controller

## 1. Purpose

The assistant has many mature governed ERP families, but natural conversation is still fragmented across older routing lanes.

The target architecture is:

1. user question
2. NBU semantic interpretation and context selection
3. deterministic contract, registry, evidence, and authority validation
4. governed family/action execution
5. business-safe response rendering

NBU becomes the understanding brain, not the final law.

The governing principle is:

`NBU understands. Contracts verify. Governed families execute. Renderers explain.`

## 2. Honest Current Baseline

Current NBU exists and is partially activated, but it is not yet the primary dispatcher.

Observed browser failures show that the assistant still struggles with:

1. choosing customer risk versus AR aging for broad risk wording
2. separating collection recommendations from supporting ERP facts
3. replacing generic runtime failure with professional prediction boundaries
4. resolving rank/row references from the current visible table
5. resolving explicit prior artifacts such as "above AR table"
6. escaping stale context after topic switches
7. turning missing fields into governed requery plans when sources exist
8. avoiding internal technical words in user-facing fallback

## 3. Enterprise Controls

NBU front-controller activation must be controlled, measured, and reversible.

Required controls:

1. schema and output contract hardening
2. business conversation quality standard
3. evaluation harness and failure taxonomy
4. always-on shadow before activation
5. NBU versus current-router scorecard
6. arbitration layer before NBU dominance
7. shared context graph before deep follow-up activation
8. canary/feature-flag levels
9. latency and runtime-unavailable behavior
10. no user-facing internal architecture vocabulary

## 4. Final Mini-Phase Slices

### FC0: Failure Inventory And Baseline

Status: complete

Purpose:

Lock current known failures into a reusable, non-keyword baseline registry.

Deliverables:

1. structured baseline case registry
2. failure-class taxonomy
3. expected action and target per case
4. green schema tests for the baseline registry
5. documentation that each case represents a shared behavior class

Exit gate:

1. all known browser failures are represented
2. no case is framed as a one-off phrase patch
3. automated validation passes

### FC0.25: Business Conversation Quality Standard

Status: complete

Purpose:

Define what good business conversation means before activating NBU control.

Required standards:

1. answer or route clear business questions
2. resolve vague but context-resolvable questions
3. ask one useful clarification when ambiguous
4. explain what can be answered when unsupported
5. separate ERP facts from recommendations, predictions, approvals, and policy decisions
6. never expose internal words such as contract, runtime, artifact, or governed boundary
7. never repeat a table when the user asked for explanation
8. never switch to the wrong latest context when the user names a prior artifact
9. never pretend confidence when evidence is missing

Implemented artifacts:

1. `qwen_chat/natural_business_understanding_quality_standard.py`
2. `tests/test_natural_business_understanding_quality_standard.py`

Implementation note:

1. the quality standard is represented in code, not only prose
2. every allowed NBU action has quality expectations
3. every FC0 baseline failure class is covered by at least one quality rule
4. user-facing response text can be checked for internal vocabulary such as contract, runtime, artifact, governed boundary, and policy artifact

### FC0.5: NBU Schema, Prompt, Confidence, And Renderer Hardening

Status: complete

Purpose:

Harden the model contract before always-on shadow.

Deliverables:

1. strict allowed actions
2. strict candidate interpretation schema
3. confidence semantics by action type
4. model prompt/output hardening
5. renderer quality gate

Implemented artifacts:

1. `qwen_chat/natural_business_understanding_schema_hardening.py`
2. `tests/test_natural_business_understanding_schema_hardening.py`
3. runtime trace audit hook in `qwen_chat/natural_business_understanding_runtime.py`

Implementation note:

1. every allowed NBU action now has a hardening rule
2. each action rule defines compatible response modes, minimum confidence, authority expectations, evidence expectations, and context requirements where relevant
3. current-artifact answers require resolved context and visible evidence support before they can be considered hardened
4. governed requery actions require a ready requery support path before they can be considered hardened
5. boundary and clarification responses are checked against the business conversation quality gate so internal architecture vocabulary does not leak to users
6. the NBU runtime now records `schema_hardening_assessment` beside the professional response and activation assessment for future scorecard/arbitration work

Verification:

1. local compile passed for the FC0.5 module, runtime update, and tests
2. backend compile passed for the FC0.5 module, runtime update, and tests
3. backend NBU regression suite passed with 82 tests on 2026-05-01

### FC0.75: NBU Evaluation Harness And Failure Taxonomy

Status: complete

Purpose:

Evaluate NBU as both a model and a control system.

Failure buckets:

1. model misunderstanding
2. missing registry metadata
3. context graph failure
4. validation/gate failure
5. route execution failure
6. renderer quality failure
7. policy/evidence gap
8. latency or runtime unavailable

Implemented artifacts:

1. `qwen_chat/natural_business_understanding_evaluation_harness.py`
2. `tests/test_natural_business_understanding_evaluation_harness.py`

Implementation note:

1. the failure taxonomy is represented in code and includes all 8 enterprise buckets
2. baseline cases can now be evaluated against NBU traces using expected action, expected target, schema hardening, response quality, policy/evidence status, requery readiness, and latency/runtime availability
3. evaluation reports separate blocking failure buckets from diagnostic buckets, so an expected policy boundary can pass while still recording a policy/evidence gap for governance visibility
4. suite summaries count pass/fail rate and bucket frequency so future FC1/FC1.5 shadow runs can compare NBU against the current router systematically
5. this remains non-activating: it measures NBU behavior and does not change user-facing routing

Verification:

1. local compile passed for the FC0.75 harness and tests
2. local harness validation returned ok with 8 taxonomy buckets and 10 baseline cases
3. backend compile passed for the FC0.75 harness and tests
4. backend NBU regression suite passed with 91 tests on 2026-05-01

### FC1: Always-On NBU Shadow

Status: complete

Purpose:

Run NBU for every user message without changing user-facing behavior.

Implemented artifacts:

1. `build_nbu_always_on_shadow_trace` in `qwen_chat/natural_business_understanding_service_activation.py`
2. service-level FC1 wiring in `qwen_chat/service.py`
3. updated service activation tests in `tests/test_natural_business_understanding_service_activation.py`

Implementation note:

1. NBU now builds one shadow trace early in the chat turn after conversation-control message normalization
2. the trace is appended as an audit/tool payload across the main service paths without changing the assistant answer
3. the trace includes `always_on_shadow_audit` with latency, action, response mode, schema-hardening status, activation state, and explicit `live_behavior_changed = False`
4. later NBU presentation activation reuses the precomputed FC1 trace instead of calling the NBU runtime a second time
5. runtime failures remain fail-open: the service records an observe-only trace and existing governed routing continues

Verification:

1. local compile passed for `service.py`, NBU service activation, and updated tests
2. backend compile passed for `service.py`, NBU service activation, and updated tests
3. backend NBU regression suite passed with 94 tests on 2026-05-01
4. Frappe bench service smoke passed via `run_phase4_compiled_rollout_governance_selftests` on 2026-05-01

### FC1.5: NBU Versus Current Router Scorecard

Status: complete

Purpose:

Score NBU and current router decisions:

1. NBU correct, current router wrong
2. current router correct, NBU wrong
3. both correct
4. both wrong
5. NBU unsafe
6. NBU low-confidence

Implemented artifacts:

1. `qwen_chat/natural_business_understanding_scorecard.py`
2. `tests/test_natural_business_understanding_scorecard.py`

Implementation note:

1. the scorecard uses the FC0 baseline cases as the correctness oracle
2. live production shadow traces can show agreement or disagreement, but true correct/wrong labels require a labelled case or approved expectation
3. current-router outcomes are converted into the same evaluation shape as NBU traces, so both are judged by the same front-controller harness
4. scorecard outcomes are explicit: `both_correct`, `nbu_correct_current_wrong`, `current_correct_nbu_wrong`, `both_wrong`, `nbu_unsafe`, and `nbu_low_confidence`
5. low-confidence NBU is separated from unsafe NBU so future arbitration can decide whether to clarify, keep the current route, or hold NBU in shadow
6. this remains non-activating: it does not change user-facing routing or responses

Verification:

1. local compile passed for the FC1.5 scorecard module and tests
2. backend compile passed for the FC1.5 scorecard module and tests
3. targeted backend scorecard tests passed with 10 tests on 2026-05-01
4. backend NBU regression suite passed with 104 tests on 2026-05-01

### FC2: Arbitration And Disagreement Audit

Status: complete

Purpose:

Choose whether to trust NBU, trust existing route, clarify, or fail safely.

Implemented artifacts:

1. `qwen_chat/natural_business_understanding_arbitration.py`
2. `tests/test_natural_business_understanding_arbitration.py`

Implementation note:

1. arbitration now sits above the FC1.5 scorecard as a control-policy layer
2. scorecard outcomes are translated into one of five decisions: `trust_current_router`, `trust_nbu`, `ask_clarification`, `safe_boundary`, or `shadow_only`
3. NBU can only be trusted when its required action lane is enabled by the current activation level
4. activation levels are explicit: `shadow_only`, `presentation_only`, `current_artifact_answer`, `governed_requery`, `fresh_query`, and `full_front_controller`
5. unsafe NBU output fails safely, low-confidence NBU does not win by accident, and both-wrong cases clarify or boundary instead of guessing
6. FC2 still does not change live user behavior; it records whether a behavior change would be authorized by policy and leaves actual service activation for later slices

Verification:

1. local compile passed for the FC2 arbitration module and tests
2. backend compile passed for the FC2 arbitration module and tests
3. targeted backend arbitration tests passed with 10 tests on 2026-05-01
4. backend NBU regression suite passed with 114 tests on 2026-05-01

### FC3: Shared Context Graph Backbone

Status: complete

Purpose:

Support references such as:

1. latest result
2. previous AR table
3. current supplier list
4. rank 2
5. that product
6. go back to the customer

Implemented artifacts:

1. `qwen_chat/natural_business_understanding_context_graph.py`
2. `tests/test_natural_business_understanding_context_graph.py`
3. public context-resolution helper wrappers in `qwen_chat/natural_business_understanding_context_resolution.py`

Implementation note:

1. the graph indexes current artifacts, previous artifacts, visible rows, row-derived entities, recent-focus nodes, and candidate options
2. artifact aliases are derived from metadata such as title, report name, family ID, dimensions, and generated acronyms rather than hardcoded business phrase mappings
3. explicit references such as "above AR table" can resolve to a compatible prior artifact instead of blindly using the latest visible result
4. unqualified row/rank references still prefer the current artifact unless the message names or implies a prior artifact
5. deictic entity references such as "that product" can resolve from recent-focus nodes
6. ambiguous visible references such as "this customer" return useful options instead of repeating an unrelated report
7. FC3 remains a backbone slice: it provides shared context resolution that later activation slices can consume, but it does not yet change live service behavior

Verification:

1. local compile passed for the FC3 context graph module, context-resolution helper wrappers, and tests
2. backend compile passed for the FC3 context graph module, context-resolution helper wrappers, and tests
3. targeted backend context graph tests passed with 8 tests on 2026-05-01
4. backend NBU regression suite passed with 122 tests on 2026-05-01

### FC4: Safe Presentation And Boundary Activation

Status: complete

Purpose:

Activate safe non-execution responses only.

Implemented artifacts:

1. FC4 presentation-gate updates in `qwen_chat/natural_business_understanding_service_activation.py`
2. shared activation-lane helpers in `qwen_chat/natural_business_understanding_arbitration.py`
3. updated activation and arbitration tests in `tests/test_natural_business_understanding_service_activation.py` and `tests/test_natural_business_understanding_arbitration.py`

Implementation note:

1. NBU can now activate only safe presentation actions under the `presentation_only` activation level
2. allowed FC4 actions are clarification, supported options, safe boundary, capability guidance, and out-of-scope responses
3. FC4 does not execute governed queries, does not perform requery, and does not answer from current artifacts
4. current-artifact direct answers were deliberately removed from the live try-path and remain deferred to FC5
5. every activated FC4 response records activation level, required action lane, allowed lanes, and `live_behavior_changed_by_fc4`
6. presentation activation still requires the NBU professional response to be safe-to-show and free of user-facing quality warnings

Verification:

1. local compile passed for FC4 arbitration, service activation, and tests
2. backend compile passed for FC4 arbitration, service activation, and tests
3. targeted backend activation/arbitration tests passed with 22 tests on 2026-05-01
4. backend NBU regression suite passed with 125 tests on 2026-05-01

### FC5: Current Artifact Answer Activation

Status: complete

Purpose:

Answer from visible/current artifact facts after row/entity/evidence validation.

Implemented artifacts:

1. FC5 current-artifact answer gates in `qwen_chat/natural_business_understanding_service_activation.py`
2. updated activation-lane support in `qwen_chat/natural_business_understanding_arbitration.py`
3. expanded activation tests in `tests/test_natural_business_understanding_service_activation.py`

Implementation note:

1. NBU can now activate direct answers from already-visible current-artifact rows under the `current_artifact_answer` activation level
2. activation requires action `answer_from_current_artifact`, response mode `direct_answer`, schema hardening OK, current-artifact evidence support, safe-read authority, resolved context, and displayable row facts
3. FC5 does not execute governed queries and does not requery ERP
4. FC5 records activation level, required lane, allowed lanes, `live_behavior_changed_by_fc5`, and `execution_not_performed`
5. FC4 presentation responses still work under the higher `current_artifact_answer` activation level because presentation is an allowed lower-risk lane
6. missing fields, unresolved context, unsafe schema, or unsupported authority remain fail-open to the existing assistant flow
7. FC5 live-precedence hardening now places the safe NBU activation seam before broad legacy front-door/family routers, so visible row/rank/focus follow-ups cannot fall through into unrelated financial statement or supplier-list lanes first
8. FC5 now uses the shared context graph to resolve visible current and prior artifacts, including natural references such as "second position in the above table" and "second position in the above AR table"
9. ambiguous deictic references such as "this customer" remain safe clarification flows unless a recent selected entity is proven

Verification:

1. local compile passed for FC5 service activation and tests
2. backend compile passed for FC5 service activation and tests
3. targeted backend activation/arbitration tests passed with 25 tests on 2026-05-01
4. backend NBU regression suite passed with 128 tests on 2026-05-01
5. FC5 live-precedence refinement compile passed for `service.py`, `natural_business_understanding_service_activation.py`, `natural_business_understanding_context_graph.py`, and related tests on 2026-05-01
6. focused backend context-graph/service-activation regression suite passed with 26 tests on 2026-05-01
7. full backend NBU regression suite passed with 132 tests on 2026-05-01
8. post-restart service smoke passed on 2026-05-01

### FC6: Governed Requery Planning Activation

Status: later

Purpose:

Move from current artifact to an approved source when current evidence is insufficient.

### FC7: Fresh Query Routing Activation

Status: later

Purpose:

Let NBU route new standalone questions to governed families after validation.

### FC8: Recommendation, Prediction, And Policy Gate Framework

Status: later

Purpose:

Keep unsupported decisions safe while showing useful ERP facts.

### FC9: Full Automated And Manual Quality Gate

Status: later

Purpose:

Verify full business conversation readiness before Phase 4 complex questions.

### FC10: Production Canary, Monitoring, And Rollback

Status: later

Purpose:

Deploy front-controller behavior safely with monitoring and rollback controls.

## 5. FC0 Implementation Record

Implemented artifacts:

1. `qwen_chat/natural_business_understanding_front_controller_cases.py`
2. `tests/test_natural_business_understanding_front_controller_cases.py`

The first baseline registry includes cases for:

1. customer risk broad ask
2. collection recommendation boundary
3. default prediction boundary
4. supplier context switch
5. rank 2 current artifact answer
6. above AR table previous context
7. credit limit governed requery
8. customer risk correction
9. AR/AP health composite
10. ambiguous "this customer" clarification

Verification:

1. local compile passed for the FC0 registry and tests
2. backend compile passed for the FC0 registry and tests
3. backend NBU regression suite passed with 67 tests on 2026-05-01

## 6. Current Next Step

Continue to FC6.

FC0 through FC5 are now in place, including the FC5 live-precedence hardening discovered during manual browser UAT. The next step is FC6 governed requery planning activation, where NBU may request an approved ERP source only when current visible evidence is insufficient and the required source path is proven.
