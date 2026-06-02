# V1-IB-A-G Independent Clause-Role Verification Guard

Date: 2026-05-28

Decision target: `v1_ib_a_g_independent_clause_role_verification_guard_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-G is a pure contract/validator hardening slice. It addresses the rejected V1-IB-A-F gap where a trusted proposer could split a mixed unsafe request into multiple clauses and falsely label every clause as factual.

No runtime routing, visible-context wiring, final-emission wiring, model endpoint call, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

A proposer may propose clause roles, but it may not verify clause roles. Natural-language report routing now requires independent clause-role verification evidence before `report_routing_allowed=true`.

The verifier remains consistency evidence only:

- It cannot authorize routing.
- It must be independent from the proposer source.
- It must use a separate run id.
- It must use `clause_role_verifier_authority_effect=consistency_evidence_only`.
- It must verify every clause.
- It must agree with proposed roles, or the validator fails closed.
- The role-disagreement policy must be `fail_closed`.

The deterministic validator remains the only route authority.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added verifier authority constants.
- Added contract-level verifier metadata fields.
- Added per-clause verified role fields.
- Added independent clause-role verification validation.
- Added source/run independence checks.
- Added per-clause verification status/confidence checks.
- Added proposer/verifier agreement checks.
- Added fail-closed behavior for missing verifier, partial verifier, low-confidence verifier, unverified clauses, same-source verifier, same-run verifier, wrong authority effect, and role disagreement.
- Preserved the empty validator-owned mechanical command registry.
- Preserved lexical restrict-only behavior.
- Preserved semantic restrict-only behavior.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Added coverage for forged multi-clause unsafe prompts labelled factual.
- Added verifier disagreement coverage.
- Added action/legal/single-clause forged factual failures.
- Added safe factual without verifier failures.
- Added same-source and same-run verifier failures.
- Added low-confidence, partial, unverified-clause, and non-fail-closed policy failures.
- Added incomplete proposal, unresolved residual, unresolved reference, semantic safe/unsafe behavior.
- Added verified safe multi-clause factual success.
- Added strict-safe mechanical registry empty failure.
- Added trace redaction and verifier metadata proof.

## Verification

- V1-IB contract validator tests: PASS, `27 passed`
- Python compile for touched contract/test: PASS
- Guardrail: PASS
- Fake-Frappe `service.py` import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Runtime raw append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- `git diff --check`: PASS
- `git diff --cached --check`: PASS
- Report diff/check: PASS
- Excluded/artifact status scan: clean
- Staged files: `0`

## Decision

`v1_ib_a_g_independent_clause_role_verification_guard_ready_for_counterpart_qa_review`
