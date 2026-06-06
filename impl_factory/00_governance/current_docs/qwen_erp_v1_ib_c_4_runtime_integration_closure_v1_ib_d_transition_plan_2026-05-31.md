# V1-IB-C-4 Runtime Integration Closure / V1-IB-D Transition Plan

Decision target:
`v1_ib_c_4_runtime_integration_closure_v1_ib_d_transition_plan_ready_for_counterpart_qa_review`

## Purpose

This is a report-only transition plan after QA accepted:

```text
accept_v1_ib_c_3_adversarial_service_level_phase_closure
```

This report consolidates V1-IB-C runtime integration evidence and asks QA/Counterpart for the next bounded decision: whether V1-IB-C is ready for a formal closure checkpoint and whether Development may proceed to V1-IB-D planning only.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_4_runtime_integration_closure_v1_ib_d_transition_plan_2026-05-31.md`

V1-IB-C-4 is report-only. No source/runtime/test behavior changed. No keyword, regex, synonym, punctuation, phrase, or no-alarm route authority was added. No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise closure, or V2 work occurred. V1-IB-D implementation is not approved by this report.

## Accepted Runtime Integration Foundation

Accepted V1-IB-C runtime integration evidence:

- V1-IB-C-0 integration plan accepted.
- V1-IB-C-1 implementation boundary accepted.
- V1-IB-C-2 runtime integration implemented.
- V1-IB-C-2-A stale final-emission contract authority fix accepted.
- V1-IB-C-2-B legacy authorized-emission test alignment accepted.
- V1-IB-C-2-C runtime integration closure checkpoint accepted.

Key runtime guarantees established by C-2:

- V1-IB contract is the runtime authority path.
- Missing contracts fail closed.
- Invalid contracts fail closed.
- Stale contracts fail closed.
- Raw/normalized hash mismatches fail closed.
- Non-redaction-safe contracts fail closed.
- Unsafe, mixed, ambiguous, unresolved, or unproven contracts fail closed.
- Final emission only accepts a carried V1-IB contract when it is current, hash-matching for the current interaction, valid, and trace-safe.
- Selected governed-report answer text and payloads do not leak on final-emission veto.
- Legacy authorized-emission expectations now require current V1-IB authority for governed business emission.

## Accepted C-3 Adversarial Service Closure

Accepted V1-IB-C-3 adversarial service evidence:

- C-3-2 first adversarial runtime tests accepted.
- C-3-4 visible-context/report-routing closure accepted.
- C-3-5 model-reasoning/report-selector/trace closure accepted.
- C-3-6 long-context/full-call-stack tests accepted.
- C-3-7 phase closure readiness accepted.
- QA accepted `accept_v1_ib_c_3_adversarial_service_level_phase_closure`.

Key adversarial guarantees established by C-3:

- Visible context requires current hash-matching, valid, trace-safe V1-IB authority.
- `context_reuse_allowed=true` alone is not authority.
- Model reasoning cannot activate when V1-IB blocks.
- Report selector cannot override V1-IB.
- Compiled-query execution cannot override V1-IB.
- Governed requery cannot override V1-IB.
- Final-answer authority cannot bypass V1-IB.
- Long-context prior report, visible-context, artifact, grounded state, and safe follow-up history cannot bleed into unsafe later prompts.
- Leak markers do not surface through messages, returned payloads, agent metadata, tool payloads, or trace-like metadata on blocked turns.
- Safe controls require valid current V1-IB authority.

## Accepted Authority Model

The accepted V1-IB runtime authority model remains:

- `IntentBoundaryContract` is sole runtime authority.
- Classifier/proposer output is evidence only.
- Semantic-safe/model output cannot authorize.
- Lexical/token/no-alarm evidence cannot authorize.
- Visible context cannot authorize model reasoning.
- Report selector cannot authorize itself.
- Enterprise model output cannot authorize final answer.
- Final-answer authority cannot bypass V1-IB.
- Missing, invalid, stale, unsafe, mixed, ambiguous, unresolved, non-redaction-safe, or unproven V1-IB contracts fail closed.

## Remaining C-Level Risks

Remaining risks and boundaries:

- Current V1-IB-C evidence is service/unit level, not browser/API UAT.
- Browser/API UAT is not approved by C-4.
- The dirty worktree remains not package-ready.
- Existing old V1-R lexical artifacts and rejected scratch files remain dirty/unpackaged and must be handled later before packaging.
- A future packaging/readiness cleanup phase is needed after later V1-IB-F/UAT gates, not now.
- QA/Counterpart decision is still required before declaring full V1-IB-C closed.
- V1-IB-D implementation is not approved by this transition plan.

## Proposed Next Decisions

QA/Counterpart is asked to decide:

```text
Is V1-IB-C ready for a formal closure checkpoint?
May Development proceed to V1-IB-D planning only?
```

Suggested next slice if approved:

- V1-IB-C-5 runtime integration formal closure checkpoint, report-only

Alternative next slice if QA wants to move planning forward before formal C closure:

- V1-IB-D-0 architecture/planning report, report-only

Development should not start V1-IB-D implementation directly from this report.

## Verification Results

C-3 closure group:

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

Python compile for C/V1-IB touched files:

```text
python3 -m py_compile \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_contract.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_proposal_classifier.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_integration.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_prerouting.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_adversarial_final_emission.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_integration.py \
  impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_final_emission_contract_veto.py \
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
dirty_worktree_count_before_report=129
```

Final hygiene should be rerun after this report is copied into the remote worktree.

## Boundary Statement

V1-IB-C-4 is not implementation. It does not approve browser/API UAT, packaging, staging, commit, push, deployment, strict enforcement, enterprise closure, V2 work, or V1-IB-D implementation.

The worktree remains dirty and not package-ready.
