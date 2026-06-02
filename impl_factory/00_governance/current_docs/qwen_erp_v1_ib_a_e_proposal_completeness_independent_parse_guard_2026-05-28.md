# V1-IB-A-E Proposal Completeness And Independent Parse Guard

Date: 2026-05-28

Decision target: `v1_ib_a_e_proposal_completeness_independent_parse_guard_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-E is a pure contract/validator hardening slice. It addresses the rejected V1-IB-A-D authority gap where a trusted proposer could self-attest a full-span mixed unsafe natural-language request as one factual clause and receive governed ERP report authority.

No runtime routing, visible-context wiring, final-emission wiring, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

A proposal remains evidence, not authority by itself. The validator now requires explicit proposal-completeness and independent parse-guard metadata before report routing can be authorized.

Report routing can be allowed only when all of the following pass:

- trusted proposal authority source
- complete proposer status
- confidence threshold
- complete clause span coverage
- no unresolved residual text
- no unresolved references
- no mixed intent
- no unsafe/action/advice/policy clause
- no semantic backstop restriction
- no lexical conservative alarm
- `proposal_completeness_status=complete`
- `clause_segmentation_status=passed`
- `secondary_intent_audit_status=passed`
- `residual_audit_status=passed`
- `clause_role_confidence_status=passed`
- `independent_parse_guard_status=passed`

Full-span factual clauses are no longer accepted as normal natural-language shortcuts. A full-span factual clause requires mechanical-only authority and an approved mechanical reason; otherwise it fails closed. Safe natural-language factual requests must provide segmented proposal coverage and the required completeness metadata.

## Strict Safe Subset Update

The strict deterministic safe subset remains mechanical-only. It now rejects proofs that lack:

- `mechanical_command_id`
- `mechanical_command_registry_status=approved`
- `natural_language_interpretation_required=false`
- `intent_interpretation_required=false`

This prevents ordinary natural-language ERP questions from being authorized by self-attested strict-safe proof objects.

## Tests Added

The validator tests now prove:

- trusted full-span false factual mixed prompt fails
- trusted full-span false factual generic action prompt fails
- omitted unsafe residual still fails
- explicit mixed proposal blocks cleanly
- safe factual proposal can pass only with completeness metadata
- safe factual proposal without completeness metadata fails
- strict-safe proof over mixed natural language fails
- strict-safe proof over ordinary natural language fails without mechanical registry fields
- regex/keyword/pattern proposer source cannot authorize
- lexical alarm restricts
- semantic safe cannot authorize invalid or missing proposal
- semantic unsafe/ambiguous restricts otherwise valid proposal
- trace payload includes completeness/authority fields and no raw business text

## Explicit Non-Goals

- No continuation of `intent_boundary_structural_classifier.py`.
- No keyword, regex, synonym, or phrase-list authority.
- No source edits outside the allowed contract/test files.
- No runtime behavior changes.

## Verification

- V1-IB contract validator tests: PASS, `14 passed`
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

`v1_ib_a_e_proposal_completeness_independent_parse_guard_ready_for_counterpart_qa_review`
