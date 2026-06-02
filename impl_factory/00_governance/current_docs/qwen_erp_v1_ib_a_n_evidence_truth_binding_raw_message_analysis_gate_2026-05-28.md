# V1-IB-A-N Evidence Truth Binding / Validator-Owned Raw-Message Analysis Gate

Date: 2026-05-28

Decision target: `v1_ib_a_n_evidence_truth_binding_raw_message_analysis_gate_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-N is a pure contract/validator authority hardening slice. It addresses the rejected V1-IB-A-M gap where structured, signed, redaction-safe evidence objects could still assert safe conclusions without an independent validator-owned raw-message analysis supporting those conclusions.

No runtime routing, `service.py`, `authorized_emission.py`, visible-context runtime, report-routing runtime, model endpoint, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

A signed safe proof can no longer authorize governed ERP routing unless a separate validator-owned raw-message analysis entry independently supports every safe evidence conclusion.

The new analysis gate is separate from:

- proposer clause roles
- verifier clause roles
- semantic-safe output
- lexical phrase authority
- proof assertions

The validator now requires:

- raw-message analysis exists in validator-owned module state
- analysis raw/normalized subject matches the proof subject
- analysis status is safe, not unsafe, ambiguous, unknown, or inconclusive
- analysis statuses match proof-level conclusions
- analysis covers connector, secondary-intent, mixed-intent, residual, reference, and unsafe/ambiguity conclusions
- analysis evidence hashes match the proof evidence hashes
- analysis is non-derived
- analysis is redaction-safe

If analysis is missing, weak, contradictory, derived, inconclusive, or evidence-mismatched, the validator fails closed.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added validator-owned raw-message analysis registry, empty by default for production.
- Added raw-message analysis contract fields and trace fields.
- Added analysis validation against proof subject hashes, proof statuses, and proof evidence hashes.
- Added fail-closed checks for missing analysis, missing fields, subject mismatch, unsafe/ambiguous/unknown analysis status, status contradictions, connector/residual/reference contradictions, evidence hash mismatch, derivation from non-authority sources, and unsafe redaction.
- Updated the route-authority path so proof evidence semantics are not sufficient without matching validator-owned analysis.
- Changed `detect_raw_message_unsafe_evidence()` from a permissive stub to a conservative restrict-only alarm that never grants authority.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Added test-only raw-message analysis fixtures in validator-owned module state.
- Proved signed false-safe proof with no raw-message analysis fails.
- Proved missing analysis subject hash and subject mismatch fail.
- Proved unsafe, ambiguous, and unknown analysis statuses fail.
- Proved secondary-intent, mixed-intent, connector, residual, and reference contradictions fail.
- Proved analysis derived from proposer roles, verifier roles, semantic-safe output, or lexical phrase authority fails.
- Proved analysis evidence hash mismatch fails.
- Proved safe factual prompt may pass only with matching validator-owned raw-message analysis and proof evidence.
- Proved the required unsafe probes fail even when proof evidence claims safe.
- Proved the raw-message unsafe-evidence detector is conservative and restrict-only, not permissive authority.
- Preserved semantic unsafe restriction, lexical alarm restriction, trusted verifier consistency-only behavior, and redaction-safe trace behavior.

## Verification

Local pre-sync verification:

- V1-IB contract validator tests: PASS, `72 passed`
- Python compile for touched contract/test: PASS

Remote verification:

- V1-IB contract validator tests: PASS, `72 passed`
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

`v1_ib_a_n_evidence_truth_binding_raw_message_analysis_gate_ready_for_counterpart_qa_review`
