# V1-IB-A-D Remove Lexical Authority From Intent Boundary Foundation

Date: 2026-05-28

Decision target: `v1_ib_a_d_remove_lexical_authority_foundation_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-D preserves the V1-IB-A contract scaffold while removing lexical/regex/keyword/pattern authority from the intent boundary foundation. This is a pure contract/validator slice only.

No runtime routing, visible-context wiring, final-emission wiring, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Model Update

Lexical evidence is now restrict-only. It cannot grant:

- `report_routing_allowed=true`
- `context_reuse_allowed=true`
- `model_reasoning_allowed=true`
- `final_emission_allowed=true`
- `required_answer_mode=governed_erp_answer`

The only report-eligible authority path in this slice is a trusted structured proposal with:

- `proposal_authority_source=lightweight_model_structured_proposal`
- complete schema
- complete clause span coverage
- no residual text
- no unresolved connector/pronoun/reference
- valid target schemas
- confidence above threshold
- complete proposer status
- valid output status
- safe trace redaction status
- no decision/advice/action/policy flags
- no semantic backstop restriction
- no lexical conservative alarm

Semantic backstop output remains restrict-only. A semantic-safe result cannot authorize a missing or invalid proposal.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added explicit proposal authority-source fields and trace payload fields.
- Added trusted source value: `lightweight_model_structured_proposal`.
- Added strict-safe mechanical authority value: `deterministic_safe_subset_mechanical_validator`.
- Added restrict-only values for semantic backstop and lexical alarms.
- Added forbidden lexical proposer identifiers: `regex_classifier`, `keyword_classifier`, `pattern_classifier`, `handcrafted_lexical_classifier`.
- Required `proposal_authority_source` in proposal schema validation.
- Rejected lexical/pattern/regex/keyword proposer names as report-authority sources.
- Added `lexical_conservative_alarm` handling that fails closed.
- Quarantined raw lexical evidence detection so it returns no authority and no safety proof.
- Removed raw lexical evidence checks from factual clause authorization.
- Redefined strict deterministic safe subset as mechanical-only and rejected self-attested semantic safety proofs unless a pre-approved mechanical command shape is proven.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Replaced lexical-hardening tests with authority-path tests.
- Covered regex/keyword/pattern proposal rejection.
- Covered lexical alarm restriction.
- Covered trusted structured factual proposal authorization.
- Covered trusted structured mixed proposal blocking.
- Covered omitted unsafe clause residual blocking.
- Covered semantic safe non-authorization.
- Covered semantic unsafe/ambiguous restriction.
- Covered forged strict-safe self-attestation rejection.
- Covered trace payload redaction and authority-source exposure.

## Explicit Non-Goals

- No continuation of `intent_boundary_structural_classifier.py`.
- No dependency on the rejected V1-IB-B deterministic structural classifier path.
- No prompt/synonym hardening.
- No runtime behavior change.
- No source edits outside the allowed contract/test files.

## Verification

- V1-IB contract validator tests: PASS, `11 passed`
- Python compile for touched contract/test: PASS
- Guardrail: PASS
- Fake-Frappe `service.py` import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Runtime raw append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- `git diff --check`: PASS
- `git diff --cached --check`: PASS
- Staged files: `0`

## Boundary Notes

Existing dirty artifacts from prior rejected/accepted V1-R and V1-IB slices remain outside the V1-IB-A-D scope. This slice did not stage or package any file.

The approved V1 browser UAT manifest JSON remains the only known approved JSON artifact candidate in the broader dirty tree; V1-IB-A-D itself did not create JSON/YAML data artifacts.

## Decision

`v1_ib_a_d_remove_lexical_authority_foundation_ready_for_counterpart_qa_review`
