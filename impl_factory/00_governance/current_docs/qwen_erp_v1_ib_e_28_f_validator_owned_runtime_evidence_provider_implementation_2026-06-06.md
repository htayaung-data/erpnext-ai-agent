# V1-IB-E-28-F Validator-Owned Runtime Evidence Provider Implementation

Decision target: `v1_ib_e_28_f_validator_owned_runtime_evidence_provider_implementation_ready_for_qa_owner_review`

## Scope And Boundary

E-28-F implements the validator-owned runtime evidence provider needed for the PR review blocker: `Provide validator evidence before gating all reports.` The slice is limited to runtime evidence provider wiring, focused tests, and this governance report.

No PR merge, review-thread resolution/comment, package build, browser/API UAT, deployment, strict enforcement, package readiness claim, release readiness claim, enterprise/product closure, or V2 work occurred.

## Root Cause Fixed

`service.py` previously built the V1-IB runtime boundary with only the raw message. Safe factual report prompts therefore failed closed because the validator did not receive independent clause-role verifier evidence or validator-owned raw-message safety proof evidence.

The failing reasons were:

- `external_verifier_envelope_missing`
- `validator_owned_safety_proof_verifier_not_trusted`
- `validator_owned_safety_proof_missing`

## Implementation Summary

Changed files:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_evidence.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_evidence_provider.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_e_28_f_validator_owned_runtime_evidence_provider_implementation_2026-06-06.md`

The new provider creates a scoped validator-owned evidence context for one raw user message. It installs verifier, safety proof, raw-message analysis, and analysis execution records into validator-owned registries only for the duration of `build_v1_ib_runtime_boundary(...)`.

`service.py` now calls `_build_v1_ib_runtime_boundary_for_service(raw_msg)`, which invokes `validator_owned_runtime_evidence(raw_msg)` and passes only the resulting verifier envelope into the existing V1-IB validator path. Service code does not self-attest report authority and does not fabricate proof registry state.

## Authority Model Preserved

Only a current, hash-matching, trace-safe, validated V1-IB contract can allow report routing.

The provider does not make proposer/classifier labels, semantic-safe output, lexical/token/no-alarm evidence, report selector output, visible context, model reasoning, final-answer authority, prior context, selected rows, artifacts, narratives, grounded evidence, rendered payloads, or trace metadata into route authority.

Missing, stale, forged, unsafe, mixed, ambiguous, malformed, non-redaction-safe, semantic-only, or proposer-only evidence remains fail-closed.

## Focused Test Evidence

Added focused tests proving:

- Safe factual report with validator-owned runtime evidence can pass the report authority gate.
- The same safe factual report without provider evidence fails closed.
- Stale provider evidence fails closed for the current message.
- Caller-supplied safety proof registry evidence is rejected as forged/non-authoritative.
- Unsafe/mixed prompt with provider evidence still fails closed.
- Semantic-safe output cannot authorize without provider evidence.
- Proposer/classifier-only evidence cannot authorize without provider evidence.
- The service helper uses the provider and fails closed when the provider yields no evidence.

## Verification Results

| Check | Result |
| --- | --- |
| Focused E-28-F provider tests | PASS: 9 tests |
| Accepted baseline group | PASS: 157 tests |
| C-3 service adversarial group | PASS: 19 tests |
| Focused contract/classifier/runtime/authorized-emission group | PASS: 147 tests |
| D authority/trace/legacy group | PASS: 18 tests |
| Python compile for qwen_chat source/tests | PASS |
| Package-exclusion gates | PASS: root `=`, rejected structural source/test, old direct lexical tests, old `qwen_erp_v1_r_*` reports, and EC-10-G absent |
| Runtime rejected structural classifier refs | PASS: `[]` |
| Qwen enterprise guardrail | PASS |
| Fake-Frappe service import | PASS |
| Direct assistant inventory | PASS: `0 / 1 / 27` |
| Raw append scan | PASS: `authorized_emission.py:271`, `authorized_emission.py:327` |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS before staging |
| PR #9 public state | PASS: open, ready for review / not Draft, unmerged, base `main`, head `codex/v1-ib-package-readiness`, head SHA `eca00076d234aff6d8fcd0e2c2d2747fd839f49f` |

The clean worktree environment does not have `gh` installed, so no thread-aware GraphQL mutation or resolution was attempted. E-28-F leaves `discussion_r3356338969` for QA/Owner review and does not comment on or resolve it.

## Boundary Statement

E-28-F does not resolve or comment on the GitHub review thread. It does not approve merge, package build, browser/API UAT, deployment, strict enforcement, package readiness, release readiness, enterprise/product closure, or V2 work.
