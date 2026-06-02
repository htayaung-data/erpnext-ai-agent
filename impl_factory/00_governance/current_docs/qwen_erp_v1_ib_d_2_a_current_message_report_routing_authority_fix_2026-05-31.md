# V1-IB-D-2-A Current-Message Report-Routing Authority Fix

Decision target:
`v1_ib_d_2_a_current_message_report_routing_authority_fix_ready_for_counterpart_review`

## 1. Scope And Boundary

V1-IB-D-2-A is the narrow fix for the D-2 blocker where stale report-allow V1-IB metadata could be accepted as report-routing authority for a different current user message.

Files changed in this slice:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_cross_lane_contract_identity.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_2_a_current_message_report_routing_authority_fix_2026-05-31.md`

No `authorized_emission.py`, `intent_boundary_contract.py`, `intent_boundary_runtime_integration.py`, `intent_boundary_proposal_classifier.py`, `user_intent_boundary.py`, rejected structural classifier, business report generation, report selector semantics, or compiled-query behavior was modified. Compiled query remains unchanged except that service gates now require current-message report authority before compiled routing can be reached.

No keyword, regex, synonym, punctuation, phrase, or no-alarm route authority was added. No compatibility fallback for stale or missing contracts was added. No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, or V2 work occurred.

## 2. Blocker Summary

D-2 preserved this failing evidence:

```text
current message: Show EC7H-ITEM-A item sales
stale allow contract source: Show EC7H-SUP-A payable status
_user_intent_boundary_report_routing_allowed(stale_boundary) returned True
_user_intent_boundary_pre_routing_response_required(stale_boundary) returned False
service reached compiled_first_turn
expected: boundary/control path, no compiled query, no report routing
```

Root cause:

- `service.py:_user_intent_boundary_report_routing_allowed` checked only the `report_routing_allowed` boolean.
- `_user_intent_boundary_pre_routing_response_required` trusted that boolean-only helper.
- Compiled/report-routing service gates could therefore accept stale report-allow metadata if stale metadata reached the runtime boundary object.

## 3. Exact Fix

`_user_intent_boundary_report_routing_allowed(...)` now accepts `raw_message` and fails closed unless all current-message authority conditions are true:

- boundary is a non-empty dict
- current raw message is provided and non-blank
- `type == qwen_user_intent_boundary_contract`
- `raw_message_hash == hash_text(raw_message)`
- `normalized_message_hash == hash_text(normalize_message(raw_message))`
- `validator_status == valid`
- `trace_redaction_status == safe`
- `report_routing_allowed == true`
- `required_answer_mode == governed_erp_answer`
- `authority_decision == allow_report`
- `replayed_raw_message_safety_final_decision == safe`
- `decision_intent == false`
- `advice_intent == false`
- `business_action_intent == false`
- `policy_boundary_intent == false`
- `mixed_intent_detected == false`
- `ambiguity_status` is absent, blank, or `none`

`_user_intent_boundary_pre_routing_response_required(...)` now passes the current raw message into the strict report-routing helper. It cannot skip boundary response from `report_routing_allowed=true` unless current-message identity and validator-owned report authority are proven.

`_user_intent_boundary_pre_routing_safe_metadata(...)` was added in `service.py` to ensure stale allow metadata does not appear as live route-authority flags in a pre-routing boundary/control response. If a stale/mismatched/non-current allow-shaped boundary is blocked, exposed metadata is fail-closed:

```text
context_reuse_allowed=false
report_routing_allowed=false
model_reasoning_allowed=false
final_emission_allowed=false
required_answer_mode=clarification
authority_decision=block
current_message_authority_status=fail_closed
```

This is identity/contract validation only. It does not classify language and does not add lexical/keyword authority.

## 4. Call Sites Updated / Reviewed

Updated in `service.py`:

- `_user_intent_boundary_report_routing_allowed` at line 787: now requires current raw message and full V1-IB report authority invariants.
- `_user_intent_boundary_pre_routing_response_required` at line 815: now passes `raw_message` into the strict report-routing helper.
- `_user_intent_boundary_pre_routing_safe_metadata` at line 833: fail-closes stale allow-shaped metadata before boundary/control emission.
- Pre-frontdoor model reasoning/report authority condition at line 4361: now calls `_user_intent_boundary_report_routing_allowed(user_intent_boundary, raw_message=raw_msg)`.
- Pre-routing response gate at line 4734: now passes `raw_message=raw_msg`.
- Compiled fresh-query breakout at line 5035: now calls `_user_intent_boundary_report_routing_allowed(user_intent_boundary, raw_message=raw_msg)`.

Visible-context behavior remains unchanged and still uses the previously accepted current-message context helper. Final-emission behavior remains unchanged and still uses the accepted current-message final veto path.

## 5. Test Updates

`test_v1_ib_d_cross_lane_contract_identity.py` was updated to assert the accepted D-2-A behavior:

- report helper returns false when raw message is omitted
- report helper returns false when `raw_message=None`
- report helper returns false when raw message is blank
- raw hash mismatch blocks
- normalized hash mismatch blocks
- `trace_redaction_status != safe` blocks
- missing `type` blocks
- `validator_status != valid` blocks
- `required_answer_mode != governed_erp_answer` blocks
- `authority_decision != allow_report` blocks
- `replayed_raw_message_safety_final_decision != safe` blocks
- decision, mixed, and ambiguous intent flags block
- current safe factual report control still passes
- stale allow cannot skip pre-routing boundary response

Preserved D-2 failing tests now pass:

- `test_report_routing_helper_requires_current_contract_identity`
- `test_pre_routing_gate_must_not_skip_boundary_response_for_stale_allow_contract`
- `test_stale_report_allow_contract_must_not_reach_compiled_query`

## 6. Verification Results

D-2 tests:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_cross_lane_contract_identity \
  ai_assistant_ui.tests.test_v1_ib_d_authority_surface_consistency \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_authority_consistency
```

Result:

```text
Ran 9 tests in 0.073s
OK
```

Accepted baseline:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_prerouting \
  ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_final_emission \
  ai_assistant_ui.tests.test_v1_ib_runtime_integration \
  ai_assistant_ui.tests.test_v1_ib_runtime_final_emission_contract_veto \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_contract_validator \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_proposal_classifier \
  ai_assistant_ui.tests.test_authorized_emission_contracts \
  ai_assistant_ui.tests.test_service_control_authorized_emission_contracts
```

Result:

```text
Ran 157 tests in 0.607s
OK
```

Python compile:

```text
PY_COMPILE_PASS
```

Qwen enterprise guardrail:

```text
Qwen enterprise guardrail audit: PASS
```

Fake-Frappe service import:

```text
FAKE_FRAPPE_IMPORT_PASS
```

Direct assistant inventory:

```text
ACTIVE_RUNTIME_DIRECT_ASSISTANT_APPEND_COUNT=0
INVENTORY_COUNT=1
MIGRATED_AUTHORIZED_PATHS_LENGTH=27
```

Raw assistant append scan:

```text
FORMAL_RAW_SCAN=[
  ("impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py", 271),
  ("impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py", 327)
]
```

Report presence:

```text
report_present=PASS
```

Final git hygiene after report copy:

```text
git diff --check: PASS
git diff --cached --check: PASS
excluded_artifact_scan: PASS
staged_files=0
dirty_worktree_count=138
```

## 7. Boundary Statement

V1-IB-D-2-A fixes only the current-message report-routing authority blocker. It does not claim V1-IB-D closure.

The worktree remains dirty and not package-ready. No UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise closure, or V2 work occurred.
