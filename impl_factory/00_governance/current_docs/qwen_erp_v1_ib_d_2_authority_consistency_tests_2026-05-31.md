# V1-IB-D-2 Authority Consistency Tests

Decision target:
`v1_ib_d_2_authority_consistency_tests_ready_for_counterpart_review`

## 1. Scope And Boundary

V1-IB-D-2 is a tests-only authority consistency slice. It adds D-level tests proving that runtime lanes must use the same current, hash-matching, trace-safe, validated V1-IB contract before any business route can proceed.

Files changed in this slice:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_cross_lane_contract_identity.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_authority_surface_consistency.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_trace_diagnostic_authority_consistency.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_2_authority_consistency_tests_2026-05-31.md`

No runtime/source behavior was changed in D-2. No `service.py`, `authorized_emission.py`, `intent_boundary_contract.py`, `intent_boundary_runtime_integration.py`, `intent_boundary_proposal_classifier.py`, or `user_intent_boundary.py` edits were made in this slice. Existing dirty runtime files remain from earlier accepted slices and are not package-ready.

No keyword, regex, synonym, punctuation, phrase, or no-alarm route authority was added. No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise closure, or V2 work occurred.

## 2. Accepted Authority Model Under Test

D-2 preserves the accepted V1-IB authority model:

- `IntentBoundaryContract` is the sole runtime authority.
- Classifier/proposer output is evidence only.
- Verifier output is evidence/provenance only.
- Semantic-safe/model output cannot authorize.
- Legacy `user_intent_boundary.py` cannot authorize.
- Old rejected `intent_boundary_structural_classifier.py` cannot authorize.
- Report selector, compiled query, governed requery, visible context, model reasoning eligibility, final-answer authority, selected answer text, prior conversation context, artifacts, narratives, rows, grounded evidence, rendered payloads, and trace metadata cannot authorize.
- Missing, stale, mismatched, malformed, non-redaction-safe, unsafe, mixed, ambiguous, unresolved, or unproven V1-IB contracts must fail closed.

Lexical/token logic remains restricted to identifier extraction, span/schema validation, redaction, conservative alarms, and fail-closed validation support. It must never grant route flags or `authority_decision=allow_report`.

## 3. Test Matrix Added

### Cross-Lane Contract Identity

File:
`test_v1_ib_d_cross_lane_contract_identity.py`

Coverage:

- Visible-context helper accepts only a current raw/normalized hash-matching, trace-safe V1-IB context contract.
- Visible-context helper fails closed for omitted raw message, `raw_message=None`, blank raw message, stale raw hash, normalized hash mismatch, non-redaction-safe contract, and malformed contract.
- Report-routing helper is expected to reject stale, normalized-mismatched, non-redaction-safe, and malformed report-allow contracts.
- Pre-routing is expected not to skip the boundary response for a stale allow contract.

Result:
This file exposed a blocker in the report-routing/pre-routing helper path.

### Authority Surface Consistency

File:
`test_v1_ib_d_authority_surface_consistency.py`

Coverage:

- Optimistic semantic/frontdoor/visible/requery/compiled/model signals cannot override a current blocking V1-IB contract.
- Legacy allow metadata cannot expand a V1-IB block through `merge_v1_ib_with_legacy_boundary`.
- Proposal classifier output has no route-authority fields and cannot authorize without validator-owned V1-IB authority.
- Safe report control can proceed only with current V1-IB report authority.
- A stale report-allow contract must not reach compiled-query execution.

Result:
The stale report-allow service replay exposed the same report-routing identity blocker.

### Trace / Diagnostic Authority Consistency

File:
`test_v1_ib_d_trace_diagnostic_authority_consistency.py`

Coverage:

- Final emission veto rejects stale, normalized-mismatched, non-redaction-safe, and blocked V1-IB contracts.
- Final emission sanitizes selected answer, rows, artifacts, rendered payloads, narratives, grounded evidence, and helper payload leak markers on veto.
- A current trace-safe V1-IB allow contract remains a positive control for governed report final emission when existing final-answer authority is valid.

Result:
Final emission remained aligned with the accepted C-2-A current-contract authority model.

## 4. Blocker Found

D-2 found a real authority consistency blocker in report-routing/pre-routing identity proof.

Focused replay:

```text
current message: Show EC7H-ITEM-A item sales
stale contract source message: Show EC7H-SUP-A payable status
stale contract fields:
  type=qwen_user_intent_boundary_contract
  validator_status=valid
  trace_redaction_status=safe
  report_routing_allowed=true
  model_reasoning_allowed=true
  final_emission_allowed=true
  required_answer_mode=governed_erp_answer
  authority_decision=allow_report
  raw_message_hash=hash(stale supplier message)
  normalized_message_hash=hash(normalized stale supplier message)
