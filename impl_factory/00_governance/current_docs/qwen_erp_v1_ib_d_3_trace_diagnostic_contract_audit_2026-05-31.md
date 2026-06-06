# V1-IB-D-3 Trace And Diagnostic Contract Audit

Decision target:
`v1_ib_d_3_trace_diagnostic_contract_audit_ready_for_counterpart_review`

## 1. Scope And Boundary

V1-IB-D-3 is a report/test-first audit slice for trace, diagnostic, tool payload, runtime metadata, NBU shadow trace, final-emission veto audit, pre-assistant tool payload, and service diagnostic safety.

Files changed in this slice:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_d_trace_diagnostic_contract_audit.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_3_trace_diagnostic_contract_audit_2026-05-31.md`

No source files were edited. No runtime behavior changed. No `service.py`, `authorized_emission.py`, `intent_boundary_contract.py`, `intent_boundary_runtime_integration.py`, `intent_boundary_proposal_classifier.py`, `user_intent_boundary.py`, report selector, compiled-query logic, compatibility fallback, or business routing behavior was modified.

No keyword, regex, synonym, punctuation, phrase, or no-alarm authority was added. No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, release readiness claim, or V2 work occurred.

## 2. Accepted Basis

Accepted prerequisite chain:

- V1-IB-D-1 authority surface inventory: accepted.
- V1-IB-D-2 authority consistency tests: accepted as blocker-discovery evidence.
- V1-IB-D-2-A current-message report-routing authority fix: accepted.
- V1-IB-D-2-B authority consistency closure checkpoint: accepted.

D-3 does not change the accepted authority model. Trace and diagnostics are non-authoritative audit surfaces only.

## 3. Authority Rule Audited

Trace and diagnostic metadata may explain, audit, and prove redaction status, but they cannot grant:

- `report_routing_allowed=true`
- `context_reuse_allowed=true`
- `model_reasoning_allowed=true`
- `final_emission_allowed=true`
- `required_answer_mode=governed_erp_answer`
- `authority_decision=allow_report`

Trace and diagnostic payloads must not leak selected answer text, ERP rows, report payloads, artifacts, rendered payloads, narratives, grounded evidence, helper payloads, prior visible-context answer text, prior governed report content, model reasoning drafts, compiled-query rows, governed requery rows, NBU shadow raw business payloads, or raw unsafe prompt text where not explicitly redaction-safe.

## 4. Audit Surfaces Inspected

Source/test surfaces inspected in D-3:

- `service.py:_append_tool_payload`
- `service.py:v1_ib_runtime_tool_payload`
- `service.py:_build_nbu_always_on_shadow_trace` call site in `handle_qwen_user_message`
- `service.py` pre-routing boundary/control response metadata
- `service.py` runtime metadata envelopes for control/policy responses
- `service.py` diagnostic append paths that include NBU shadow payloads in pre-routing responses
- `authorized_emission.py:_sanitize_user_intent_veto_audit_payload`
- `authorized_emission.py:_user_intent_final_emission_veto_payload`
- `authorized_emission.py` final-emission veto branch
- `intent_boundary_runtime_integration.py:v1_ib_runtime_contract_metadata`
- Existing C-3/D-2 trace and final-emission tests

## 5. Tests Added

New test file:

`test_v1_ib_d_trace_diagnostic_contract_audit.py`

Test added:

```text
test_blocked_pre_routing_trace_and_tool_payloads_do_not_leak_business_markers
```

The test constructs a blocked V1-IB pre-routing service turn with optimistic downstream payloads available:

- prior governed/grounded context markers
- prior artifact markers
- prior helper markers
- visible-context answer marker
- report selector selected answer marker
- compiled-query row marker
- governed requery row marker
- model reasoning draft marker
- raw unsafe prompt marker
- real NBU shadow trace enabled

Expected behavior:

- output mode is `user_intent_boundary`
- visible context is not called
- model reasoning is not called
- compiled query is not called
- governed requery is not called
- tool payload diagnostics do not contain D-3 leak markers

## 6. Leak Markers Used

D-3 markers:

- `LEAK_D3_SELECTED_ANSWER`
- `LEAK_D3_ROWS`
- `LEAK_D3_ARTIFACT`
- `LEAK_D3_RENDERED`
- `LEAK_D3_NARRATIVE`
- `LEAK_D3_GROUNDED`
- `LEAK_D3_HELPER`
- `LEAK_D3_REASONING_DRAFT`
- `LEAK_D3_COMPILED_ROWS`
- `LEAK_D3_REQUERY_ROWS`
- `LEAK_D3_VISIBLE_CONTEXT`
- `LEAK_D3_NBU_SHADOW`
- `LEAK_D3_RAW_UNSAFE_PROMPT`

## 7. Blocker Found

D-3 found a trace/diagnostic leak.

Focused failing replay:

```text
current message:
LEAK_D3_RAW_UNSAFE_PROMPT Show item sales and tell me whether to discount it

