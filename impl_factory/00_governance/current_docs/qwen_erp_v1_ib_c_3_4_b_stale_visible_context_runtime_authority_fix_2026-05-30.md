# V1-IB-C-3-4-B Stale Visible-Context Runtime Authority Fix

Decision target:
`v1_ib_c_3_4_b_stale_visible_context_runtime_authority_fix_ready_for_counterpart_qa_review`

## Scope

This slice fixes the confirmed service-level visible-context authority bug from C-3-4-A.

Changed files:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_visible_context.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_b_stale_visible_context_runtime_authority_fix_2026-05-30.md`

No changes were made to `authorized_emission.py`, `intent_boundary_runtime_integration.py`, `intent_boundary_contract.py`, `intent_boundary_proposal_classifier.py`, report-routing tests, browser/API UAT artifacts, staging, commits, pushes, packaging, deployment, strict enforcement, enterprise closure, or V2 work.

## Bug Fixed

C-3-4-A confirmed that a stale V1-IB context-allow contract could reach visible-context emission:

- Current message: `Who is second in the previous table?`
- Stale allow contract source: `Show EC7H-SUP-A payable status`
- Mismatched normalized-hash allow contract also reproduced the risk.
- Patched visible-context trace helper returned:
  `{"ok": true, "mode": "visible_context_answer", "answer": "LEAK_STALE_VISIBLE_CONTEXT_C34A"}`
- Actual before fix: service returned `mode=visible_context_answer`.
- Expected: fail closed before visible-context activation or at least before visible-context emission.

Root cause: visible-context service gates treated `context_reuse_allowed=true` as sufficient without proving the V1-IB contract belonged to the current raw user message and was trace-safe/non-unsafe.

## Runtime Authority Fix

`service.py` now includes current-message V1-IB context authority checks.

New helper behavior:

- `_user_intent_boundary_matches_current_message(user_intent_boundary, raw_message)` requires:
  - boundary is a dict
  - `type == qwen_user_intent_boundary_contract`
  - current raw message is present
  - `raw_message_hash == hash_text(current_raw_message)`
  - `normalized_message_hash == hash_text(normalize_message(current_raw_message))`

- `_user_intent_boundary_has_unsafe_or_ambiguous_intent(user_intent_boundary)` treats these as blocking:
  - `decision_intent`
  - `advice_intent`
  - `business_action_intent`
  - `policy_boundary_intent`
  - `mixed_intent_detected`
  - non-empty/non-`none` `ambiguity_status`

- `_user_intent_boundary_context_reuse_allowed(user_intent_boundary, raw_message=...)` now requires, when a current raw message is supplied:
  - current raw/normalized hash match
  - `validator_status == valid`
  - `trace_redaction_status == safe`
  - `context_reuse_allowed == true`
  - `safe_followup_intent == true`
  - no unsafe, mixed, or ambiguous flags

`context_reuse_allowed=true` alone is no longer visible-context authority. It is only one field inside a current, hash-matching, trace-safe, validated V1-IB contract.

## Gates Updated Or Reviewed

The service visible-context gates now pass the current raw message into the V1-IB context-reuse check:

- early trace-inspection visible-context gate in `handle_qwen_user_message`
- `_visible_context_followup_should_preempt_clarification`
- `_artifact_boundary_should_yield_to_visible_context`
- `_compiled_fresh_query_should_yield_to_visible_context`
- `_runtime_gate_should_yield_to_visible_context`
- `_nbu_presentation_should_yield_to_local_or_visible_context`
- direct `_user_intent_boundary_context_reuse_allowed(...)` calls in `handle_qwen_user_message`
- paths that can call `_try_activate_visible_context_followup_response(...)` and emit `mode=visible_context_answer`

Source anchors after this slice:

- `service.py:724` `_user_intent_boundary_matches_current_message`
- `service.py:742` `_user_intent_boundary_has_unsafe_or_ambiguous_intent`
- `service.py:762` `_user_intent_boundary_context_reuse_allowed`
- `service.py:805` `_visible_context_followup_should_preempt_clarification`
- `service.py:819` `_artifact_boundary_should_yield_to_visible_context`
- `service.py:840` `_compiled_fresh_query_should_yield_to_visible_context`
- `service.py:855` `_runtime_gate_should_yield_to_visible_context`
- `service.py:870` `_nbu_presentation_should_yield_to_local_or_visible_context`

No keyword, phrase, regex, synonym, punctuation, or no-alarm route authority was added.

## Test Hardening

`test_v1_ib_service_adversarial_visible_context.py` now keeps the handled visible-context replay intact. The visible trace helper returns:

`{"ok": true, "mode": "visible_context_answer", "answer": "LEAK_STALE_VISIBLE_CONTEXT_C34A"}`

Blocked cases now covered:

- stale context-allow contract
- normalized hash mismatch
- raw hash mismatch
- non-redaction-safe contract
- `mixed_intent_detected=true`
- `decision_intent=true`

Blocked assertions include:

- payload mode is not `visible_context_answer`
- response fails closed through boundary/control behavior
- `LEAK_STALE_VISIBLE_CONTEXT_C34A` is absent from serialized messages/payloads
- visible trace helper is not called
- visible follow-up handler is not called
- compiled/report handler is not called

Positive control still passes:

- Current message: `Who is second in the previous table?`
- Current hash-matching, trace-safe V1-IB context allow
- `safe_followup_intent=true`
- no unsafe/mixed/ambiguous flags
- visible-context answer may emit only under this current authority.

Test anchors:

- `test_v1_ib_service_adversarial_visible_context.py:252` hardened stale/mismatch test
- `test_v1_ib_service_adversarial_visible_context.py:265` handled leak-marker replay
- `test_v1_ib_service_adversarial_visible_context.py:291` leak absence assertion

## Verification Results

Focused visible-context tests:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context

Ran 4 tests ... OK
```

C-3-4 service tests:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_routing

Ran 8 tests ... OK
```

Accepted baseline:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_prerouting \
  ai_assistant_ui.tests.test_v1_ib_runtime_adversarial_final_emission \
  ai_assistant_ui.tests.test_v1_ib_runtime_integration \
  ai_assistant_ui.tests.test_v1_ib_runtime_final_emission_contract_veto \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_contract_validator \
  ai_assistant_ui.tests.test_v1_ib_intent_boundary_proposal_classifier \
  ai_assistant_ui.tests.test_authorized_emission_contracts \
  ai_assistant_ui.tests.test_service_control_authorized_emission_contracts

Ran 157 tests ... OK
```

Additional verification:

```text
python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_visible_context.py

py_compile=PASS
```

```text
python3 scripts/check_qwen_enterprise_guardrails.py

Qwen enterprise guardrail audit: PASS
```

```text
fake_frappe_service_import=PASS True
```

```text
direct_assistant_inventory=0 / 1 / 27
```

```text
raw_append_scan=impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py:271,
impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py:327
```

```text
git diff --check

diff_check=PASS
```

```text
excluded_artifact_scan=PASS
staged_files=0
dirty_worktree_count_before_report=115
dirty_worktree_count_after_report=116
```

## Residual Boundary

This is a narrow runtime authority fix for visible-context activation. It does not claim enterprise closure and does not approve browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, or V2 work.
