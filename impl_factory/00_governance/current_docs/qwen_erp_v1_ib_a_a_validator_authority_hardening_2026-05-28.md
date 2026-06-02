# V1-IB-A-A Validator Authority Hardening

Date: 2026-05-28

Decision target: `v1_ib_a_a_validator_authority_hardening_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-A is a narrow pure validator hardening slice. It fixes the authority-validation gap found after V1-IB-A review.

No runtime routing, visible-context wiring, final-emission change, model endpoint change, browser/API UAT, staging, commit, push, deployment, strict enforcement, or V2 work was performed.

## Rejection Background

V1-IB-A correctly introduced a contract-first validator, but review found two P0 gaps:

- a lightweight model could cover the entire unsafe message as one factual clause and the validator would accept it
- a strict deterministic safe-subset proof could be forged by setting all self-attested booleans to safe

Both gaps violated the V1-IB-0-C proposal-completeness requirement. Span coverage alone is not enough. Covered spans also need semantic compatibility with their proposed clause type.

## Implemented Fix

The validator now includes an independent raw-message unsafe-evidence model used only to restrict routing.

It checks:

- second-intent connectors
- decision/advice markers
- ontology/domain evidence

This evidence does not authorize report routing. It can only block a false-safe proposal or false strict-safe proof.

## Factual Clause Compatibility

Factual clauses are now checked for hidden unsafe evidence inside the covered span.

If a full-span factual clause contains decision/advice/action/domain evidence, validation fails closed with:

- `factual_clause_contains_unrepresented_unsafe_evidence`

This directly blocks the probe:

- `Show item sales for EC7H-ITEM-A and tell me whether to discount it`

when proposed as one full-span factual clause.

## Strict Safe-Subset Hardening

Strict deterministic safe-subset proof no longer accepts self-attested booleans alone.

It now also requires:

- independent raw-message safety status
- deterministic raw-message validator authority source
- no unsafe evidence detected in the normalized raw message

Forged proof over an unsafe raw message fails closed with:

- `strict_safe_subset_raw_message_unsafe_evidence`

Self-attested proof without independent raw safety fails closed with:

- `strict_safe_subset_missing_independent_raw_safety`

## Tests Added

Pure tests now cover:

- full-span factual clause hiding an unsafe pricing decision fails closed
- forged strict deterministic safe subset for unsafe raw message fails closed
- strict deterministic safe subset without independent raw safety authority fails closed
- legitimate strict deterministic safe subset still passes only when independent raw safety fields are present

## Verification

Verification completed on `/tmp/erpai_pr5_postmerge_verify`.

- V1-IB-A/A-A pure tests: PASS, `15 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Runtime raw append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- Diff/check: PASS
- Excluded/artifact scan: clean
- Staged files: `0`

## Decision

`v1_ib_a_a_validator_authority_hardening_ready_for_counterpart_qa_review`
