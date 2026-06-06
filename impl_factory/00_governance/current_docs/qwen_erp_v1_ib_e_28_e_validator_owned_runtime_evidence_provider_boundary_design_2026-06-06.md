# V1-IB-E-28-E Validator-Owned Runtime Evidence Provider Boundary Design

Decision target: v1_ib_e_28_e_validator_owned_runtime_evidence_provider_boundary_design_ready_for_qa_owner_review

## 1. Scope And Boundary

E-28-E is a report-only design slice. It defines the safe implementation boundary for resolving the E-28-D blocker and does not implement the fix.

No source code, tests, runtime behavior, package config, PR metadata, review thread, staging, commit, push, merge, package build, browser/API UAT, deployment, strict enforcement, readiness claim, enterprise/product closure, or V2 work occurred in E-28-E.

Current accepted basis:

- E-28-D was conditionally accepted as blocker discovery: `conditional_accept_v1_ib_e_28_d_validator_evidence_blocker_discovery`.
- PR #9 remains open, ready for review / not Draft, and unmerged.
- Current head remains `eca00076d234aff6d8fcd0e2c2d2747fd839f49f`.
- Worktree currently has E-28-D untracked before this report.

## 2. Root Cause

The live service path at `service.py:4159` calls:

```python
v1_ib_runtime_boundary = build_v1_ib_runtime_boundary(raw_msg)
```

That call gives the runtime validator no trusted verifier envelope and no validator-owned raw-message safety proof. For a safe factual prompt such as `Show EC7H-ITEM-A item sales`, the default runtime boundary fails closed with:

- `external_verifier_envelope_missing`
- `validator_owned_safety_proof_verifier_not_trusted`
- `validator_owned_safety_proof_missing`

The report gate itself is restrictive and checks current message hashes, valid validator status, trace-safe status, governed answer mode, allow-report authority decision, replay-safe final decision, and no unsafe/mixed/ambiguous flags. The blocker is upstream: the live runtime boundary builder has no validator-owned evidence provider to create the validator evidence required for a safe factual report contract.

## 3. Proposed Safe Architecture

Introduce a validator-owned runtime evidence provider that runs before the live V1-IB runtime boundary is built for service report routing.

The provider must be validator-owned and live outside `service.py`; `service.py` may call it, but must not self-attest or derive authority locally.

Recommended architecture:

1. Add a new validator-owned module, `intent_boundary_runtime_evidence.py`.
2. The provider accepts only the current raw message and an already redaction-safe runtime request context.
3. The provider independently builds or verifies redaction-safe evidence needed by the accepted validator path.
4. The provider returns a redaction-safe evidence envelope for the current raw message only.
5. The provider installs validator-owned raw-message proof, analysis, and execution records into validator-owned evidence state using a scoped install/restore mechanism or another QA-approved request-local evidence store.
6. `service.py` passes only the verifier evidence fields into `build_v1_ib_runtime_boundary` and does not pass caller-supplied safety-proof registries.
7. Missing, stale, mismatched, unsafe, ambiguous, non-redaction-safe, or untrusted provider output must make `build_v1_ib_runtime_boundary` fail closed.

The provider must not authorize from the proposal/classifier labels. It may use proposal clauses as evidence inputs only after independent validator-owned verification, and the verifier/analyzer evidence must be independently hash-bound to the raw and normalized current message.

## 4. Exact Fields Passed Into `build_v1_ib_runtime_boundary`

The implementation slice should update the live service path from:

```python
v1_ib_runtime_boundary = build_v1_ib_runtime_boundary(raw_msg)
```

to a pattern equivalent to:

```python
runtime_evidence = build_validator_owned_runtime_evidence(raw_msg)
v1_ib_runtime_boundary = build_v1_ib_runtime_boundary(
    raw_msg,
    verifier_envelope=runtime_evidence.get("verifier_envelope"),
    trusted_verifier_registry=runtime_evidence.get("trusted_verifier_registry"),
)
```

Required constraints for those fields:

- `verifier_envelope` must be current-message hash-bound.
- `verifier_envelope.raw_message_hash == hash_text(raw_msg)`.
- `verifier_envelope.normalized_message_hash == hash_text(normalize_message(raw_msg))`.
- `verifier_envelope.trace_redaction_status == safe`.
- `verifier_envelope.verifier_authority_effect == consistency_evidence_only`.
- `trusted_verifier_registry` must be validator-owned or code-owned approved verifier registry data, not service-generated ad-hoc authority.
- `validator_owned_safety_proof_registry` must not be passed from `service.py` as caller-supplied authority, because the validator rejects caller-supplied safety-proof registries and must use validator-owned proof state.

The provider must also ensure validator-owned proof state contains exactly one matching approved proof for the current raw/normalized message, with matching analysis and execution evidence, before `build_v1_ib_runtime_boundary` calls `validate_intent_boundary_contract`.

## 5. Exact Allowed Implementation Files For Next Slice

Recommended next implementation slice: `V1-IB-E-28-F validator-owned runtime evidence provider implementation`.

