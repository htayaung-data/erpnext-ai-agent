# V1-IB-C-2-B Legacy Authorized-Emission Test Alignment

Decision target:

`v1_ib_c_2_b_legacy_authorized_emission_test_alignment_ready_for_counterpart_qa_review`

## Scope

C-2-B aligns legacy authorized-emission tests with the accepted V1-IB-C-2 and C-2-A authority model.

This is a test-alignment slice only. It does not modify runtime source, routing behavior, visible-context wiring, report routing, proposal classification, validator logic, or final-emission implementation.

## Files Changed

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_authorized_emission_contracts.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_2_b_legacy_authorized_emission_test_alignment_2026-05-30.md`

`test_service_control_authorized_emission_contracts.py` was inspected and run because it is an allowed legacy authorized-emission test file, but no C-2-B edits were required there.

## Legacy Expectations Updated

Older broad authorized-emission tests assumed governed business final emission could pass from final-answer authority, grounded report context, or selected artifact metadata alone.

C-2-B updates those expectations:

- governed report and visible-context business emissions now include a current, hash-matching, trace-redaction-safe V1-IB boundary when they are meant to pass
- business final emission with final-answer authority but no V1-IB contract now expects the V1-IB veto/control response
- business final emission with a stale V1-IB allow contract now expects the veto/control response
- blocked/veto paths assert selected answer text does not leak
- bounded policy-boundary tests remain valid because policy/control boundary emissions are not governed business answer types
- existing final-answer authority block tests keep their original purpose by adding a current V1-IB allow contract, then proving final-answer authority can still block

## Added Regressions

Added explicit regressions proving old behavior is no longer allowed:

- governed report answer plus valid final-answer authority plus no V1-IB contract vetoes and does not leak selected answer text
- governed report answer plus stale V1-IB allow contract vetoes and does not leak selected answer text

Added positive controls:

- governed report answer plus valid final-answer authority plus current hash-matching V1-IB allow contract emits governed report
- visible-context answer plus current hash-matching V1-IB context allow contract emits visible-context answer

## Runtime Source Change Proof

C-2-B did not edit runtime source files.

Existing dirty runtime source files from earlier C-2/C-2-A implementation slices remain in the worktree and are not introduced by this test-alignment slice:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_integration.py`

## Verification Results

- Aligned legacy authorized-emission tests: PASS
  - `test_authorized_emission_contracts.py`: `14 passed`
  - `test_service_control_authorized_emission_contracts.py`: `3 passed`
- V1-IB runtime/final-emission/contract/classifier tests: PASS, `130 passed`
- Python compile for touched test files: PASS
- Qwen enterprise guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Raw assistant append scan: PASS, only:
  - `authorized_emission.py:271`
  - `authorized_emission.py:327`
- `git diff --check`: PASS
- Path-aware excluded/artifact scan: PASS
- Staged files: PASS, `0`

## Non-Actions

No runtime source changes, `service.py` edits, `authorized_emission.py` edits, contract/validator changes, classifier changes, visible-context wiring, report-routing changes, browser/API UAT, staging, commit, push, packaging, deployment, strict enforcement, or V2 work occurred in C-2-B.
