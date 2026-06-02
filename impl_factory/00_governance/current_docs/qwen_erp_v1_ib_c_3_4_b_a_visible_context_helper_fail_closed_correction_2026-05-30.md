# V1-IB-C-3-4-B-A Visible-Context Helper Fail-Closed Correction

Decision target:
`v1_ib_c_3_4_b_a_visible_context_helper_fail_closed_correction_ready_for_counterpart_qa_review`

## Scope

This slice corrects the direct helper authority gap in `service.py::_user_intent_boundary_context_reuse_allowed`.

Changed files:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_visible_context.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_b_a_visible_context_helper_fail_closed_correction_2026-05-30.md`

No changes were made to `authorized_emission.py`, `intent_boundary_runtime_integration.py`, `intent_boundary_contract.py`, `intent_boundary_proposal_classifier.py`, report-routing tests, browser/API UAT artifacts, staging, commits, pushes, packaging, deployment, strict enforcement, enterprise closure, or V2 work.

## Blocking Issue Corrected

Counterpart rejected C-3-4-B because the visible-context helper still had a permissive compatibility mode:

```text
helper_without_raw= True
helper_with_none= True
helper_with_blank= False
helper_with_current= True
helper_with_mismatch= False
```

That meant callers could omit `raw_message` or pass `None` and still receive `context_reuse_allowed=true` from a carried contract without proving current raw/normalized message ownership.

## Source Behavior Now Required

`_user_intent_boundary_context_reuse_allowed(...)` now returns `True` only when every required condition is satisfied:

- `user_intent_boundary` is a non-empty dict.
- `raw_message` is provided and not blank after string conversion/strip.
- `type == qwen_user_intent_boundary_contract`.
- `raw_message_hash == hash_text(current raw message)`.
- `normalized_message_hash == hash_text(normalize_message(current raw message))`.
- `validator_status == valid`.
- `trace_redaction_status == safe`.
- `context_reuse_allowed == true`.
- `safe_followup_intent == true`.
- `decision_intent == false`.
- `advice_intent == false`.
- `business_action_intent == false`.
- `policy_boundary_intent == false`.
- `mixed_intent_detected == false`.
- `ambiguity_status` is empty or `none`.

If any condition fails, the helper returns `False`.

Important authority statement:

- `raw_message` is mandatory for any visible-context reuse authority.
- `context_reuse_allowed=true` alone cannot authorize visible-context activation.
- No compatibility mode remains where `raw_message=None` can allow reuse.
- No keyword, regex, synonym, punctuation, phrase, or no-alarm route authority was added.

## Direct Probe Result After Fix

The direct helper probe now returns:

```text
helper_without_raw= False
helper_with_none= False
helper_with_blank= False
helper_with_current= True
helper_with_mismatch= False
```

## Tests Added

`test_v1_ib_service_adversarial_visible_context.py` now includes direct helper coverage proving:

- valid context-allow contract + omitted `raw_message` => `False`
- valid context-allow contract + `raw_message=None` => `False`
- valid context-allow contract + `raw_message="   "` => `False`
- valid context-allow contract + mismatched raw message => `False`
- valid context-allow contract + current hash-matching raw message => `True`
- stale context-allow contract + current raw message => `False`
- normalized hash mismatch + current raw message => `False`
- raw hash mismatch + current raw message => `False`
- non-redaction-safe + current raw message => `False`
- `mixed_intent_detected=true` + current raw message => `False`
- `decision_intent=true` + current raw message => `False`

Existing service-level protection remains covered:

- stale/mismatched visible-context replay does not call the trace visible helper
- `LEAK_STALE_VISIBLE_CONTEXT_C34A` does not appear in messages or payload
- safe explicit read-only follow-up with current hash-matching V1-IB authority can still activate visible context

## Verification Results

Focused visible-context tests:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context

Ran 5 tests ... OK
```

C-3-4 service tests:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_routing

Ran 9 tests ... OK
```

Python compile:

```text
python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_visible_context.py

py_compile=PASS
```

Qwen enterprise guardrail:

```text
Qwen enterprise guardrail audit: PASS
```

Fake-Frappe service import and append inventory:

```text
FAKE_FRAPPE_SERVICE_IMPORT=PASS
ACTIVE_RUNTIME_DIRECT_ASSISTANT_APPEND_COUNT=0
INVENTORY_COUNT=1
MIGRATED_AUTHORIZED_PATHS_LENGTH=27
FORMAL_RAW_SCAN=[
  ("impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py", 271),
  ("impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py", 327)
]
```

Hygiene:

```text
git diff --check: PASS
excluded/artifact scan: PASS
staged files: 0
dirty_worktree_count_before_report=116
dirty_worktree_count_after_report=117
```

## Baseline Status

The accepted baseline command exposed one out-of-scope legacy assertion that still expects the rejected compatibility behavior:

```text
FAIL: test_visible_context_requires_contract_context_allow
(ai_assistant_ui.tests.test_v1_ib_runtime_integration.V1IBRuntimeIntegrationTests)

self.assertTrue(service._user_intent_boundary_context_reuse_allowed(context_boundary))
AssertionError: False is not true
```

This failure is expected under the corrected C-3-4-B-A authority rule because the test calls `_user_intent_boundary_context_reuse_allowed(context_boundary)` without a current `raw_message`. That file is outside the approved C-3-4-B-A file boundary and was not edited.

Recommendation: request a separate test-alignment slice for `test_v1_ib_runtime_integration.py` to update this legacy helper expectation so the baseline asserts the new fail-closed contract:

```text
_user_intent_boundary_context_reuse_allowed(context_boundary) == False
_user_intent_boundary_context_reuse_allowed(context_boundary, raw_message=current_message) == True
```

## Residual Boundary

This slice is a narrow helper fail-closed correction. It does not approve browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise closure, or V2 work.
