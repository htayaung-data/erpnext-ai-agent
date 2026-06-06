# V1-IB-C-3-7 Adversarial Service-Level Phase Closure Readiness

Decision target:
`v1_ib_c_3_7_adversarial_service_level_phase_closure_readiness_ready_for_counterpart_qa_review`

Decision request:
`accept_v1_ib_c_3_adversarial_service_level_phase_closure`

## Purpose

This is a report-only C-3 phase closure readiness packet after QA accepted C-3-6. It consolidates the accepted V1-IB-C-3 adversarial service-level evidence and asks QA/Counterpart to decide whether to close V1-IB-C-3 and return to the main V1-IB roadmap.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_3_7_adversarial_service_level_phase_closure_readiness_2026-05-31.md`

C-3-7 is report-only. No source/runtime/test behavior changed. No keyword, regex, synonym, punctuation, phrase, or no-alarm route authority was added. No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise closure, or V2 work occurred.

## Accepted Authority Model

The accepted V1-IB authority model remains:

- `IntentBoundaryContract` is sole runtime authority.
- Classifier/proposer output is evidence only.
- Semantic-safe/model output cannot authorize.
- Lexical/token/no-alarm evidence cannot authorize.
- Visible context cannot authorize model reasoning.
- Report selector cannot authorize itself.
- Enterprise model output cannot authorize final answer.
- Final-answer authority cannot bypass V1-IB.
- Missing, invalid, stale, unsafe, mixed, ambiguous, unresolved, non-redaction-safe, or unproven V1-IB contract fails closed.

## Accepted C-3 Evidence

### C-3-2 First Adversarial Runtime Tests

C-3-2 was accepted as the first adversarial runtime test implementation slice.

Coverage:

- pre-routing adversarial blocks
- final-emission veto/leak tests
- pricing, payment, report manipulation, accounting/write-off families
- safe governed report positive controls
- safe visible-context positive controls

The C-3-2 evidence established that unsafe and mixed prompts fail closed before report routing, and that late selected business answers are vetoed and sanitized when V1-IB does not authorize final emission.

### C-3-4 Visible-Context / Report-Routing Closure

C-3-4 through C-3-4-C were accepted for service-level visible-context and report-routing closure.

Key findings and fixes:

- C-3-4-A found a stale/mismatched visible-context leak where a stale V1-IB context-allow contract could activate a visible-context answer.
- C-3-4-B fixed active stale visible-context authority.
- C-3-4-B-A hardened `_user_intent_boundary_context_reuse_allowed` so `raw_message` is mandatory.
- C-3-4-B-B aligned the legacy runtime-integration test expectation with the accepted fail-closed helper behavior.
- C-3-4-C closure was accepted.

Final visible-context rule:

- current raw message must be provided
- raw-message hash must match the current message
- normalized-message hash must match the current message
- `validator_status` must be `valid`
- `trace_redaction_status` must be `safe`
- `safe_followup_intent` must be true
- `context_reuse_allowed` must be true
- unsafe, mixed, and ambiguous flags must be false
- `context_reuse_allowed=true` alone is not authority

Accepted C-3-4 evidence also confirmed report routing remains separately gated by report-routing authority and cannot be authorized by visible context, stale context, legacy allow state, report selector confidence, or grounded artifacts.

### C-3-5 Model-Reasoning / Report-Selector / Trace Closure

C-3-5 through C-3-5-3 were accepted for service-level model-reasoning, report-selector / compiled-query, and trace-redaction closure.

Accepted evidence shows:

- model reasoning handler is blocked behind V1-IB
- optimistic semantic reasoning evidence cannot override V1-IB
- prior grounded turn does not authorize reasoning
- visible context does not authorize reasoning
- report selector/frontdoor candidate does not authorize routing
- compiled query handler is not called for blocked prompts
- governed requery helper is not called for blocked prompts
- final-answer authority does not bypass V1-IB
- C-35 trace leak markers are absent on blocked paths
- safe factual controls require valid current V1-IB report authority

Leak markers covered in C-3-5:

- `LEAK_MODEL_REASONING_C35`
- `LEAK_REPORT_SELECTOR_C35`
- `LEAK_TRACE_ROWS_C35`
- `LEAK_TRACE_ARTIFACT_C35`
- `LEAK_TRACE_GROUNDED_EVIDENCE_C35`
- `LEAK_TRACE_HELPER_PAYLOAD_C35`

### C-3-6 Long-Context / Full-Call-Stack Evidence

C-3-6 was accepted by QA/Risk as the final requested long-context/full-call-stack service evidence slice, with no additional C-3 adversarial service slice required before the phase-closure decision.

Accepted C-3-6 coverage:

- prior governed report payload seeded
- prior visible-context payload seeded
- prior artifact seeded
- prior grounded context seeded
- prior safe factual follow-up history seeded
- optimistic visible-context, report-selector, requery, compiled-query, and model-reasoning lanes made available
- blocking V1-IB contract kept all downstream call counts at zero
- C-36 leak markers absent from session messages, returned payload, agent metadata, tool payloads, and trace-like service metadata
- safe controls require valid current V1-IB authority
- safe-looking controls without valid current V1-IB authority fail closed

Unsafe/mixed long-context prompt families covered in C-3-6:

- customer/AR decision
- supplier/AP payment
- invoice manipulation
- P&L/accounting action
- product/sales pricing
- inventory action
- legal/regulatory advice
- forecast/prediction

Leak markers covered in C-3-6:

- `LEAK_LONG_CONTEXT_ROWS_C36`
- `LEAK_LONG_CONTEXT_ARTIFACT_C36`
- `LEAK_LONG_CONTEXT_RENDERED_C36`
- `LEAK_LONG_CONTEXT_NARRATIVE_C36`
- `LEAK_LONG_CONTEXT_GROUNDED_C36`
- `LEAK_LONG_CONTEXT_HELPER_C36`
- `LEAK_LONG_CONTEXT_SELECTED_C36`
- `LEAK_LONG_CONTEXT_VISIBLE_C36`
- `LEAK_LONG_CONTEXT_REASONING_C36`
- `LEAK_LONG_CONTEXT_REPORT_SELECTOR_C36`

## Closure Readiness Assessment

The accepted C-3 evidence now covers:

- helper-level adversarial pre-routing and final-emission veto behavior
- service-level visible-context activation blocking
- service-level report-routing blocking
- stale and mismatched context authority rejection
- model-reasoning activation blockers
- report-selector / compiled-query blockers
- governed requery blockers
- final-answer authority dominance checks
- long-context multi-turn service behavior
- full optimistic service stack with V1-IB block dominance
- trace and payload redaction under blocked service turns
- safe factual controls requiring valid current V1-IB authority

The current evidence is service-level and unit-level. It does not approve browser/API UAT, packaging, staging, deployment, strict enforcement, enterprise closure, or V2 work.

## Verification Results

C-3-6 + C-3-5 + C-3-4 + runtime integration group:

```text
PYTHONPATH=impl_factory/05_custom_logic/custom_app/ai_assistant_ui python3 -m unittest \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_long_context_full_stack \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_model_reasoning \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_selector \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_trace_redaction \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_visible_context \
  ai_assistant_ui.tests.test_v1_ib_service_adversarial_report_routing \
  ai_assistant_ui.tests.test_v1_ib_runtime_integration

Ran 30 tests ... OK
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

Python compile for C-3 tests:

```text
python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_prerouting.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_final_emission.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_visible_context.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_report_routing.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_model_reasoning.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_report_selector.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_trace_redaction.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_adversarial_long_context_full_stack.py

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

Hygiene before this report:

```text
git diff --check: PASS
excluded/artifact scan: PASS
staged files: 0
dirty_worktree_count_before_report=128
```

Final hygiene should be rerun after this report is copied into the remote worktree.

## Dirty Worktree / Package Boundary

The worktree remains dirty and is not package-ready. C-3-7 does not stage, commit, push, package, deploy, enable strict enforcement, claim enterprise closure, or start V2 work.

## Decision Request

QA/Counterpart is asked to decide:

```text
accept_v1_ib_c_3_adversarial_service_level_phase_closure
```

If accepted, the next roadmap step should be:

- return to main V1-IB-C runtime integration closure / V1-IB-D planning
- not browser/API UAT yet
- not packaging yet

If not accepted, QA/Counterpart should identify the specific remaining C-3 service-level adversarial gap and approve a narrow tests-only follow-up slice before any source fix.
