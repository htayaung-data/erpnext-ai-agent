# V1-IB-A-F Non-Self-Attestable Mechanical Authority Guard

Date: 2026-05-28

Decision target: `v1_ib_a_f_non_self_attestable_mechanical_authority_guard_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-F is a pure contract/validator hardening slice. It addresses the rejected V1-IB-A-E authority gap where proposal-supplied metadata could self-attest mechanical authority and allow a full-span factual clause over normal natural language.

No runtime routing, visible-context wiring, final-emission wiring, browser/API UAT, deployment, strict enforcement, staging, commit, push, or V2 work was performed.

## Authority Correction

Authority fields are now validator-owned, not proposer-owned.

The validator records proposer claims such as:

- `full_span_factual_authority`
- `full_span_factual_allow_reason`
- `natural_language_interpretation_required`
- completeness/audit status fields

But those claims cannot authorize full-span factual report routing. Full-span factual natural-language clauses now require a validator-owned mechanical command registry entry. The registry is code-owned and is currently empty, so normal user wording cannot enter report routing through the strict mechanical path.

## Implementation Summary

Updated `intent_boundary_contract.py`:

- Added `VALIDATOR_OWNED_MECHANICAL_COMMAND_REGISTRY`, currently empty.
- Added validator-owned mechanical authority trace fields:
  - `validator_owned_mechanical_authority_status`
  - `validator_owned_mechanical_command_id`
- Added validator-owned mechanical command lookup.
- Made full-span factual clauses fail closed unless the validator-owned registry approves the command ID.
- Made proposer-claimed `mechanical_only`, `preapproved_mechanical_command`, and `natural_language_interpretation_required=false` fail closed when not validator-owned.
- Made strict deterministic safe subset reject proof-supplied registry approval when the command is not validator-owned.
- Preserved segmented trusted structured proposal path.
- Preserved semantic and lexical restrict-only behavior.

Updated `test_v1_ib_intent_boundary_contract_validator.py`:

- Added forged full-span mechanical factual mixed prompt failure.
- Added forged strict-safe proof with proof-supplied registry approval failure.
- Added safe full-span natural-language factual default failure.
- Preserved segmented safe factual success.
- Preserved explicit mixed proposal blocking.
- Preserved omitted residual blocking.
- Preserved missing completeness metadata blocking.
- Preserved regex/keyword/pattern source blocking.
- Preserved lexical alarm restriction.
- Preserved semantic safe non-authorization and semantic unsafe/ambiguous restriction.
- Added trace proof for validator-owned mechanical authority fields and redaction safety.

## Verification

- V1-IB contract validator tests: PASS, `15 passed`
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

`v1_ib_a_f_non_self_attestable_mechanical_authority_guard_ready_for_counterpart_qa_review`
