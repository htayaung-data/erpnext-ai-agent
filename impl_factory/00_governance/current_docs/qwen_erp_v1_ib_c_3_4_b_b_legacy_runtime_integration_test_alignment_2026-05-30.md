# V1-IB-C-3-4-B-B Legacy Runtime-Integration Test Alignment

Decision target:
`v1_ib_c_3_4_b_b_legacy_runtime_integration_test_alignment_ready_for_counterpart_qa_review`

## Scope

This is a test-alignment-only slice after accepted C-3-4-B-A helper fail-closed correction.

Changed files:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_b_b_legacy_runtime_integration_test_alignment_2026-05-30.md`

No runtime/source files were changed in this slice. C-3-4-B-A helper behavior remains unchanged.

No changes were made to `service.py`, `authorized_emission.py`, `intent_boundary_contract.py`, `intent_boundary_runtime_integration.py`, `intent_boundary_proposal_classifier.py`, proposal-classifier tests, or C-3-4-B-A tests.

No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise closure, or V2 work occurred.

## Alignment Reason

The older `test_visible_context_requires_contract_context_allow` test in `test_v1_ib_runtime_integration.py` still asserted the rejected compatibility behavior:

```text
service._user_intent_boundary_context_reuse_allowed(context_boundary) == True
```

That expectation is no longer enterprise-safe. Accepted C-3-4-B-A behavior requires a current raw message before visible-context reuse authority can be true:

```text
_user_intent_boundary_context_reuse_allowed(boundary) == False
_user_intent_boundary_context_reuse_allowed(boundary, raw_message=None) == False
_user_intent_boundary_context_reuse_allowed(boundary, raw_message="   ") == False
_user_intent_boundary_context_reuse_allowed(boundary, raw_message=current_message) == True only when hashes match and all V1-IB authority fields are valid/safe.
```

Raw-message-less context reuse is no longer allowed.

## Test Update

`test_visible_context_requires_contract_context_allow` now asserts:

- missing/`None` boundary remains false
- contract without context reuse remains false even with current `raw_message`
- valid current context boundary without `raw_message` is false
- valid current context boundary with `raw_message=current_message` is true
- valid context boundary with mismatched `raw_message` is false
- report routing still depends on `report_routing_allowed` separately and remains false for the visible-context-only boundary

This preserves the accepted authority model:

- `context_reuse_allowed=true` alone is not authority
- current raw/normalized hash proof is required
- report routing authority is separate from visible-context context reuse
- no keyword, regex, synonym, punctuation, phrase, or no-alarm route authority was added

## Verification Results

Runtime-integration module:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_runtime_integration

Ran 11 tests ... OK
```

C-3-4 service tests:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_routing

Ran 9 tests ... OK
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

Python compile:

```text
python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py

py_compile=PASS
```

Qwen enterprise guardrail:

```text
Qwen enterprise guardrail audit: PASS
```

Fake-Frappe service import and inventory:

```text
FAKE_FRAPPE_SERVICE_IMPORT=PASS
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

Hygiene:

```text
git diff --check: PASS
excluded/artifact scan: PASS
staged files: 0
dirty_worktree_count_before_report=117
dirty_worktree_count_after_report=118
```

## Boundary

This slice only aligns a legacy test with the accepted C-3-4-B-A authority model. It does not reintroduce compatibility mode, does not change runtime behavior, and does not add lexical/regex authority.
