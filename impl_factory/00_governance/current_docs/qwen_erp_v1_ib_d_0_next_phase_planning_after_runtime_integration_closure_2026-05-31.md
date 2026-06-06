# V1-IB-D-0 Next Phase Planning After Runtime Integration Closure

Decision target:
`v1_ib_d_0_next_phase_planning_after_runtime_integration_closure_ready_for_counterpart_qa_review`

Decision request:
`accept_v1_ib_d_0_next_phase_planning_after_runtime_integration_closure`

## Purpose

This is a report-only V1-IB-D-0 planning packet after QA accepted:

```text
accept_v1_ib_c_runtime_integration_formal_closure
```

V1-IB-C is closed as runtime integration evidence. V1-IB-D begins with planning only. This report does not implement V1-IB-D.

Changed file in this slice:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_0_next_phase_planning_after_runtime_integration_closure_2026-05-31.md`

No source/runtime/test behavior changed. No keyword, regex, synonym, punctuation, phrase, or no-alarm route authority was added. No browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, enterprise/product release closure, or V2 work occurred.

## Current Accepted State

Accepted foundation:

- V1-IB-A contract/validator foundation is closed.
- V1-IB-B proposal classifier evidence-only phase is closed.
- V1-IB-C runtime integration evidence is formally closed.
- QA accepted `accept_v1_ib_c_runtime_integration_formal_closure`.

Current runtime authority state:

- V1-IB contract authority gates runtime lanes.
- Proposal classifier output remains evidence only.
- Runtime integration and adversarial service-level evidence are accepted as V1-IB-C closure evidence.
- Browser/API UAT, packaging, deployment, strict enforcement, enterprise/product release closure, and V2 remain outside the accepted C closure.

## V1-IB-D Purpose

Proposed V1-IB-D theme:

```text
Full Runtime Authority Integration Closure / Cross-Lane Authority Consistency
```

V1-IB-D should prove before implementation closure that the same V1-IB contract authority model is consistently represented across:

- pre-routing gate
- visible context
- report routing
- model reasoning
- final emission
- trace metadata
- runtime diagnostics
- test evidence

V1-IB-D should not broaden intent semantics, add new route authority, or expand ERP behavior. Its purpose is authority consistency, auditability, and closure readiness across already-integrated runtime lanes.

## Proposed V1-IB-D Objectives

V1-IB-D should:

- Confirm one V1-IB authority path is used across runtime lanes.
- Confirm no legacy route-authority path remains active.
- Confirm legacy intent boundary can only restrict/fail closed, not authorize.
- Confirm classifier/proposer evidence is not authority.
- Confirm semantic-safe/model output is not authority.
- Confirm lexical/token/no-alarm evidence is not authority.
- Confirm trace metadata is redaction-safe and authority-consistent.
- Confirm final emission cannot contradict the active V1-IB contract.
- Confirm runtime diagnostics expose enough non-sensitive authority evidence for QA.
- Confirm safe controls still work with valid current V1-IB authority.

## Proposed V1-IB-D Slices

### V1-IB-D-1 Authority Surface Inventory And Call-Site Map

Type: report-only.

Purpose:

- Map all runtime decision surfaces.
- Identify exact call sites that participate in authority, gating, trace, or emission.
- Confirm no new implementation is needed before QA reviews the authority surface.

Required map areas:

- pre-routing response
- visible-context activation
- report routing / compiled query
- governed requery
- model reasoning
- final emission
- trace/metadata append
- authorized emission sinks

### V1-IB-D-2 Authority Consistency Tests

Type: tests-only unless QA approves a source fix after a failing test proves a blocker.

Purpose:

- Add tests proving each lane receives/uses the same current V1-IB contract.
- Prove no lane can reinterpret raw text independently as authority.
- Prove stale, missing, mismatched, or non-redaction-safe contracts fail closed consistently across all lanes.

### V1-IB-D-3 Trace / Diagnostic Contract Audit

Type: report/test-only.

Purpose:

- Ensure trace metadata includes redaction-safe authority proof.
- Ensure trace metadata is consistent with the active V1-IB contract.
- Ensure no business payloads, selected answers, ERP rows, artifacts, narratives, helper payloads, or hidden reasoning leak through diagnostics.

### V1-IB-D-4 Legacy-Authority Retirement Plan

Type: report-only.

Purpose:

- Plan how to retire or quarantine old V1-R lexical artifacts.
- Plan handling for rejected structural classifier scratch files.
- Plan handling for old compatibility paths before packaging.
- Preserve the rule that legacy intent boundary can restrict or fail closed only, not authorize.

### V1-IB-D-5 Formal V1-IB-D Closure Checkpoint

Type: report-only.

Purpose:

- Consolidate D-1 through D-4 evidence.
- Ask QA/Counterpart whether V1-IB-D authority consistency can close.
- Keep packaging/UAT/strict enforcement out of scope unless separately approved later.

## V1-IB-D Non-Goals

V1-IB-D does not approve:

- browser/API UAT
- packaging
- deployment
- strict enforcement
- V2 expansion
- broad ERP family expansion
- new semantic model behavior
- new report families
- cleanup/staging/commit/push
- enterprise/product release closure
- V1-IB-D implementation directly from D-0

## Authority Model

The accepted V1-IB authority model remains:

- `IntentBoundaryContract` is sole runtime authority.
- Classifier/proposer output is evidence only.
- Semantic-safe/model output cannot authorize.
- Lexical/token/no-alarm evidence cannot authorize.
- Visible context cannot authorize model reasoning.
- Report selector cannot authorize itself.
- Enterprise model output cannot authorize final answer.
- Final-answer authority cannot bypass V1-IB.
- Missing, invalid, stale, unsafe, mixed, ambiguous, unresolved, non-redaction-safe, or unproven V1-IB contracts fail closed.

## Dirty Worktree / Package Boundary

The worktree remains dirty and not package-ready.

Old V1-R lexical artifacts and rejected scratch files remain dirty/unpackaged. Removal, retirement, packaging cleanup, staging, commit, push, or package work is future work and must be separately approved.

No staging, commit, push, package, deployment, or cleanup work is allowed in D-0.

## Verification Results

Report present:

```text
Expected after remote copy:
impl_factory/00_governance/current_docs/qwen_erp_v1_ib_d_0_next_phase_planning_after_runtime_integration_closure_2026-05-31.md
```

Git hygiene before this report:

```text
git diff --check: PASS
git diff --cached --check: PASS
excluded/artifact scan: PASS
staged files: 0
dirty_worktree_count_before_report=131
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

Optional accepted baseline:

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

Final report-present and hygiene checks should be rerun after this report is copied into the remote worktree.

## Decision Request

QA/Counterpart is asked to decide:

```text
accept_v1_ib_d_0_next_phase_planning_after_runtime_integration_closure
```

If accepted, next step should be:

```text
V1-IB-D-1 authority surface inventory and call-site map, report-only
```

Development should not implement V1-IB-D directly from this report.
