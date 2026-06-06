# V1-IB-E-28-D Review Thread Validator Evidence Resolution

Decision target: v1_ib_e_28_d_review_thread_validator_evidence_resolution_blocked_pending_validator_owned_runtime_evidence_provider

## 1. Scope And Boundary

E-28-D inspected the active PR review blocker at `service.py:4159` / `discussion_r3356338969`:

- Review title: `Provide validator evidence before gating all reports`
- PR: https://github.com/htayaung-data/erpnext-ai-agent/pull/9
- Branch: `codex/v1-ib-package-readiness`
- Worktree: `/tmp/erpai_v1_ib_package_readiness_clean`
- Starting local/remote/PR head: `eca00076d234aff6d8fcd0e2c2d2747fd839f49f`

This report records blocker evidence and stops E-28-D without changing runtime behavior. No code, tests, runtime, package config, PR metadata, or review thread state was changed.

## 2. Review Blocker Reproduced

The reviewed service call site is:

```python
legacy_user_intent_boundary = build_user_intent_boundary_contract(raw_msg)
v1_ib_runtime_boundary = build_v1_ib_runtime_boundary(raw_msg)
user_intent_boundary = merge_v1_ib_with_legacy_boundary(
    v1_ib_runtime_boundary,
    legacy_user_intent_boundary,
)
```

The live service path calls `build_v1_ib_runtime_boundary(raw_msg)` without verifier/proof evidence. A direct runtime probe for the safe factual control `Show EC7H-ITEM-A item sales` confirmed the review concern:

```text
validator_status=invalid
report_routing_allowed=False
required_answer_mode=clarification
authority_decision=block
replayed_raw_message_safety_final_decision=blocked
v1_ib_runtime_status=fail_closed
v1_ib_runtime_blocking_reason=external_verifier_envelope_missing;validator_owned_safety_proof_verifier_not_trusted;validator_owned_safety_proof_missing
deterministic_validator_errors=[
  external_verifier_envelope_missing,
  validator_owned_safety_proof_verifier_not_trusted,
  validator_owned_safety_proof_missing,
]
```

This means the current live pre-routing authority can block a normal safe factual report prompt before governed report execution because validator-owned evidence is absent.

## 3. Existing Validator Authority Requirements

The accepted validator path requires all of the following for governed report routing:

- Current raw-message hash match.
- Current normalized-message hash match.
- `validator_status == valid`.
- `trace_redaction_status == safe`.
- `required_answer_mode == governed_erp_answer`.
- `authority_decision == allow_report`.
- `report_routing_allowed == true`.
- `replayed_raw_message_safety_final_decision == safe`.
- No decision, advice, business-action, policy-boundary, mixed, or ambiguous flags.
- Trusted external clause-role verifier evidence.
- Validator-owned raw-message safety proof.
- Validator-owned raw-message analysis and execution proof.

The service report gate itself is restrictive and checks the current-message identity plus valid/trace-safe/replay-safe authority fields. The blocker is upstream: the live service builder does not receive or construct the validator-owned evidence required to produce a valid V1-IB report contract.

## 4. Why A Narrow Code Fix Was Not Applied In E-28-D

A safe fix cannot be achieved by simply passing a caller-supplied safety registry. The contract validator explicitly rejects caller-supplied safety proof registries with `validator_owned_safety_proof_registry_caller_supplied_not_allowed` and reads validator-owned module state instead.

A safe fix also cannot be achieved by deriving report authority from any of the following:

- Lightweight proposal/classifier output.
- Legacy `user_intent_boundary.py` output.
- Report selector output.
- Semantic-safe/model output.
- Lexical, keyword, regex, synonym, punctuation, phrase, or no-alarm logic.
- A service-local ad-hoc proof generated from the same proposal being validated.

Creating production validator evidence requires a trusted verifier/analyzer/provenance provider that can populate or expose validator-owned evidence before the live service gate. That provider is a design-significant authority surface and should be implemented in a separate approved fix slice, not improvised in E-28-D.

## 5. Existing Test Evidence Reviewed

Accepted tests prove that the validator can authorize safe factual report routing when trusted verifier and validator-owned proof fixtures are installed:

- `test_safe_report_routes_through_accepted_validator_replay_fixture`
- `test_positive_safe_factual_replay_controls_pass_with_full_invariants`
- `test_positive_safe_factual_replay_controls_pass_with_question_punctuation`
- `test_safe_factual_no_question_control_passes_positive_replay`

Those tests also prove that default missing proof fails closed. The test fixture registries are explicitly test-only and cannot be treated as production route authority.

## 6. Required Future Fix Slice

Recommended next slice:

`V1-IB-E-28-E validator-owned runtime evidence provider for report routing`

The future slice should be implementation-first only after QA/Owner approval and should define a real validator-owned runtime evidence provider that supplies the service gate with proof without weakening V1-IB authority.

Minimum future requirements:

- Add or wire a validator-owned verifier/analyzer evidence provider before `build_v1_ib_runtime_boundary(raw_msg)`.
- Do not pass caller-supplied safety-proof registries as authority.
- Preserve current raw/normalized hash matching.
- Preserve `validator_status == valid`.
- Preserve `trace_redaction_status == safe`.
- Preserve replay final decision `safe`.
- Preserve no unsafe/mixed/ambiguous flags.
- Preserve fail-closed behavior when evidence is missing, stale, mismatched, unsafe, non-redaction-safe, ambiguous, or untrusted.
- Add focused service tests proving safe factual prompts route only when validator-owned runtime evidence exists.
- Add focused service tests proving missing runtime evidence still fails closed.
- Add adversarial tests proving unsafe/mixed prompts cannot be authorized by the evidence provider.

## 7. E-29 Merge Boundary Impact

E-29 merge execution must remain blocked. The review thread should not be resolved until QA/Owner accepts either:

- a separately approved E-28-E runtime evidence provider fix, or
- an explicit Owner waiver explaining why the current fail-closed behavior is acceptable despite the active review blocker.

## 8. Verification Performed

Pre-inspection state:

- Branch: `codex/v1-ib-package-readiness`.
- Local HEAD: `eca00076d234aff6d8fcd0e2c2d2747fd839f49f`.
- Remote HEAD: `eca00076d234aff6d8fcd0e2c2d2747fd839f49f`.
- Ahead/behind: `0 / 0`.
- Worktree before report: staged `0`, unstaged `0`, untracked `0`.
- PR #9: open, ready for review / not Draft, unmerged.

Probe evidence:

- Safe factual default runtime boundary failed closed with missing verifier/proof evidence.
- Service `service.py:4159` currently calls `build_v1_ib_runtime_boundary(raw_msg)` without verifier/proof evidence.
- Contract validator rejects caller-supplied safety proof registries and requires validator-owned proof state.

No full verification suite was run because E-28-D stopped before code/test implementation. No package-exclusion or authority model changes were made.

## 9. Explicit Non-Actions

E-28-D performed none of the following:

- No source code edit.
- No test edit.
- No runtime behavior change.
- No package config change.
- No review-thread resolution.
- No GitHub thread reply/comment.
- No PR state/title/body/reviewer/label/approval/base/head change.
- No merge.
- No push.
- No package build.
- No browser/API UAT.
- No deployment.
- No strict enforcement.
- No package readiness claim.
- No release readiness claim.
- No enterprise/product closure claim.
- No V2 work.

## 10. Conclusion

E-28-D is stopped as a blocker-discovery/evidence slice. The review comment is valid: the live service path lacks validator-owned verifier/proof evidence before strict V1-IB report gating. A narrow safe correction requires a separately approved validator-owned runtime evidence provider slice.
