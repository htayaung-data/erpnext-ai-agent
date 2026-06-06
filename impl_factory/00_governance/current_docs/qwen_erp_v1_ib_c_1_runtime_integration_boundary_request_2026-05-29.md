# V1-IB-C-1 Runtime Integration Implementation Boundary Request

## Decision Target

`v1_ib_c_1_runtime_integration_boundary_request_ready_for_counterpart_qa_review`

## Current State

Accepted foundation:

- V1-IB-A/Q is accepted as the contract/validator authority foundation.
- V1-IB-B/B-B is accepted as the evidence-only proposal-classifier checkpoint.
- V1-IB-C-0 is accepted as the runtime integration plan.

Authority model:

- Classifier output is evidence only.
- Proposer/model output is evidence only.
- Verifier output is consistency evidence only.
- Stored proof/analysis/execution/replay-status records are provenance only.
- Semantic-safe output cannot authorize routing.
- Lexical, regex, synonym, keyword, phrase, punctuation, and no-alarm logic cannot authorize routing.
- The `IntentBoundaryContract` validator is the sole route-authority source.
- Only positive validator-owned safe factual replay plus all accepted validator invariants can allow governed ERP routing.

Dirty runtime files are not accepted by this C-1 slice.

Old V1-IB-B/B-A/B-B structural classifier artifacts remain rejected historical scratch unless explicitly replaced in a later accepted slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py`

## Future File Boundary

Future V1-IB-C runtime integration should be limited to the smallest viable file set.

Proposed runtime files:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py`

Accepted foundation files to import/use, not re-architect:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_contract.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_proposal_classifier.py`

Future helper module only if absolutely necessary:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_integration.py`

Helper-module approval conditions:

- it must be pure runtime glue
- it must not contain route authority independent of `IntentBoundaryContract`
- it must not use lexical/regex/synonym/no-alarm logic to authorize
- it must fail closed if the contract is missing or invalid

