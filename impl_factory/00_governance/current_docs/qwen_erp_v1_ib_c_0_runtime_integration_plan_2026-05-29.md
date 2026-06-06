# V1-IB-C-0 Runtime Integration Plan

## Decision Target

`v1_ib_c_0_runtime_integration_plan_ready_for_counterpart_qa_owner_review`

## Accepted Foundation

V1-IB-A/Q is accepted as the contract/validator authority foundation.

The accepted authority model is:

- proposer/model output cannot authorize routing
- verifier output is consistency evidence only
- proof, analysis, execution, and replay-status records are provenance only
- semantic-safe output cannot authorize routing
- lexical, regex, keyword, synonym, phrase, punctuation, and no-alarm logic cannot authorize routing
- only positive validator-owned safe factual replay plus all accepted contract invariants can allow governed ERP routing
- unknown, ambiguous, unsafe, mixed, unresolved, stale, conflicting, non-redaction-safe, or unproven natural-language ERP intent fails closed

V1-IB-B/B-B is accepted as an evidence-only proposal-classifier checkpoint.

The accepted classifier boundary is:

- `build_intent_boundary_proposal(raw_message)` may produce structured proposal evidence
- classifier output has no route-authority fields
- classifier cannot authorize report routing, context reuse, model reasoning, final emission, governed ERP answer mode, or `authority_decision=allow_report`
- validator remains the sole route authority

## Proposed Future Runtime Call Sites

This plan identifies future call sites only. No runtime files were edited in C-0.

Future raw user message intake anchor:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py:3966`, `handle_qwen_user_message`

Future pre-routing/user-intent gate anchors:

- `service.py:714`, `_user_intent_boundary_context_reuse_allowed`
- `service.py:720`, `_user_intent_boundary_report_routing_allowed`
- `service.py:726`, `_user_intent_boundary_pre_routing_response_required`
- `service.py:3506`, `_emit_user_intent_boundary_pre_routing_response`

Future visible-context reuse anchors:

- `service.py:743`, `_visible_context_followup_should_preempt_clarification`
- `service.py:752`, `_artifact_boundary_should_yield_to_visible_context`
- `service.py:768`, `_compiled_fresh_query_should_yield_to_visible_context`
- `service.py:777`, `_runtime_gate_should_yield_to_visible_context`
- `service.py:4055`, `service.py:4191`, `service.py:4324`, and related call sites currently checking user-intent context reuse

Future report routing anchors:

- `service.py:720`, `_user_intent_boundary_report_routing_allowed`
- `service.py:4831`, `_try_activate_nbu_governed_requery_response`
- `service.py:4864`, governed report/requery branch guarded by report-routing permission
- `service.py:5423` and `service.py:5466`, governed scope decision construction before local governed-scope/report handling

Future model-reasoning anchors:

- `service.py:853`, `_reasoning_activation_has_execution_authority`
- `service.py:894`, `_frontdoor_should_yield_to_reasoning_activation`
- `service.py:979`, `_current_artifact_evidence_should_preempt_reasoning`

Future final-answer / authorized-emission anchors:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py:210`, `emit_authorized_assistant_answer`
- `authorized_emission.py:364`, `_user_intent_boundary_for_final_emission_veto`
- `authorized_emission.py:394`, `_user_intent_final_emission_veto_required`
- `authorized_emission.py:474`, `emit_authorized_assistant_answer`

Future implementation must first audit the duplicate `emit_authorized_assistant_answer` definitions before editing. This C-0 plan does not edit or approve any final-emission implementation.

## Integration Order

Future implementation must follow this order:

1. Capture the raw user message at runtime intake.
2. Build proposal evidence from the raw user message using the accepted V1-IB-B proposal classifier.
3. Validate the proposal with the accepted V1-IB-A/Q `IntentBoundaryContract` validator.
4. Store redaction-safe contract metadata for the turn.
5. Gate visible-context reuse from the validated contract.
6. Gate report routing from the validated contract.
7. Gate model reasoning from the validated contract.
8. Before authorized final answer emission, verify the same contract or fail closed.

No runtime lane may treat classifier output, semantic-safe output, old user-intent boundary output, or lexical/no-alarm evidence as route authority.

## Single Authority Path

The same validated intent-boundary contract must control:

- pre-routing boundary/clarification behavior
- visible-context reuse
- report routing
- model reasoning permission
- final-emission veto
- redaction-safe trace metadata

Runtime lanes must not reinterpret raw text independently after the contract is built. If any lane receives a selected answer that conflicts with the validated contract, the final-emission path must veto or fail closed.

## Failure Behavior

If the classifier is missing, validator is missing, contract is invalid, replay is missing, replay is ambiguous, replay is unsafe, replay is unproven, proof is stale, proof is conflicting, trace is non-redaction-safe, or any accepted invariant fails:

- `report_routing_allowed=false`
- `context_reuse_allowed=false`
- `model_reasoning_allowed=false`
- `final_emission_allowed=false`
- answer mode must be clarification or boundary
- governed ERP answer must not be emitted

Failure paths must not dump reports, activate visible context, call enterprise answer reasoning, or leak selected-answer evidence.

## Trace / Redaction Policy

Future trace metadata must be redaction-safe and minimal.

Allowed trace fields should include:

- contract version
- contract id or hash
- raw/normalized message hashes
- validator status
- authority decision
- route flags
- required answer mode
- replay decision/status
- trace redaction status
- non-sensitive blocking reason codes

Forbidden trace content:

- raw business text
- raw ERP row values
- selected report rows
- selected-answer text
- rendered payloads
- business evidence payloads
- selected-answer narratives
- helper/model trace payloads containing business fields

If a veto fires after a selected answer exists, the emitted payload must use the existing sanitized veto pattern and must not preserve selected-answer payloads.

## Required Future Implementation Tests

Before any V1-IB-C runtime implementation can be accepted, tests must prove:

- safe factual prompt routes only after validated contract permission
- unsafe prompt blocks before report routing
- mixed factual plus unsafe prompt blocks before report routing
- visible-context unsafe follow-up blocks context reuse
- missing classifier fails closed
- missing validator fails closed
- invalid contract fails closed
- missing or ambiguous replay fails closed
- final-emission veto blocks if selected answer conflicts with the contract
- trace metadata includes contract id/status and route flags
- trace metadata does not leak raw business text, selected report payloads, rows, artifacts, narratives, or evidence
- existing direct assistant inventory remains `0 / 1 / 27`
- raw append scan remains only authorized sinks

## Dirty Worktree Note

The current dirty worktree is not package-ready.

Accepted V1-IB-A/Q and V1-IB-B/B-B artifacts coexist with older V1-R artifacts, pre-existing runtime changes, and rejected historical V1-IB-B structural classifier artifacts. The rejected structural classifier artifacts remain rejected scratch and must not be treated as accepted integration design.

Rejected artifacts include:

- `qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
- `qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
- `qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`
- `intent_boundary_structural_classifier.py`
- `test_v1_ib_structural_classifier.py`

No packaging, staging, commit, push, deployment, strict enforcement, browser/API UAT, or V2 work occurred in this C-0 slice.

## Verification

C-0 is report-only.

Verification performed:

- Report present: PASS
- `git diff --check`: PASS
- Path-aware excluded/artifact scan: PASS, clean for `__pycache__`, `.pyc`, generated governance artifacts, UAT/browser artifacts
- Staged files: PASS, `0`
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`

## Explicit Next Step

If this V1-IB-C-0 plan is accepted, the next step is V1-IB-C-1 implementation boundary request with exact files and tests.

V1-IB-C-0 does not approve integration implementation by default.
