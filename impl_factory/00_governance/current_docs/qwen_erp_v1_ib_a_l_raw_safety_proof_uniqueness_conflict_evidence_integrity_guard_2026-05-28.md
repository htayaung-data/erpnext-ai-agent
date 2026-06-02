# V1-IB-A-L Raw Safety Proof Uniqueness / Conflict / Evidence Integrity Guard

Date: 2026-05-28

Decision target: `v1_ib_a_l_raw_safety_proof_uniqueness_conflict_evidence_integrity_guard_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-L is a pure contract/validator proof-integrity hardening slice. It addresses the rejected V1-IB-A-K gap where a validator-owned raw-message proof registry could authorize an unsafe mixed prompt if a signed proof simply claimed the message was safe, and where first-match registry selection made the route decision order-dependent.

No runtime routing, `service.py`, `authorized_emission.py`, visible-context runtime, report-routing runtime, model endpoint, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

Raw-message safety proof authority is now unique, subject-bound, evidence-backed, attested, and order-independent.

The validator no longer accepts the first matching proof for a raw message. It collects all approved validator-owned proof entries matching the raw and normalized message hashes, then fails closed unless exactly one matching proof exists. Any duplicate or conflicting proof for the same subject blocks report routing.

A valid proof must include:

- `safety_proof_id`
- `safety_proof_subject_hash`
- raw and normalized message hashes
- validator safety analyzer id and version
- raw-message safety, clause coverage, secondary-intent, mixed-intent, residual, and reference statuses
- evidence hashes for safety, clause boundary, secondary intent, residual, and reference proof
- safe route authority
- non-derivative proof basis
- canonical proof payload hash
- analyzer-owned attestation
- trace redaction status

Status strings such as `raw_message_safety_status=safe` are not sufficient. They must be backed by non-empty evidence hashes included in the canonical proof hash and covered by the analyzer-owned attestation.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added `safety_proof_id` and `safety_proof_subject_hash` to the raw-message safety proof contract.
- Added proof uniqueness, conflict, and evidence status fields to the emitted contract payload.
- Added canonical proof payload coverage for evidence hashes.
- Added validator-owned subject hash generation from raw and normalized message hashes.
- Replaced first-match proof selection with all-match collection and fail-closed duplicate/conflict handling.
- Required registry key equality with `safety_proof_id`.
- Required `safety_proof_id` to match the canonical proof payload hash.
- Required `safety_proof_subject_hash` to match the validator-computed raw/normalized subject hash.
- Required all evidence hash fields to be present and non-empty before route authority can pass.
- Preserved verifier agreement as `consistency_evidence_only`, semantic backstop as `restrict_only`, and lexical evidence as `restrict_only`.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Updated test proof fixtures to generate subject hashes, evidence hashes, canonical proof ids, and analyzer attestations.
- Proved zero matching proof fails closed.
- Proved exactly one valid proof may pass for a safe factual prompt.
- Proved duplicate safe proofs fail closed.
- Proved safe/unsafe conflicting proofs fail closed.
- Proved unsafe-first and safe-first registry insertion orders both fail closed.
- Proved registry insertion order cannot change the route outcome.
- Proved registry-key mismatch, missing proof id, missing subject hash, missing evidence hashes, empty evidence hashes, and evidence mutation after attestation all fail closed.
- Proved status-only safe proof and signed false-safe proof without evidence fail closed.
- Preserved caller-supplied registry blocking, clause-payload-derived proof blocking, semantic restriction, lexical restriction, and verifier consistency-only behavior.
- Proved trace output records proof uniqueness/conflict/evidence status without raw business text.

## Verification

Local pre-sync verification:

- V1-IB contract validator tests: PASS, `56 passed`
- Python compile for touched contract/test: PASS

Remote verification:

- V1-IB contract validator tests: PASS, `56 passed`
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

`v1_ib_a_l_raw_safety_proof_uniqueness_conflict_evidence_integrity_guard_ready_for_counterpart_qa_review`