Proposed future tests:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_final_emission_contract_veto.py`
- existing focused authorized-emission/final-answer/visible-context tests may be extended only if the C-2 implementation boundary explicitly approves exact edits

Files not approved for future C-2 unless explicitly listed in that future boundary:

- old `intent_boundary_structural_classifier.py`
- old `test_v1_ib_structural_classifier.py`
- old rejected V1-IB-B structural classifier reports
- browser/UAT artifacts
- deployment or packaging manifests

C-1 does not modify any of these files.

## Future Call-Site Boundary

Current source was re-scanned for C-1. These are future anchors only.

Raw user message intake:

- `service.py:3966`, `handle_qwen_user_message`

Accepted proposal/validator APIs:

- `intent_boundary_proposal_classifier.py:380`, `build_intent_boundary_proposal`
- `intent_boundary_contract.py:2911`, `validate_intent_boundary_contract`

Pre-routing branch:

- `service.py:714`, `_user_intent_boundary_context_reuse_allowed`
- `service.py:720`, `_user_intent_boundary_report_routing_allowed`
- `service.py:726`, `_user_intent_boundary_pre_routing_response_required`
- `service.py:3506`, `_emit_user_intent_boundary_pre_routing_response`

Visible-context eligibility:

- `service.py:743`, `_visible_context_followup_should_preempt_clarification`
- `service.py:752`, `_artifact_boundary_should_yield_to_visible_context`
- `service.py:768`, `_compiled_fresh_query_should_yield_to_visible_context`
- `service.py:777`, `_runtime_gate_should_yield_to_visible_context`

Report routing entry:

- `service.py:4831`, `_try_activate_nbu_governed_requery_response`
- `service.py:5423`, `build_governed_scope_decision_contract` provisional scope path
- `service.py:5466`, `build_governed_scope_decision_contract` final scope path

Model reasoning entry:

- `service.py:853`, `_reasoning_activation_has_execution_authority`
- `service.py:894`, `_frontdoor_should_yield_to_reasoning_activation`
- `service.py:979`, `_current_artifact_evidence_should_preempt_reasoning`

Trace metadata construction / tool payload:

- `service.py:1094`, `_append_tool_payload`
- `service.py:1098`, `_append_tool_payload_values`
- `service.py:1106`, `_service_tool_payload_values`

Final authorized emission:

- `authorized_emission.py:72`, `_append_pre_assistant_tool_payloads`
- `authorized_emission.py:84`, `_emission_contract`
- `authorized_emission.py:210`, `emit_authorized_assistant_answer`
- `authorized_emission.py:364`, `_user_intent_boundary_for_final_emission_veto`
- `authorized_emission.py:394`, `_user_intent_final_emission_veto_required`
- `authorized_emission.py:426`, `_user_intent_final_emission_veto_payload`
- `authorized_emission.py:447`, `_user_intent_policy_boundary_payload`
- `authorized_emission.py:474`, `emit_authorized_assistant_answer`

Authorized append sinks:

- `authorized_emission.py:271`
- `authorized_emission.py:327`

Future implementation must first reconcile the duplicate `emit_authorized_assistant_answer` definitions before editing final-emission behavior.

## Future Integration Sequence

Future V1-IB-C implementation must follow this order:

1. Raw user message enters runtime at `handle_qwen_user_message`.
2. Build proposal evidence from raw message with `build_intent_boundary_proposal`.
3. Validate proposal with `validate_intent_boundary_contract`.
4. Store only redaction-safe contract metadata for the turn.
5. Block visible-context reuse unless the validated contract allows context reuse.
6. Block report routing unless the validated contract allows report routing.
7. Block model reasoning unless the validated contract allows model reasoning.
8. Final authorized emission re-checks the same validated contract.
9. Any missing contract, mismatch, stale contract, invalid contract, or selected answer conflict fails closed.

The same validated contract must gate:

- pre-routing
- visible-context reuse
- report routing
- model reasoning
- final emission
- trace metadata

No runtime lane may reinterpret raw text independently or replace the contract authority with classifier output, visible context, report selector output, enterprise model judgment, or final answer text.

## Future Failure Behavior

All failure states below must fail closed:

- missing classifier
- classifier exception
- missing validator
- validator exception
- invalid contract
- unsafe contract
- ambiguous contract
- mixed intent
- missing replay
- stale replay
- conflicting proof
- non-redaction-safe trace
- final-emission contract mismatch
- missing stored contract metadata
- contract hash mismatch between pre-routing and final emission
- selected answer conflicts with contract route flags

Required fail-closed flags:

- `report_routing_allowed=false`
- `context_reuse_allowed=false`
- `model_reasoning_allowed=false`
- `final_emission_allowed=false`
- `required_answer_mode` must not be `governed_erp_answer`
- `authority_decision` must not be `allow_report`

Fail-closed behavior must emit clarification or boundary/control response through authorized emission only. It must not dump arbitrary reports, activate visible context, invoke enterprise governed-answer reasoning, or leak selected-answer payloads.

## Prohibited Runtime Authority Paths

The future integration must never allow these to authorize routing:

- classifier output
- semantic-safe output
- proposer labels
- verifier labels
- stored proof status
- replay-status strings
- old `user_intent_boundary.py`
- old rejected structural classifier files
- lexical/regex/synonym/keyword/punctuation/no-alarm logic
- visible context
- report selector
- enterprise model judgment
- final answer text

Lexical/token logic may only:

- extract IDs
- check spans
- support redaction
- raise conservative alarms
- contribute restrictive evidence
- fail closed

Lexical/token logic must never grant:

- `report_routing_allowed=true`
- `context_reuse_allowed=true`
- `model_reasoning_allowed=true`
- `final_emission_allowed=true`
- `required_answer_mode=governed_erp_answer`
- `authority_decision=allow_report`

## Future Test Matrix

Future implementation cannot be accepted without tests proving:

- safe factual ERP prompt passes only with validator-owned replay-safe contract
- unsafe prompt blocks before report routing
- mixed factual plus unsafe prompt blocks before report routing
- visible-context prompt blocks unless it is an explicit safe read-only follow-up and contract allows context reuse
- report selector cannot override contract
- enterprise model cannot override contract
- final emission veto blocks unsafe selected answer
- selected rows/evidence/rendered payloads do not leak on veto
- missing contract blocks all authority flags
- classifier exception fails closed
- validator exception fails closed
- stale contract hash fails closed
- pre-routing/final-emission contract mismatch fails closed
- semantic-safe cannot compensate for missing/invalid contract
- visible context cannot compensate for missing/invalid contract
- old lexical/structural classifier cannot authorize anything
- direct assistant inventory remains `0 / 1 / 27`
- raw append scan remains only authorized sinks

Required adversarial runtime families:

- safe factual ERP lookup
- unsafe advice/action/legal/manipulation/prediction prompts
- mixed factual plus unsafe prompts
- unsafe visible-context follow-ups
- long-context prior report followed by unsafe prompt
- selected-report answer forced late after blocking contract
- missing classifier/validator/proof/replay conditions

## Trace Policy

Allowed trace fields:

- contract version
- raw/normalized hashes
- clause counts
- route flags
- authority decision
- validator status
- replay status/decision
- redaction status
- safe/unsafe/ambiguous/mixed statuses
- non-sensitive blocking reason codes

Forbidden trace fields:

- raw business text
- ERP rows
- selected answer text
- report payloads
- rendered artifacts
- narratives
- grounded evidence
- helper payloads containing business data
- model chain-of-thought or hidden reasoning
- visible-context raw row evidence on blocked turns

If final-emission veto fires after a selected answer exists, the emission must include only sanitized contract metadata and must not preserve selected-answer `pre_assistant_tool_payloads`, rows, artifacts, narratives, grounded evidence, rendered payloads, or selected answer text.

## Rollback Plan

Future integration must be safe to disable by fail-closed behavior:

- default to blocked route flags when integration state is missing
- no partial permissive mode
- no fallback to old routing authority
- no fallback to old lexical classifier
- no fallback to old `user_intent_boundary.py` as an allow source
- no fallback to visible-context inference
- no fallback to report selector confidence
- no fallback to enterprise model judgment
- no fallback to final answer text

If integration must be disabled, it should preserve authorized clarification/boundary behavior and prevent governed ERP report answers until a valid contract path is restored.

## Verification For C-1

C-1 is report-only.

Verification performed:

- Report present: PASS
- `git diff --check`: PASS
- Staged files: PASS, `0`
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`
- Path-aware excluded/artifact scan: PASS, clean for `__pycache__`, `.pyc`, generated governance artifacts, UAT/browser artifacts

## Final Boundary Statement

V1-IB-C-1 is not implementation approval. It is only a runtime integration implementation boundary request.

If Counterpart/QA accept this boundary, the next slice may propose V1-IB-C implementation with exact approved files and tests. Runtime source must not be edited until that future slice is explicitly approved.
