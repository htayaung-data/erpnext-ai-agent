# V1-IB-A-B Raw Message Safety Proof Hardening

Date: 2026-05-28

Decision target: `v1_ib_a_b_raw_message_safety_proof_hardening_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-B is a narrow pure validator hardening slice. It responds to the remaining hidden-authority false-allow class found after V1-IB-A-A.

No runtime routing, visible-context wiring, final-emission change, model endpoint change, browser/API UAT, staging, commit, push, deployment, strict enforcement, or V2 work was performed.

## Rejection Background

V1-IB-A-A blocked the first full-span factual laundering probe, but its raw evidence detector was still too narrow. It only blocked second-intent connectors or a simple decision-marker plus known-domain-marker shape.

That allowed direct decision/advice/action prompts to be hidden inside a single full-span factual clause when the lightweight proposal mislabeled the whole message as factual.

Owner probes included:

- `Is EC7H-ITEM-A overpriced?`
- `Is EC7H-ITEM-A worth stocking?`
- `Should EC7H-SUP-A be our supplier?`
- `Can EC7H-CUST-A be added to customer list?`
- `Is this invoice okay to leave out?`
- `Would EC7H-CUST-A be good to keep?`

The same class also affected forged strict deterministic safe-subset proof when that proof claimed external raw safety.

## Implemented Fix

The raw-message safety detector was replaced with a structural unsafe-evidence proof model.

The detector now evaluates:

- ERP target evidence, including EC7H IDs, this/that entity references, and governed ERP entity nouns
- decision/interrogative/advice framing
- domain evidence grouped by ontology domain
- second-intent connectors
- safe factual lookup markers as non-authorizing context

The structural rule is conservative:

- ERP target plus decision framing plus unsafe domain evidence blocks report authority
- connector plus unsafe domain evidence blocks report authority
- high-risk policy/control domains with decision framing block report authority
- safe factual lookup wording remains allowed only when unsafe domain evidence is absent

This evidence can only restrict routing. It cannot authorize report routing.

## Strict Safe-Subset Correction

Strict deterministic safe-subset validation now depends on the validator's computed raw-message safety evidence, not on externally supplied safe-status claims.

If the raw message contains structural unsafe evidence, strict safe-subset proof fails closed with:

- `strict_safe_subset_raw_message_unsafe_evidence`

This is true even when the proof claims:

- `independent_raw_message_safety_status = safe`
- `safe_subset_authority_source = deterministic_raw_message_validator`

## Tests Added

Pure tests now cover:

- direct unsafe decision prompts falsely proposed as one full-span factual clause
- forged strict-safe proof over those same direct unsafe prompts
- safe factual ID lookups that must remain report-routable

The direct unsafe probes fail closed with:

- `factual_clause_contains_unrepresented_unsafe_evidence`
- `strict_safe_subset_raw_message_unsafe_evidence`

Safe factual controls remain governed ERP eligible:

- payable status
- outstanding balance
- customer details
- supplier details
- item sales
- item price
- invoice details

## Verification

Verification completed on `/tmp/erpai_pr5_postmerge_verify`.

- V1-IB-A/A-A/A-B pure tests: PASS, `18 passed`
- Direct owner false-allow probes: PASS, all block in full-span factual and forged strict-safe paths
- Safe factual lookup controls: PASS, all remain `governed_erp_answer`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: `0 / 1 / 27`
- Runtime raw append scan: only `authorized_emission.py:271` and `authorized_emission.py:327`
- Diff/check: PASS
- Excluded/artifact scan: clean
- Staged files: `0`

## Decision

`v1_ib_a_b_raw_message_safety_proof_hardening_ready_for_counterpart_qa_review`
