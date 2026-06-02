# V1-IB-A-M Raw-Message Safety Analyzer Contract / Evidence Semantics

Date: 2026-05-28

Decision target: `v1_ib_a_m_raw_message_safety_analyzer_contract_evidence_semantics_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-M is a pure contract/validator evidence-semantics hardening slice. It addresses the conditional V1-IB-A-L gap where proof objects were unique, evidence-backed, and attested, but a single signed proof could still claim safe conclusions without structured evidence semantics supporting those conclusions.

No runtime routing, `service.py`, `authorized_emission.py`, visible-context runtime, report-routing runtime, model endpoint, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

A raw-message safety proof can no longer pass route authority using status strings and hashes alone. The proof must include structured, redaction-safe evidence objects whose semantics support every safe conclusion.

Required evidence objects:

- `raw_message_clause_coverage_evidence`
- `raw_message_secondary_intent_evidence`
- `raw_message_mixed_intent_evidence`
- `raw_message_residual_evidence`
- `raw_message_connector_evidence`
- `raw_message_reference_evidence`
- `raw_message_unsafe_ambiguity_evidence`

Each object must include:

- evidence id, type, status, basis, and canonical evidence hash
- source analyzer id and version
- non-derivation flags for proposer roles, verifier roles, semantic-safe output, and lexical phrase authority
- redaction status
- blocking reason

Safe proof conclusions must be backed by matching evidence semantics:

- clause coverage evidence: `complete`
- secondary intent evidence: `none`
- mixed intent evidence: `none`
- residual evidence: `clear`
- connector evidence: `accounted`
- reference evidence: `resolved_or_not_required`
- unsafe/ambiguity evidence: `none`

If any evidence object is missing, malformed, contradictory, unsupported, unknown, ambiguous, unsafe, label-derived, semantic-safe-derived, lexical-authority-derived, or not redaction-safe, the validator fails closed.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added required raw-message safety evidence object schema.
- Added canonical evidence hashing and proof-level canonical coverage for evidence objects.
- Added evidence semantics validation before route authority can pass.
- Required evidence status to match the corresponding proof-level conclusion where applicable.
- Required evidence source analyzer id/version to match the proof analyzer.
- Required evidence basis to remain non-derivative raw-message safety analysis.
- Rejected evidence derived from proposer roles, verifier roles, semantic-safe output, or lexical phrase authority.
- Rejected unsafe redaction status and raw business text in evidence object fields.
- Added redaction-safe evidence semantics status to the contract payload.
- Preserved verifier agreement as `consistency_evidence_only`, semantic backstop as `restrict_only`, and lexical evidence as `restrict_only`.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Extended raw-message safety proof fixtures to include structured evidence objects.
- Proved signed false-safe proof with missing evidence objects fails.
- Proved signed false-safe proof with status-only evidence hashes fails.
- Proved unsupported, unknown, and contradictory evidence statuses fail.
- Proved secondary-intent and mixed-intent evidence contradictions fail.
- Proved connector, residual, and reference unresolved evidence fail.
- Proved evidence derived from proposer roles, verifier roles, semantic-safe output, or lexical phrase authority fails.
- Proved evidence with unsafe redaction status or raw business text fails.
- Proved safe factual prompt may pass only with complete, redaction-safe, non-derived, internally consistent evidence semantics.
- Preserved semantic unsafe restriction, lexical alarm restriction, trusted verifier consistency-only behavior, and redaction-safe trace behavior.

## Verification

Local pre-sync verification:

- V1-IB contract validator tests: PASS, `63 passed`
- Python compile for touched contract/test: PASS

Remote verification:

- V1-IB contract validator tests: PASS, `63 passed`
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

`v1_ib_a_m_raw_message_safety_analyzer_contract_evidence_semantics_ready_for_counterpart_qa_review`
