# V1-IB-C-2 Runtime Integration Implementation

Decision target:

`v1_ib_c_2_runtime_integration_implementation_ready_for_counterpart_qa_review`

## Scope

V1-IB-C-2 implements the first runtime integration slice for the accepted V1-IB-A/Q validator foundation and accepted V1-IB-B/B-B evidence-only proposal classifier.

This slice does not claim enterprise closure. It is runtime integration evidence only and still needs Counterpart/QA review plus later adversarial/runtime/UAT gates.

## Files Changed

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_integration.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_final_emission_contract_veto.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_2_runtime_integration_implementation_2026-05-29.md`

No `intent_boundary_contract.py` or `intent_boundary_proposal_classifier.py` edits were made.

## Call Sites Touched

- `service.py:52`: imports the V1-IB runtime integration glue.
- `service.py:719`: missing/empty context-reuse boundary now fails closed.
- `service.py:725`: missing/empty report-routing boundary now fails closed.
- `service.py:3979`: legacy user-intent boundary is built only as restrictive legacy metadata.
- `service.py:3980`: V1-IB runtime boundary is built from the raw user message.
- `service.py:3981`: V1-IB boundary is merged with legacy metadata, with V1-IB blocking authority dominant.
- `service.py:3985`: redaction-safe V1-IB contract metadata is prepared for the turn.
- `service.py:4068`: trace-inspection pre-payloads include redaction-safe V1-IB metadata.
- `service.py:4579`: pre-routing boundary gate continues to run before entity/report routing.
- `service.py:4591`: blocked pre-routing responses include redaction-safe V1-IB metadata.
- `authorized_emission.py:364`: final-emission veto lookup now prefers a carried V1-IB boundary payload.
- `authorized_emission.py:386`: if no carried boundary exists, final emission rebuilds V1-IB and merges legacy restrictively instead of using legacy as an allow source.

## Authority Flow

Runtime authority now follows one path:

1. Raw user text enters `handle_qwen_user_message`.
2. `build_intent_boundary_proposal(...)` produces evidence only.
3. `validate_intent_boundary_contract(...)` produces the only route-authority flags.
4. `intent_boundary_runtime_integration.py` normalizes only redaction-safe validator metadata.
5. Existing service gates read the merged V1-IB-dominant boundary.
6. Final emission prefers the carried same boundary; missing carried boundary fails closed by rebuilding V1-IB rather than trusting legacy routing.

The classifier, legacy `user_intent_boundary.py`, semantic output, visible context, report selector, model output, and final answer text cannot authorize a route in this slice.

## Fail-Closed Behavior

The runtime glue sets all authority flags false when any required authority path is missing or invalid:

- classifier missing
- classifier exception
- validator missing
- validator exception
- contract missing
- contract invalid
- unsafe or ambiguous contract
- mixed intent
- replay missing or blocked
- non-redaction-safe trace
- legacy boundary restricts after V1-IB allow
- final-emission contract missing from carried metadata

Blocked flags:

- `report_routing_allowed=false`
- `context_reuse_allowed=false`
- `model_reasoning_allowed=false`
- `final_emission_allowed=false`
- `required_answer_mode != governed_erp_answer`
- `authority_decision != allow_report`

## Trace Redaction

Allowed runtime metadata is whitelisted and redaction-safe:

- contract version
- raw/normalized hashes
- clause count
- route flags
- authority decision
- validator status
- replay status/decision
- ambiguity/mixed/unsafe booleans
- non-sensitive reason codes
- redaction status

Forbidden payloads are not copied into V1-IB metadata:

- raw business text
- ERP rows
- selected answer text
- report payloads
- rendered artifacts
- narratives
- grounded evidence
- visible-context raw evidence on blocked turns
- hidden reasoning

Final-emission veto tests prove selected-answer text, selected rows, rendered payloads, narratives, and grounded evidence do not survive a V1-IB veto.

## Test Matrix

Added runtime integration tests cover:

- safe factual ERP prompt can route only from validator-owned replay-safe contract flags
- safe factual ERP prompt routes through the accepted classifier/validator replay fixture
- classifier output alone cannot route
- replay-missing contract blocks even if other fields claim report allowed
- missing classifier fails closed
- classifier exception fails closed
- missing validator fails closed
- validator exception fails closed
- V1-IB block overrides legacy allow
- legacy block conservatively restricts V1-IB allow
- service gate helpers fail closed on missing contract
- visible-context reuse requires contract context allow
- real classifier plus accepted validator default-fails-closed for mixed prompt without proof
- runtime metadata is redaction-safe
- final emission veto blocks unsafe selected report answer
- final emission veto sanitizes selected rows/rendered/narrative/grounded evidence/selected answer text
- raw-message fallback uses V1-IB fail-closed path, not legacy allow
- allowed carried V1-IB contract still must pass existing final-answer authority

## Verification Results

- New V1-IB-C runtime tests: PASS, `14 passed`
- V1-IB contract validator tests: PASS, `100 passed`
- V1-IB proposal-classifier tests: PASS, `12 passed`
- Combined V1-IB runtime + contract + classifier run: PASS, `126 passed`
- Python compile for touched files: PASS
- Qwen enterprise guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Raw assistant append scan: PASS, only:
  - `authorized_emission.py:271`
  - `authorized_emission.py:327`
- `git diff --check`: PASS
- Path-aware excluded/artifact scan: PASS
- Staged files: PASS, `0`

## Dirty Worktree Note

The worktree remains dirty and is not package-ready. Existing untracked governance history and old rejected V1-IB-B structural-classifier artifacts remain unaccepted historical scratch unless separately approved.

An unrelated pre-existing modified file remains outside this C-2 scope:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py`

## Explicit Non-Actions

No browser/UAT, staging, commit, push, packaging, deployment, strict enforcement, or V2 work occurred.

No runtime lane now grants authority from classifier output, legacy intent logic, visible context, report selector confidence, semantic-safe output, model judgment, or selected final answer text.
