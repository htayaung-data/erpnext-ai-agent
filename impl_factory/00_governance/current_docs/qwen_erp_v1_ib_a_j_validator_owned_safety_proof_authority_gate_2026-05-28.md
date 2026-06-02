# V1-IB-A-J Validator-Owned Safety Proof Authority Gate

Date: 2026-05-28

Decision target: `v1_ib_a_j_validator_owned_safety_proof_authority_gate_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-J is a pure contract/validator authority hardening slice. It addresses the rejected V1-IB-A-I gap where a trusted, attested verifier could still agree with proposer clause roles and thereby authorize unsafe mixed natural-language prompts.

No runtime routing, `service.py`, `authorized_emission.py`, visible-context runtime, report-routing runtime, final-emission runtime, model endpoint, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

Verifier agreement is now consistency evidence only. It cannot grant governed ERP report routing, context reuse, model reasoning, final emission, or `required_answer_mode=governed_erp_answer`.

Governed ERP report routing now requires a separate validator-owned safety proof gate. The default production safety proof registry remains empty. Tests inject a local test-only validator-owned proof fixture to prove the positive path without letting proposer, verifier, semantic, or lexical evidence authorize routing.

The validator-owned safety proof gate requires:

- contract schema and proposer metadata are valid
- trusted verifier provenance is valid
- all clause spans cover the normalized message
- no unresolved residual text
- connectors are accounted for
- pronouns/references are resolved
- semantic backstop is not unsafe or ambiguous
- lexical conservative alarm is absent
- no mixed intent
- no unsafe clause type
- no decision, advice, business-action, policy-boundary, unsafe-domain, or ambiguous flags
- every clause is a pure factual lookup clause
- exact validator-owned safety proof id exists in validator-owned registry

If the validator-owned proof is missing or fails, the contract fails closed with report routing, context reuse, model reasoning, and final emission blocked.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added `validator_owned_safety_proof` contract fields and route-authority status fields.
- Added explicit authority-effect fields:
  - role verification: `consistency_evidence_only`
  - semantic backstop: `restrict_only`
  - lexical evidence: `restrict_only`
- Added empty validator-owned safety proof registry.
- Added redaction-safe validator-owned safety proof id generation over normalized-message hash, clause structure, target hashes, and reference structure.
- Added `_validate_validator_owned_safety_proof`.
- Required validator-owned safety proof success before governed ERP routing.
- Preserved trusted verifier provenance as a prerequisite, not route authority.
- Preserved lexical restrict-only and semantic restrict-only behavior.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Added test-only validator-owned safety proof registry fixture.
- Proved trusted, attested verifier agreement alone cannot authorize report routing.
- Proved the required adversarial mixed prompts fail even when proposer and trusted verifier agree they are factual.
- Proved safe single-clause and multi-clause factual prompts fail without validator-owned safety proof.
- Proved safe factual prompts may pass only with validator-owned safety proof plus all normal invariants.
- Proved semantic safe cannot replace validator-owned safety proof.
- Proved lexical alarm, semantic unsafe/ambiguous, residual text, unresolved references, verifier disagreement, and unsafe verified clauses still fail closed.
- Proved model reasoning and final emission remain blocked whenever safety proof is missing or failed.
- Proved trace payload records verifier provenance, role-verification authority effect, safety proof status, route-authority status, and no raw business text.

## Verification

Remote verification:

- V1-IB contract validator tests: PASS, `38 passed`
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

`v1_ib_a_j_validator_owned_safety_proof_authority_gate_ready_for_counterpart_qa_review`
