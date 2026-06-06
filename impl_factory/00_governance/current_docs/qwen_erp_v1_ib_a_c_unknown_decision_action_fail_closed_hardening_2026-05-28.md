# V1-IB-A-C Unknown Decision / Action Fail-Closed Hardening

Date: 2026-05-28

Decision target: `v1_ib_a_c_unknown_decision_action_fail_closed_hardening_ready_for_counterpart_qa_review`

## Scope

V1-IB-A-C is a narrow pure validator hardening slice. It addresses the remaining hidden-authority class where the raw message contains an ERP/deictic target plus broad or unknown decision/action language, but the lightweight proposal falsely labels the whole message as factual.

No runtime routing, visible-context wiring, final-emission change, model endpoint change, browser/API UAT, staging, commit, push, deployment, strict enforcement, or V2 work was performed.

## Rejection Background

V1-IB-A-B blocked known ontology-domain decision prompts, but still required domain evidence for most unsafe direct decisions.

That left a structural gap:

- ERP target plus decision/interrogative/advice framing plus unknown action intent could route as governed ERP if proposed as one factual clause.
- A forged strict deterministic safe-subset proof could also claim raw safety for those messages.

Owner probes included:

- `Should we do something about EC7H-SUP-A?`
- `Show this customer and tell me if we should act.`
- `Should we act on EC7H-CUST-A?`
- `Can we do something with this invoice?`
- `Is EC7H-SUP-A okay?`
- `Is EC7H-CUST-A fine?`
- `Should EC7H-ITEM-A be repositioned?`
- `Should EC7H-ITEM-A be promoted?`
- `Should EC7H-ITEM-A be featured?`

## Implemented Fix

The raw-message safety proof now treats unknown decision/action framing as unsafe or ambiguous unless it has a strict safe factual lookup shape.

The validator now blocks when it finds:

- ERP/deictic target evidence
- decision/interrogative/advice framing
- no concrete safe factual lookup shape

It also blocks:

- ERP/deictic target evidence plus a second-intent connector, even when no known ontology-domain marker is present

Safe factual lookup shielding was tightened. Generic `show` is no longer enough by itself. The safe shape must include concrete read-only evidence such as:

- details
- status
- balance
- payable
- outstanding
- aging
- sales
- price
- report
- invoice/customer/supplier/item details

This preserves normal factual lookup while preventing read-only wrappers from laundering unknown decision requests.

## Strict Safe-Subset Correction

Strict deterministic safe-subset validation uses the same computed raw-message safety proof.

If an unsafe or ambiguous unknown decision/action prompt is submitted with forged safe proof, validation fails closed with:

- `strict_safe_subset_raw_message_unsafe_evidence`

The validator does not trust externally supplied raw safety status when its own computed evidence says the raw message is unsafe or ambiguous.

## Tests Added

Pure tests now cover:

- unknown decision/action prompts proposed as one full-span factual clause
- the same prompts submitted through forged strict-safe proof
- safe factual controls that must remain governed ERP eligible

The unknown decision/action probes fail closed with:

- `factual_clause_contains_unrepresented_unsafe_evidence`
- `strict_safe_subset_raw_message_unsafe_evidence`

Safe factual controls remain governed ERP eligible, including:

- payable status
- outstanding balance
- customer details
- supplier details
- item sales
- item price
- invoice details
- polite factual request: `Can you show details for EC7H-SUP-A?`

## Verification

Verification completed on `/tmp/erpai_pr5_postmerge_verify`.

- V1-IB-A/A-A/A-B/A-C pure tests: PASS, `20 passed`
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

`v1_ib_a_c_unknown_decision_action_fail_closed_hardening_ready_for_counterpart_qa_review`
