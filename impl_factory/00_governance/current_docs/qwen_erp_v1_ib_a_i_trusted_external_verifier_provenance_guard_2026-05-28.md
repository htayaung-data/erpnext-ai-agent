# V1-IB-A-I Trusted External Verifier Provenance Guard

Date: 2026-05-28

Decision target: `v1_ib_a_i_trusted_external_verifier_provenance_guard_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-I is a pure contract/validator provenance hardening slice. It addresses the rejected V1-IB-A-H gap where an external verifier envelope was separate from the proposal, but still caller-supplied and therefore forgeable.

No runtime routing, `service.py`, `authorized_emission.py`, visible-context code, final-emission code, model endpoint call, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

Verifier envelope claims are no longer enough to authorize natural-language ERP report routing. The validator now requires verifier provenance from validator-owned registry state.

The production trusted verifier registry remains empty by default. Tests inject a local test-only registry fixture to prove the positive path without granting production trust.

The validator now enforces:

- verifier source must exist in the validator-owned trusted verifier registry
- verifier prompt version must be approved for that source
- verifier model name must match registry policy
- verifier run id must differ from proposer run id
- verifier source must remain independent from proposer source/model
- canonical verifier payload hash is recomputed by the validator
- supplied verifier payload hash must match the recomputed canonical hash
- verifier attestation must match the registry-owned test secret/key
- verifier authority effect must be `consistency_evidence_only`
- trace redaction status must be `safe`
- clause span/hash/role agreement checks from V1-IB-A-H still apply

If provenance, hash, attestation, independence, trace safety, clause verification, semantic, lexical alarm, residual, or reference checks fail, report routing, context reuse, model reasoning, and final emission remain blocked for invalid contracts.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added empty validator-owned trusted verifier registry.
- Added canonical verifier payload construction excluding caller-supplied hash/attestation fields.
- Added validator-recomputed canonical verifier payload hash.
- Added validator-owned attestation check using registry-owned secret material.
- Added verifier provenance, payload hash, and attestation statuses to the contract payload.
- Required `verifier_attestation` in the external verifier envelope.
- Preserved proposal-carried verifier metadata as non-authoritative.
- Preserved empty validator-owned mechanical command registry.
- Preserved lexical restrict-only and semantic restrict-only behavior.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Added test-only trusted verifier registry fixture.
- Added canonical hash and attestation helpers for test envelopes.
- Proved forged unknown/unregistered verifier envelopes fail.
- Proved fake hash, wrong canonical hash, missing attestation, and wrong attestation fail.
- Proved unapproved prompt version and model name fail.
- Proved same verifier/proposer source or run id still fail.
- Proved fake trusted-looking envelopes fail across the required adversarial probes.
- Proved safe single-clause and multi-clause factual prompts pass only with test-trusted verifier, correct canonical hash, correct attestation, and all invariants.
- Proved unsafe mixed prompts still block when a valid verifier identifies unsafe intent.
- Proved semantic unsafe/ambiguous still restrict and semantic safe cannot authorize missing/untrusted verifier.
- Proved mechanical registry path still fails while the registry is empty.
- Proved trace payload exposes verifier provenance/hash/attestation statuses without raw business text.

## Verification

Remote verification:

- V1-IB contract validator tests: PASS, `33 passed`
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

`v1_ib_a_i_trusted_external_verifier_provenance_guard_ready_for_counterpart_qa_review`
