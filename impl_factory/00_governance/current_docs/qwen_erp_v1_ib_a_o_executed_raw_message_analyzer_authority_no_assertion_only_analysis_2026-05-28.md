# V1-IB-A-O Executed Raw-Message Analyzer Authority / No Assertion-Only Analysis

Date: 2026-05-28

Decision target: `v1_ib_a_o_executed_raw_message_analyzer_authority_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-O is a pure contract/validator execution-authority hardening slice. It addresses the rejected V1-IB-A-N gap where proof, evidence, and analysis registry entries could all assert safe conclusions without proving the raw-message analyzer was actually executed.

No runtime routing, `service.py`, `authorized_emission.py`, visible-context runtime, report-routing runtime, model endpoint, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

Governed ERP routing can no longer be authorized by hand-written proof, evidence, or analysis registry entries alone. The validator now requires a validator-owned executed analyzer record.

The execution record must include:

- raw and normalized message hashes
- analyzer id and approved analyzer version
- run id
- input hash
- output hash
- artifact hash
- execution source and version
- execution mode and completed status
- replay verification status
- redaction-safe trace status
- canonical execution payload hash
- analyzer-owned attestation

The validator recomputes:

- input hash from raw hash, normalized hash, and subject hash
- output hash from the raw-message analysis object
- canonical execution payload hash
- analyzer attestation over the canonical execution payload hash

If execution proof is missing, incomplete, forged, mismatched, not replay-verified, not redaction-safe, or not from an approved analyzer/version, report routing fails closed.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added empty validator-owned raw-message analysis execution registry.
- Added execution contract fields, canonical execution hashing, and attestation helpers.
- Added trace-safe execution metadata to the contract payload.
- Added execution validation linked to the raw-message analysis object.
- Required execution source to be validator-owned.
- Required execution status to be `completed` and replay status to be `verified`.
- Required execution input hash to match the raw/normalized message subject.
- Required execution output hash to match the exact analysis object.
- Required artifact hash, safe redaction, approved analyzer id/version, canonical payload hash, and valid analyzer attestation.
- Preserved proof/evidence/analysis checks as necessary but not sufficient.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Added test-only executed analyzer proof fixtures.
- Proved analysis registry entry without execution proof fails.
- Proved missing run id, missing input hash, input mismatch, missing output hash, output mismatch, missing artifact hash, invalid attestation, incomplete execution status, non-validator execution source, unapproved analyzer version, unsafe trace redaction, unverified replay, and forged execution mutation all fail.
- Proved signed proof plus safe analysis with no execution proof fails.
- Proved the required unsafe probes fail without valid executed analyzer proof.
- Proved safe factual prompt may pass only with valid executed analyzer proof and all previous proof/evidence/analysis invariants.
- Proved trace output includes execution source, run id, status, replay status, and no raw business text.

## Verification

Local pre-sync verification:

- V1-IB contract validator tests: PASS, `82 passed`
- Python compile for touched contract/test: PASS

Remote verification:

- V1-IB contract validator tests: PASS, `82 passed`
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

`v1_ib_a_o_executed_raw_message_analyzer_authority_ready_for_counterpart_qa_review`