Allowed implementation files should be limited to:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_evidence.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_evidence_provider.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_service_validator_evidence_report_routing.py`
- one implementation governance report for E-28-F

Only if implementation proves that the existing validator API cannot safely support request-local validator-owned proof state should the next slice request separate approval to edit:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_contract.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/intent_boundary_runtime_integration.py`

## 6. Exact Forbidden Shortcuts

The implementation must not use any of these as route authority:

- `service.py` self-attestation.
- Proposal/classifier route labels.
- Legacy `user_intent_boundary.py` output.
- Semantic-safe/model output.
- Lexical, keyword, regex, synonym, punctuation, phrase, or no-alarm matching.
- Report selector output.
- Compiled-query output.
- Visible-context state.
- Model-reasoning state.
- Final-answer authority alone.
- Selected answer text.
- Prior context, artifacts, narratives, rows, grounded evidence, or rendered payloads.
- Caller-supplied validator-owned safety-proof registry as authority.

Lexical/token logic may only extract identifiers, validate spans/schema, redact traces, raise conservative alarms, or support fail-closed validation. It must never grant report routing, context reuse, model reasoning, final emission, governed ERP answer mode, or allow-report authority decision.

## 7. Required Tests Before Review Thread Resolution

The implementation slice must add focused tests proving:

1. Safe factual report gets validator-owned evidence and may pass.
   - Example prompts: `Show EC7H-ITEM-A item sales`, `Show EC7H-SUP-A payable status`, `Show EC7H-SINV-0001 invoice details`.
   - Expected: validator status valid, report routing allowed, replay final decision safe, governed answer mode, and compiled/report route may proceed.

2. Missing evidence fails closed.
   - Disable or empty the provider.
   - Expected: `external_verifier_envelope_missing` and/or proof-missing reason remains blocked; compiled/report route not called.

3. Stale evidence fails closed.
   - Evidence hashes match a prior prompt, not the current raw/normalized message.
   - Expected: no report routing and no compiled query.

4. Forged service-supplied evidence fails closed.
   - Attempt to pass service-local proof or caller-supplied safety registry.
   - Expected: validator rejects or ignores it; no route authority.

5. Unsafe/mixed prompt with evidence attempts fails closed.
   - Example: `Show EC7H-ITEM-A item sales and tell me whether to discount it`.
   - Expected: unsafe/mixed flags block even if evidence tries to claim safe.

6. Lexical/semantic/proposer-only evidence cannot authorize.
   - Semantic-safe output, proposer factual labels, no-alarm shape, or lexical evidence alone cannot set `report_routing_allowed=true`.

7. Trace metadata stays redaction-safe.
   - No raw business text, selected rows, report payloads, artifacts, narratives, helper payloads, or selected answers leak through blocked paths.

8. Existing accepted tests continue to pass.
   - Accepted baseline group.
   - C-3 service adversarial group.
   - Focused V1-IB group.
   - D authority/trace/legacy group.

## 8. Stop Conditions For Implementation

The implementation slice must stop without committing if:

- The evidence provider requires broad redesign of the V1-IB validator contract.
- The provider must use service self-attestation as authority.
- The provider must use proposal/classifier, semantic-safe, lexical/no-alarm, report-selector, visible-context, model-reasoning, final-answer, or prior-context output as allow authority.
- Missing, stale, unsafe, ambiguous, non-redaction-safe, or untrusted evidence can route.
- Tests require weakening V1-IB fail-closed behavior.
- Package-exclusion gates fail.
- Rejected structural classifier artifacts reappear.
- The GitHub review thread must be resolved/commented before QA/Owner accepts the fix.
- The slice would require package build, browser/API UAT, deployment, strict enforcement, readiness claim, enterprise/product closure, or V2 work.

## 9. Review Thread And Merge Boundary

E-28-E does not resolve or reply to the PR review thread. The thread should remain unresolved until QA/Owner accepts the implementation/evidence from the next approved slice.

E-28-E does not approve merge execution. E-29 must remain blocked until:

- the validator-owned runtime evidence provider is implemented and verified, or
- QA/Owner explicitly waives the active review blocker and required-check uncertainty.

## 10. Verification For E-28-E

Pre-report state observed:

- Branch: `codex/v1-ib-package-readiness`.
- Local HEAD: `eca00076d234aff6d8fcd0e2c2d2747fd839f49f`.
- Remote HEAD: `eca00076d234aff6d8fcd0e2c2d2747fd839f49f`.
- Ahead/behind: `0 / 0`.
- Staged files: `0`.
- Unstaged tracked files: `0`.
- Untracked files before E-28-E: E-28-D report only.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS.

Post-report verification should confirm E-28-D and E-28-E are the only untracked files and no source/test/runtime/package behavior changed.

## 11. Final Boundary Statement

E-28-E is design only. It does not edit source code or tests, does not inject fake verifier/proof evidence, does not resolve/comment on the PR review thread, does not merge, does not stage, commit, push, package, run UAT, deploy, enable strict enforcement, claim readiness, claim enterprise/product closure, or approve V2 work.