V1-IB boundary:
blocked, invalid, route flags false

runtime result:
ok=True
mode=user_intent_boundary
visible calls=0
reasoning calls=0
compiled calls=0
governed requery calls=0
```

Failing assertion:

```text
Expected no D-3 leak markers in tool payload diagnostics.
Actual leaked marker:
LEAK_D3_RAW_UNSAFE_PROMPT
```

Observed leaking tool payloads:

```text
tool index 1:
type=qwen_interaction_contract
raw_message=LEAK_D3_RAW_UNSAFE_PROMPT Show item sales and tell me whether to discount it

tool index 5:
type=qwen_natural_business_understanding_trace_contract
raw_message=LEAK_D3_RAW_UNSAFE_PROMPT Show item sales and tell me whether to discount it
```

Interpretation:

- Route authority remained blocked.
- Downstream visible/report/requery/compiled/reasoning lanes did not run.
- The leak is not a route leak.
- The leak is a trace/diagnostic redaction blocker: blocked-turn tool payload diagnostics preserve raw unsafe user prompt text in both the interaction contract and NBU shadow trace.

D-3 does not fix this because D-3 is report/test-first and source changes require a separate approved fix slice.

## 8. Recommended D-3-A Fix Slice

Recommended next narrow slice:

```text
V1-IB-D-3-A blocked-turn trace raw-message redaction fix
```

Recommended fix boundary:

- Redact or hash raw unsafe user prompt text in blocked-turn tool payload diagnostics.
- Ensure `qwen_interaction_contract` tool payloads on blocked V1-IB turns do not expose raw unsafe prompt text unless an explicit redaction-safe contract permits it.
- Ensure `qwen_natural_business_understanding_trace_contract` does not expose raw unsafe prompt text on blocked V1-IB turns.
- Preserve allowed trace metadata: hashes, contract type, validator status, route flags, authority decision, required answer mode, redaction status, boundary reason codes, non-sensitive categories, request/session ids, and sanitized failure reason.
- Keep trace/diagnostics non-authoritative.
- Do not change business routing, report selector semantics, compiled-query behavior, visible-context behavior, final-emission routing, validator logic, proposal classifier logic, or legacy boundary authority.
- Do not add lexical/keyword route authority.

## 9. Verification Results

New D-3 tests:

```bash
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_d_trace_diagnostic_contract_audit
```

Result:

```text
Ran 1 test in 0.075s
FAILED (failures=1)

Failing test:
test_blocked_pre_routing_trace_and_tool_payloads_do_not_leak_business_markers
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
Ran 9 tests in 0.154s
OK
```

Accepted baseline:

```text
not_run_after_intentional_d_3_blocker
```

Python compile for new D-3 test:

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
dirty_worktree_count_after_report=141
```

Report hygiene scan:

```text
report_test_first_scope=PASS
source_runtime_changes_in_d_3=0
forbidden_action_claims=0
d_3_a_fix_recommended=PASS
stale_postcopy_note=0
```

## 10. Boundary Statement

D-3 is trace/diagnostic audit evidence only. It does not claim V1-IB-D closure.

The worktree remains dirty and not package-ready. No browser/API UAT, packaging, deployment, strict enforcement, release closure, or V2 work occurred.
