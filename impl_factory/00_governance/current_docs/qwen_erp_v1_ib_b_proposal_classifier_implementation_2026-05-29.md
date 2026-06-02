# V1-IB-B Proposal Classifier Implementation

Decision target:

`v1_ib_b_proposal_classifier_implementation_ready_for_counterpart_qa_review`

## Scope

This slice implements the V1-IB-B pure proposal classifier only.

Files changed:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_proposal_classifier.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_intent_boundary_proposal_classifier.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_proposal_classifier_implementation_2026-05-29.md`

No runtime routing, visible-context activation, final-emission behavior, browser/UAT artifact, staging, commit, push, deployment, strict enforcement, or V2 work occurred.

Old V1-IB-B/B-A/B-B artifacts remain rejected historical context and were not edited or accepted by this slice.

## Authority Model

The classifier output is evidence only.

It does not authorize:

- report routing
- context reuse
- model reasoning
- final emission
- governed ERP answer mode
- `authority_decision=allow_report`
- validator-owned safe route authority

The accepted A-Q authority model remains unchanged:

- proposer/model output is evidence only
- verifier output is consistency evidence only
- proof, analysis, execution, and replay-status records are provenance only
- semantic-safe output cannot authorize
- lexical, regex, synonym, keyword, phrase, punctuation, and no-alarm logic cannot authorize
- only positive validator-owned safe factual replay plus all accepted contract invariants can allow governed ERP routing

## Classifier Output

The public API is:

`build_intent_boundary_proposal(raw_message: str) -> dict`

The returned payload contains proposal evidence only:

- raw and normalized message hashes
- normalized message
- proposal source/run/status/confidence fields
- clause candidates and spans
- residual and connector evidence
- ERP target candidates
- visible-context reference candidates
- factual lookup evidence
- decision/advice/action/legal/manipulation/prediction evidence
- mixed and ambiguous evidence
- completeness/status/confidence fields
- trace-redaction status

The classifier explicitly removes route-authority keys from its top-level payload, and the test suite recursively asserts route-authority fields are absent from nested proposal evidence as well.

## Test Matrix

The V1-IB-B proposal-classifier tests cover:

- classifier output has no route-authority fields
- safe factual governed subset produces evidence only
- safe factual proposal can route only after accepted validator replay/invariants pass
- unsafe prompts do not route from classifier output
- mixed prompts preserve factual plus unsafe evidence
- ambiguous prompts remain unproven/fail-closed
- visible-context references remain evidence only
- proposer omission attempts leave residual/incomplete evidence visible to the validator
- semantic-safe cannot compensate for classifier uncertainty
- lexical/punctuation/no-alarm output cannot route without validator replay

Adversarial prompt families include safe factual, unsafe, mixed, ambiguous, and visible-context prompts from the V1-IB-B approval boundary.

## Verification

Remote verification on `/tmp/erpai_pr5_postmerge_verify`:

- V1-IB proposal-classifier tests: PASS, `10 passed`
- V1-IB contract validator tests: PASS, `100 passed`
- Python compile for touched classifier/test files: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`
- `git diff --check`: PASS
- Path-aware excluded/artifact scan: PASS, clean for `__pycache__`, `.pyc`, generated governance artifacts, UAT/browser artifacts
- Staged files: PASS, `0`

## Dirty Worktree Note

The worktree is still dirty and not package-ready. This slice added only the approved V1-IB-B proposal-classifier file, focused test file, and this governance report. Pre-existing dirty/untracked V1-IB-A, V1-R, rejected V1-IB-B, and runtime files remain outside this slice and are not accepted or packaged here.

## Closure

V1-IB-B implements a pure proposal/evidence classifier. It does not grant route permission. The accepted validator remains the sole authority for governed ERP routing.
