# V1-IB-B-B Proposal Classifier Closure Checkpoint

Decision target:

`v1_ib_b_b_proposal_classifier_closure_checkpoint_ready_for_counterpart_qa_review`

## Scope

QA_Risk accepted V1-IB-B-A after the evidence strictness fix. This checkpoint consolidates V1-IB-B and V1-IB-B-A before any packaging or integration discussion.

Files changed in this B-B slice:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_proposal_classifier.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_proposal_classifier_closure_checkpoint_2026-05-29.md`

The proposal classifier source was audited and did not require changes for this closure checkpoint.

No runtime routing, `service.py`, `authorized_emission.py`, visible-context wiring, report routing integration, final-emission change, browser/API UAT, staging, commit, push, deployment, strict enforcement, packaging, or V2 work occurred.

## Closure Findings

The V1-IB-B proposal classifier is coherent with the accepted V1-IB-A/Q authority model:

- Classifier output remains evidence-only.
- Classifier output has no route-authority fields anywhere in nested payloads.
- Classifier cannot authorize report routing.
- Classifier cannot authorize context reuse.
- Classifier cannot authorize model reasoning.
- Classifier cannot authorize final emission.
- Classifier cannot set governed ERP answer mode.
- Classifier cannot set `authority_decision=allow_report`.
- Validator remains the sole route authority.
- Safe factual subset produces clean proposal evidence only.
- Safe factual route passes only through accepted validator positive replay and invariants.
- Unsafe prompts produce unsafe/restrictive evidence or ambiguity.
- Mixed prompts preserve factual plus unsafe evidence.
- Ambiguous prompts remain unproven and fail closed.
- Visible-context references are evidence only and do not activate context.
- Unapproved extra text is surfaced as ambiguity, residual, or restrictive evidence.
- Lexical/token logic is not route authority.
- Absence of alarm is not safety.

Old V1-IB-B/B-A/B-B structural classifier artifacts remain rejected historical scratch and are not accepted by this checkpoint:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py`

## Closure Assertion

Added `test_v1_ib_b_b_closure_matrix_preserves_evidence_only_boundary`.

The closure test passes safe factual, unsafe, mixed, ambiguous, visible-context, and extra-business-text prompts through the classifier and accepted validator fixture. It proves:

- classifier output recursively has no route-authority fields
- safe factual proposals are blocked without validator replay
- safe factual proposals may allow only after accepted positive validator-owned replay/invariants pass
- unsafe, mixed, ambiguous, visible-context, and extra-business-text proposals remain blocked even under semantic-safe and optimistic replay provenance
- classifier never directly sets authority fields

## Dirty Worktree / Packaging Status

The worktree remains dirty and is not package-ready.

Current dirty state includes accepted V1-IB-A and V1-IB-B artifacts, rejected historical V1-IB-B structural artifacts, V1-R artifacts, and pre-existing runtime/source/test changes outside this B-B closure slice. No staging occurred.

Any future packaging step must explicitly classify accepted versus rejected artifacts before staging.

## Verification

Remote verification on `/tmp/erpai_pr5_postmerge_verify`:

- V1-IB proposal-classifier tests: PASS, `12 passed`
- V1-IB contract validator tests: PASS, `100 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`
- `git diff --check`: PASS
- Path-aware excluded/artifact scan: PASS, clean for `__pycache__`, `.pyc`, generated governance artifacts, UAT/browser artifacts
- Staged files: PASS, `0`

## Decision

`v1_ib_b_b_proposal_classifier_closure_checkpoint_ready_for_counterpart_qa_review`
