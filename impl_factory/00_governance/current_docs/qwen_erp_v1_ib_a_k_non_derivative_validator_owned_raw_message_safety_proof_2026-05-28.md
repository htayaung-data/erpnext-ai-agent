# V1-IB-A-K Non-Derivative Validator-Owned Raw-Message Safety Proof

Date: 2026-05-28

Decision target: `v1_ib_a_k_non_derivative_validator_owned_raw_message_safety_proof_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-K is a pure contract/validator authority hardening slice. It addresses the rejected V1-IB-A-J gap where the validator-owned safety proof could still be derived from proposer/verifier clause-role labels.

No runtime routing, `service.py`, `authorized_emission.py`, visible-context runtime, report-routing runtime, model endpoint, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

The validator-owned safety proof is no longer accepted from a proof id generated from proposer/verifier clause-role payloads. Role agreement remains consistency evidence only.

Governed ERP report routing now requires a non-derivative raw-message safety proof from validator-owned state. The default production raw-message analyzer registry and safety proof registry remain empty. Tests inject local validator-owned fixture state to prove the positive path without allowing caller-supplied proof registries to authorize routing.

The raw-message safety proof must include:

- raw and normalized message hashes
- validator safety analyzer id and version
- raw-message safety status
- raw-message clause coverage status
- raw-message secondary-intent status
- raw-message mixed-intent status
- raw-message residual status
- raw-message reference status
- safe route authority
- non-derivative proof basis
- proof payload hash
- analyzer-owned attestation
- trace redaction status

The proof fails if it is missing, caller-supplied, derived from clause-role payloads, missing analyzer identity, missing raw-message statuses, missing attestation, semantically restricted, lexically restricted, residual/unresolved, or not backed by a validator-owned analyzer registry entry.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added empty validator-owned raw-message safety analyzer registry.
- Added raw-message safety proof schema and canonical hash/attestation helpers.
- Added redaction-safe raw-message proof trace fields to the contract payload.
- Changed safety proof lookup to validator-owned module state, not caller-supplied registry authority.
- Rejected caller-supplied safety proof registries.
- Required non-derivative proof basis: `non_derivative_raw_message_safety_analysis`.
- Required analyzer registry approval and analyzer-owned attestation.
- Preserved proposer labels, verifier agreement, semantic backstop, and lexical alarms as non-authorizing evidence.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Added test-only raw-message safety analyzer and proof fixtures.
- Proved forged factual clauses plus trusted verifier plus clause-derived proof registry fail.
- Proved all three required adversarial prompts fail when proof registry is generated from forged clause payload.
- Proved clause-role-derived proof basis fails.
- Proved missing raw-message analyzer identity/statuses/residual/mixed/secondary/attestation fields fail.
- Proved route authority without raw-message evidence fails.
- Proved safe factual prompt without raw-message proof fails.
- Proved safe factual prompt may pass only with non-derivative raw-message safety proof and all normal invariants.
- Proved semantic safe cannot replace proof, semantic unsafe restricts, lexical alarm restricts, and model reasoning/final emission remain blocked when proof is missing or failed.
- Proved trace output records safety proof source/status without raw business text.

## Verification

Remote verification:

- V1-IB contract validator tests: PASS, `43 passed`
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

`v1_ib_a_k_non_derivative_validator_owned_raw_message_safety_proof_ready_for_counterpart_qa_review`
