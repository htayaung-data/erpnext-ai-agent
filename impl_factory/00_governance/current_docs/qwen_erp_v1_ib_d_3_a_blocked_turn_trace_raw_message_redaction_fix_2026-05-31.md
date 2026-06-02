# V1-IB-D-3-A Blocked-Turn Trace Raw-Message Redaction Fix

Decision target:
`v1_ib_d_3_a_blocked_turn_trace_raw_message_redaction_fix_ready_for_counterpart_review`

## 1. Scope And Boundary

V1-IB-D-3-A is the narrow fix for the D-3 trace/diagnostic privacy blocker where raw unsafe prompt text leaked through blocked-turn diagnostic tool payloads.

Files changed in this slice:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_trace_diagnostic_contract_audit.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_3_a_blocked_turn_trace_raw_message_redaction_fix_2026-05-31.md`

No `authorized_emission.py`, `intent_boundary_contract.py`, `intent_boundary_runtime_integration.py`, `intent_boundary_proposal_classifier.py`, `user_intent_boundary.py`, report selector logic, compiled-query logic, model reasoning logic, business routing behavior, or route authority semantics were modified.

No keyword, regex, synonym, punctuation, phrase, or no-alarm authority was added. No compatibility fallback was added. No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, release readiness claim, or V2 work occurred.

## 2. Blocker Summary

D-3 found a privacy/trace leak, not a routing leak:

```text
current message:
LEAK_D3_RAW_UNSAFE_PROMPT Show item sales and tell me whether to discount it

runtime result:
mode=user_intent_boundary
visible calls=0
reasoning calls=0
compiled calls=0
governed requery calls=0

leaking diagnostic payloads:
qwen_interaction_contract.raw_message
qwen_natural_business_understanding_trace_contract.raw_message
```

The blocked turn stayed blocked, but tool payload diagnostics exposed raw unsafe prompt text.

## 3. Exact Source Change

Added two pure redaction helpers in `service.py`:

- `_redact_blocked_turn_diagnostic_payload(...)`
- `_redact_blocked_turn_diagnostic_payloads(...)`

The helpers sanitize emitted diagnostic/tool payload copies only. They do not mutate contracts used for route decisions and do not decide authorization.

Payload types redacted on blocked pre-routing response:

- `qwen_interaction_contract`
- `qwen_natural_business_understanding_trace_contract`

Redaction behavior:

```text
raw_message -> [redacted_by_v1_ib]
raw_message_hash -> hash_text(original raw_message)
normalized_message_hash -> hash_text(normalize_message(original raw_message))
trace_redaction_status -> safe
redaction_reason -> v1_ib_blocked_turn_diagnostic_redaction
```

The blocked pre-routing control response now passes diagnostic payload copies through `_redact_blocked_turn_diagnostic_payloads(...)` before authorized emission. Routing behavior and authority semantics are unchanged.

## 4. Tests Updated

Updated:

`test_v1_ib_d_trace_diagnostic_contract_audit.py`

The D-3 test now proves:

- blocked pre-routing diagnostics do not leak `LEAK_D3_RAW_UNSAFE_PROMPT`
- no D-3 leak markers appear in tool payloads
- interaction contract raw message is redacted on blocked turn
- NBU shadow trace raw message is redacted on blocked turn
- raw and normalized hashes remain present
- `trace_redaction_status=safe` appears on redacted diagnostic payload copies
- `redaction_reason=v1_ib_blocked_turn_diagnostic_redaction` appears
- route remains `user_intent_boundary`
- visible/reasoning/compiled/requery call counts stay zero
- route-authority flags remain false

The test still inspects tool payloads directly and does not ignore the `qwen_interaction_contract` or NBU trace payloads.

## 5. Before / After Behavior

Before D-3-A:

```text
D-3 test: FAILED
LEAK_D3_RAW_UNSAFE_PROMPT appeared in:
  qwen_interaction_contract.raw_message
  qwen_natural_business_understanding_trace_contract.raw_message
```

After D-3-A:

```text
D-3 test: PASS
qwen_interaction_contract.raw_message=[redacted_by_v1_ib]
qwen_natural_business_understanding_trace_contract.raw_message=[redacted_by_v1_ib]
raw/normalized hashes remain present
route output remains user_intent_boundary
visible/reasoning/compiled/requery calls remain 0
```

## 6. Authority / Routing Statement

Trace and diagnostics remain non-authoritative. They may carry redaction-safe metadata and hashes, but they cannot grant:

- `report_routing_allowed=true`
- `context_reuse_allowed=true`
- `model_reasoning_allowed=true`
- `final_emission_allowed=true`
- `required_answer_mode=governed_erp_answer`
- `authority_decision=allow_report`

D-3-A changes diagnostic copies on blocked pre-routing emission only. It does not change business routing, report selection, compiled query execution, model reasoning, visible-context behavior, validator authority, proposal classifier behavior, or final-emission authority.

## 7. Verification Results

D-3 test:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_contract_audit
```

Result:

```text
Ran 1 test in 0.041s
OK
```

D-2 tests:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_cross_lane_contract_identity \
  ai_assistant_ui.tests.test_v1_ib_d_authority_surface_consistency \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_authority_consistency
```

Result:

```text
Ran 9 tests in 0.124s
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
Ran 157 tests in 0.442s
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

Final git and artifact hygiene after report copy:

```text
git diff --check: PASS
git diff --cached --check: PASS
excluded_artifact_scan: PASS
staged_files=0
dirty_worktree_count_after_report=142
```

Report hygiene:

```text
forbidden_files_changed=0
lexical_keyword_authority_added=0
routing_semantics_changed=0
d_3_a_scope=PASS
stale_postcopy_note=0
```

## 8. Boundary Statement

D-3-A is only the blocked-turn diagnostic raw-message redaction fix. It does not claim D-3 closure or V1-IB-D closure.

The worktree remains dirty and not package-ready. No browser/API UAT, packaging, deployment, strict enforcement, release readiness, or V2 work occurred.
