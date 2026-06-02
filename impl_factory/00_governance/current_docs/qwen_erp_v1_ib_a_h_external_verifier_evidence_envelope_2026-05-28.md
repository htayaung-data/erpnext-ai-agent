# V1-IB-A-H External Verifier Evidence Envelope

Date: 2026-05-28

Decision target: `v1_ib_a_h_external_verifier_evidence_envelope_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-H is a pure contract/validator hardening slice. It addresses the rejected V1-IB-A-G gap where verifier agreement metadata was embedded in the proposer payload and could therefore be forged by the proposer.

No runtime routing, visible-context wiring, final-emission wiring, model endpoint call, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

Proposal-carried verifier fields are now audit-only. Natural-language report routing requires a separate external verifier envelope supplied to the validator.

The validator now enforces:

- no external verifier envelope means no natural-language report routing
- proposal-embedded verifier status cannot authorize routing
- verifier envelope raw and normalized message hashes must match
- verifier source must be independent from proposer source/model
- verifier run id must differ from proposer run id
- verifier status must be `passed`
- verifier independence status must be `independent`
- verifier authority effect must be `consistency_evidence_only`
- verifier trace redaction status must be `safe`
- every proposal clause must have exactly one verified matching clause
- verified span and normalized clause hash must match the proposal clause
- verifier/proposer role disagreement fails closed
- low-confidence or partial verifier output fails closed

The deterministic validator remains the only route authority. The verifier envelope is consistency evidence only.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added external verifier envelope schema requirements.
- Added verified-clause envelope schema requirements.
- Added `verifier_envelope` keyword input to `validate_intent_boundary_contract`.
- Moved clause-role authority checks from proposal metadata to external verifier envelope validation.
- Preserved proposal-carried verifier fields as non-authoritative/audit-only.
- Added verifier envelope hash, span, role, confidence, trace, and independence checks.
- Enriched redaction-safe clause payloads with verified role metadata from the external envelope only.
- Preserved empty validator-owned mechanical registry.
- Preserved lexical restrict-only and semantic restrict-only behavior.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Added forged proposer-embedded verifier failure.
- Added mixed unsafe prompt forged as factual without external envelope failure.
- Added embedded passed-verifier failure.
- Added verifier hash mismatch, same source, same run id, partial clause map, role disagreement, and low confidence failures.
- Added residual and unresolved-reference failures even with verifier-safe evidence.
- Added semantic unsafe/ambiguous restriction with valid verifier.
- Added semantic safe non-authorization.
- Added safe single-clause and multi-clause factual success with valid external verifier.
- Added mechanical registry empty failure.
- Added model reasoning/final emission blocked when verifier authority fails.
- Added redaction-safe trace/verifier metadata proof.

## Verification

Remote verification:

- V1-IB contract validator tests: PASS, `23 passed`
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

`v1_ib_a_h_external_verifier_evidence_envelope_ready_for_counterpart_qa_review`
