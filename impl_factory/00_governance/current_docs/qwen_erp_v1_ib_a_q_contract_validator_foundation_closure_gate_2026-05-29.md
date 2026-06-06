# V1-IB-A-Q Contract / Validator Foundation Closure Gate

## Scope

V1-IB-A-Q is a report and closure-audit test slice. It does not continue V1-IB-B and does not change runtime routing, visible-context behavior, final-emission behavior, model endpoints, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work.

The only test change is a closure invariant test in the existing V1-IB contract validator test suite. No `intent_boundary_contract.py` behavior change was required.

## Reports Reviewed

Reviewed V1-IB-A through V1-IB-A-P-C governance reports:

- V1-IB-A contract/schema/validator foundation
- V1-IB-A-A through A-C authority hardening
- V1-IB-A-D lexical-authority removal
- V1-IB-A-E through A-H proposal/verifier/self-attestation guards
- V1-IB-A-I through A-O provenance, proof, evidence, analysis, and execution integrity gates
- V1-IB-A-P through P-C validator-owned replay authority, positive safe factual replay, punctuation handling, and durable sibling/adversarial tests

## Final Accepted Authority Model

The consolidated V1-IB-A foundation authority model is:

- Proposer/model output is evidence only and cannot authorize report routing.
- Verifier output is consistency evidence only and cannot authorize report routing.
- Proof, analysis, execution, registry, hash, attestation, artifact, and stored replay records are provenance/audit only and cannot authorize routing by themselves.
- Stored `replay_status=verified` cannot authorize routing.
- Semantic safe output cannot authorize routing; semantic unsafe or ambiguous output can restrict.
- Lexical, regex, keyword, synonym, punctuation, and phrase evidence cannot authorize routing.
- Punctuation is not intent. It may restrict when replay cannot prove safety, but it cannot grant or deny a proven positive safe factual lookup by itself.
- Governed ERP routing requires positive validator-owned safe factual replay plus all existing schema, completeness, verifier provenance, proof, evidence, analysis, execution, redaction, residual, connector, and reference invariants.
- Unknown, ambiguous, unsafe, mixed, unresolved, stale, conflicting, non-redaction-safe, or unproven natural-language ERP intent fails closed.
- All failure paths must keep `report_routing_allowed=false`, `context_reuse_allowed=false`, `model_reasoning_allowed=false`, `final_emission_allowed=false`, `required_answer_mode != governed_erp_answer`, and `authority_decision != allow_report`.
- The safe factual route is a narrow V1 subset only. It is not broad natural-language ERP understanding.

## Closure Test Added

Added `test_v1_ib_a_q_closure_authority_model_requires_positive_validator_owned_replay`.

The test proves:

- proposer plus verifier agreement alone cannot route
- stored `replay_status=verified` cannot route if validator-owned replay config is missing
- semantic safe cannot route without validator-owned proof/replay authority
- regex/lexical classifier source cannot route
- ambiguous natural-language ERP intent with safe provenance assertions cannot route
- positive validator-owned safe factual replay can route only when all invariants pass

## Stale Authority Claim Audit

The report audit found no current accepted V1-IB-A-P-C closure claim that lexical, synonym, regex, keyword, or punctuation rules are route authority.

Earlier V1-IB-A-B/A-C reports describe pre-A-D raw-message evidence hardening, but V1-IB-A-D explicitly removes lexical/regex/keyword/pattern route authority and the later V1-IB-A-P through P-C reports supersede the safety authority model with validator-owned positive safe factual replay.

V1-IB-A-P-B and P-C explicitly state:

- punctuation is never authority
- absence of punctuation authorizes nothing
- stored proof, analysis, execution, verifier agreement, and semantic-safe output remain provenance/audit only
- governed ERP report routing requires positive validator-owned safe factual replay proof

## Dirty Worktree / Packaging Status

This closure gate is not package-ready.

Remote worktree dirty count before syncing this A-Q slice was `86`.
Remote worktree dirty count after syncing this A-Q slice is `87`.

Observed dirty categories:

- Modified runtime/source/test files from prior slices:
  - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py`
  - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
  - `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_service_control_authorized_emission_contracts.py`
- Untracked V1-IB-A through V1-IB-A-P-C reports and contract validator files
- Untracked V1-R reports and intent-boundary regression files
- Deferred EC-10-G report
- Rejected/unaccepted V1-IB-B artifacts

Already-created V1-IB-B artifacts are not accepted by this checkpoint:

- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_deterministic_structural_classifier_2026-05-28.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_a_factual_lookup_precedence_raw_safety_hardening_2026-05-28.md`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_b_b_passive_action_needed_structural_hardening_2026-05-28.md`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_structural_classifier.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_structural_classifier.py`

Any future packaging step must classify the full dirty set and explicitly exclude or supersede rejected V1-IB-B artifacts before staging.

## Verification

Local verification before remote sync:

- V1-IB contract validator tests: PASS, `100 passed`
- Python compile for touched test file: PASS

Remote verification after sync:

- V1-IB contract validator tests: PASS, `100 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`
- Diff/check: PASS
- Excluded/artifact scan: PASS, clean
- Staged files: PASS, `0`

## Decision Target

`v1_ib_a_q_contract_validator_foundation_closure_gate_ready_for_counterpart_qa_review`