```

Observed direct helper behavior:

```text
service._user_intent_boundary_report_routing_allowed(stale_boundary) == True
service._user_intent_boundary_pre_routing_response_required(stale_boundary) == False
```

Observed service replay:

```text
build_v1_ib_runtime_boundary(current_raw_message) patched to return stale supplier allow contract
frontdoor and visible/requery helpers disabled
compiled query helper patched to return handled compiled answer

actual payload mode: compiled_first_turn
expected payload mode: user_intent_boundary
```

Failing tests:

```text
test_report_routing_helper_requires_current_contract_identity
test_pre_routing_gate_must_not_skip_boundary_response_for_stale_allow_contract
test_stale_report_allow_contract_must_not_reach_compiled_query
```

Likely source area:

- `service.py:_user_intent_boundary_report_routing_allowed` currently checks only the `report_routing_allowed` boolean.
- `service.py:_user_intent_boundary_pre_routing_response_required` trusts that boolean-only helper.
- Report/compiled routing call sites that depend on `_user_intent_boundary_report_routing_allowed(...)` can therefore treat stale report-allow metadata as sufficient if stale metadata reaches the runtime boundary object.

This is not fixed in D-2 because D-2 is tests-only. The failing tests are intentionally preserved.

## 5. Passing Evidence Despite Blocker

The new tests also confirm several accepted authority guarantees remain intact:

- Visible-context helper requires current raw message and rejects stale/mismatched/non-redaction-safe/malformed context contracts.
- Current blocking V1-IB contract defeats optimistic frontdoor, visible, requery, compiled, and model reasoning test signals.
- Legacy allow metadata remains restrict-only when merged with a blocking V1-IB boundary.
- Proposal classifier output remains evidence-only with no route-authority fields.
- Final emission rejects stale/mismatched/non-redaction-safe/blocking V1-IB contracts and redacts selected payload leak markers.
- Current trace-safe V1-IB allow plus valid final-answer authority remains a positive final-emission control.

## 6. Recommended Next Slice

Recommended next narrow fix slice:

```text
V1-IB-D-2-A current-message report-routing authority fix
```

Recommended future fix boundary:

- Add current-message hash validation for report-routing authority in `service.py`, analogous to the accepted visible-context helper hardening.
- Require non-empty current raw message, matching `raw_message_hash`, matching `normalized_message_hash`, `type=qwen_user_intent_boundary_contract`, `validator_status=valid`, `trace_redaction_status=safe`, `report_routing_allowed=true`, `required_answer_mode=governed_erp_answer`, `authority_decision=allow_report`, replay-safe status, and no unsafe/mixed/ambiguous flags.
- Use the stricter current-message report-routing helper at pre-routing, report selector, governed requery, compiled query, and model reasoning gates.
- Keep legacy intent boundary restrict-only.
- Do not use keyword/regex/synonym/punctuation/no-alarm logic as authority.
- After the fix, rerun the preserved D-2 tests and accepted baseline.

D-2 does not implement this fix.

## 7. Verification Results

New D-2 test command:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_cross_lane_contract_identity \
  ai_assistant_ui.tests.test_v1_ib_d_authority_surface_consistency \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_authority_consistency
```

Result:

```text
Ran 9 tests
FAILED (failures=3)

Intentional blocker failures:
- test_report_routing_helper_requires_current_contract_identity
- test_pre_routing_gate_must_not_skip_boundary_response_for_stale_allow_contract
- test_stale_report_allow_contract_must_not_reach_compiled_query
```

Python compile for new D-2 tests:

```text
PASS
```

Qwen enterprise guardrail:

```text
Qwen enterprise guardrail audit: PASS
```

Fake-Frappe service import:

```text
FAKE_FRAPPE_SERVICE_IMPORT=PASS
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

Report present:

```text
report_present=PASS
```

Final git hygiene after report copy:

```text
git diff --check: PASS
git diff --cached --check: PASS
excluded_artifact_scan: PASS
staged_files=0
dirty_worktree_count=137
```

Accepted baseline was not run after the intentional D-2 blocker was confirmed. Per D-2 instructions, source was not fixed in this slice and the blocker was documented instead.

## 8. Boundary Statement

D-2 is authority consistency evidence only. It does not claim V1-IB-D closure.

The worktree remains dirty and not package-ready. No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise closure, or V2 work occurred.
