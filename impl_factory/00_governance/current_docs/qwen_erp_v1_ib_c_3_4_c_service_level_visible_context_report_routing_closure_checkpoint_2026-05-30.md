# V1-IB-C-3-4-C Service-Level Visible-Context / Report-Routing Closure Checkpoint

Decision target:
`v1_ib_c_3_4_c_service_level_visible_context_report_routing_closure_checkpoint_ready_for_counterpart_qa_review`

## Scope

This is a closure checkpoint only. It consolidates C-3-4 service-level adversarial runtime evidence after the accepted fixes:

- C-3-4-A confirmed the stale/mismatched visible-context leak.
- C-3-4-B fixed active stale visible-context runtime authority.
- C-3-4-B-A hardened `_user_intent_boundary_context_reuse_allowed(...)` to fail closed without current raw-message proof.
- C-3-4-B-B aligned legacy runtime-integration test expectations with the fail-closed helper model.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_4_c_service_level_visible_context_report_routing_closure_checkpoint_2026-05-30.md`

No runtime source files, tests, validator/classifier files, report routing code, visible-context runtime code, or final-emission code were changed in C-3-4-C.

## Final Visible-Context Authority Rule

Visible-context activation requires current hash-matching V1-IB authority for the current raw user message. The service-level context helper may return `True` only when all of these are true:

- `user_intent_boundary` is a non-empty dict.
- `type == qwen_user_intent_boundary_contract`.
- `raw_message` is provided and not blank.
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

`context_reuse_allowed=true` alone is not authority. Raw-message-less helper calls fail closed. Stale raw hash, normalized hash mismatch, non-redaction-safe contracts, mixed intent, and decision intent all block visible context.

No lexical, keyword, regex, synonym, punctuation, phrase, or no-alarm logic was added as route authority.

## Closure Evidence

Visible-context closure:

- Stale context-allow contract from a different raw message blocks.
- Normalized hash mismatch blocks.
- Raw hash mismatch blocks.
- Non-redaction-safe context contract blocks.
- `mixed_intent_detected=true` blocks.
- `decision_intent=true` blocks.
- Direct helper calls without `raw_message`, with `raw_message=None`, or with blank `raw_message` return false.
- `LEAK_STALE_VISIBLE_CONTEXT_C34A` does not appear in blocked visible-context messages or payloads.
- The visible trace helper is not called for blocked stale/mismatched/unsafe-field cases.
- The visible follow-up helper is not called for blocked stale/mismatched/unsafe-field cases.
- Safe explicit read-only visible-context follow-up still works when the V1-IB context contract is current, hash-matching, trace-safe, and has valid visible-context authority.

Report-routing closure:

- Report routing remains separately gated by report-routing authority.
- Visible-context context reuse does not imply report routing.
- Report-routing adversarial tests continue to prove blocked mixed/manipulation report probes do not select or emit governed report output.

Legacy alignment:

- `test_v1_ib_runtime_integration.py` now asserts the accepted fail-closed helper behavior.
- Valid context boundary without `raw_message` is false.
- Valid context boundary with current hash-matching `raw_message` is true.
- Valid context boundary with mismatched `raw_message` is false.
- Report routing still depends on `report_routing_allowed` separately.

Leak boundary:

- Blocked visible-context paths do not leak selected answer text, ERP rows, report payloads, rendered payloads, artifacts, narratives, grounded evidence, or helper business payloads.

## Verification Results

Focused visible-context:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context

Ran 5 tests ... OK
```

C-3-4 service pair:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_routing

Ran 9 tests ... OK
```

Runtime integration:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_runtime_integration

Ran 11 tests ... OK
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

Python compile for relevant touched/accepted files:

```text
python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_visible_context.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_report_routing.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py

py_compile=PASS
```

Qwen enterprise guardrail:

```text
Qwen enterprise guardrail audit: PASS
```

Fake-Frappe service import and direct assistant inventory:

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
dirty_worktree_count_before_report=118
dirty_worktree_count_after_report=119
```

## Carry-Forward Risks

- Later C-3 service-level coverage is still needed for model reasoning, report selector edge cases, trace redaction, and broader call-stack adversarial behavior.
- Full browser/API UAT has not been performed and is not approved by this checkpoint.
- Packaging, deployment, strict enforcement, and enterprise closure are not approved by this checkpoint.
- The dirty worktree remains not package-ready.

## Boundary Statement

C-3-4-C is not UAT, not packaging, not deployment, not strict enforcement, and not enterprise closure. It does not start the next adversarial slice and does not approve V2 work.
