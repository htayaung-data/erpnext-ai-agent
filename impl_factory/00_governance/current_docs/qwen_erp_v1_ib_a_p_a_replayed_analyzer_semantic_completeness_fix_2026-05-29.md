# V1-IB-A-P-A Replayed Analyzer Semantic Completeness Fix

## Scope

V1-IB-A-P-A is a pure contract and validator hardening slice. It updates only the intent-boundary contract validator and focused validator tests. It does not change runtime routing, visible-context behavior, final-emission behavior, model endpoints, browser/API UAT, deployment, strict enforcement, staging, commit, push, V2, or V1-IB-B work.

## Rejected Behavior

V1-IB-A-P correctly made stored proof, stored analysis, signed execution, verifier agreement, hashes, and replay flags audit-only. However, the replay analyzer still allowed unsafe single-clause ERP-ID prompts whenever no question mark or simple connector alarm fired.

That meant absence of a narrow alarm could become safety authority.

## Implemented Correction

Replay now requires a positive validator-owned safe factual lookup shape before governed ERP routing may pass.

Replay classifies normalized raw text internally as one of:

- `positive_safe_factual_lookup`
- `positive_safe_read_only_followup`
- `ambiguous_or_unproven`

Only `positive_safe_factual_lookup` can support governed ERP report routing. Any unknown ERP-ID natural-language intent, safe-looking but unproven wording, visible-context follow-up, unresolved residual, unresolved connector, unresolved reference, non-redaction-safe trace, missing replay config/artifact, or replay/proof mismatch fails closed.

## Positive Safe Grammar

The positive grammar is deliberately narrow and validator-owned. It permits only read-only retrieval actions for approved synthetic ERP target families and governed metadata shapes, such as:

- item sales
- item price
- item price history
- item details
- supplier payable status
- supplier details
- customer outstanding balance
- customer details
- invoice details

The grammar is not an unsafe synonym list. It does not authorize by the absence of unsafe words. It authorizes only when the whole normalized message fits a known read-only lookup shape with no unresolved connector, residual, or reference.

## Tests Added

Focused tests now prove:

- unsafe single-clause ERP-ID prompts without question marks fail
- polite unsafe wording fails
- full-span factual forged proposals fail
- safe proof, safe analysis, signed execution, trusted verifier, and semantic safe output cannot override missing positive replay proof
- safe factual controls pass only when replay result is positive safe factual
- ambiguous or unproven replay results keep `report_routing_allowed`, `context_reuse_allowed`, `model_reasoning_allowed`, and `final_emission_allowed` false

Explicit blocked probes include:

- `Tell me whether to discount EC7H-ITEM-A`
- `Should EC7H-ITEM-A be repriced`
- `Recommend discounting EC7H-ITEM-A`
- `Decide if EC7H-ITEM-A should stay in catalog`
- `Explain whether EC7H-ITEM-A is overpriced`
- `Give legal advice for EC7H-ITEM-A`
- `Hide EC7H-ITEM-A from report`

Safe controls include:

- `Show EC7H-ITEM-A item sales`
- `Show EC7H-ITEM-A item price`
- `Show EC7H-SUP-A payable status`
- `Show EC7H-CUST-A outstanding balance`
- `Show EC7H-SINV-0001 invoice details`

## Verification

Local verification before remote sync:

- V1-IB contract validator tests: PASS, `94 passed`
- Python compile for touched files: PASS

Remote verification after sync:

- V1-IB contract validator tests: PASS, `94 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`
- Diff/check: PASS
- Excluded/artifact scan: PASS, clean
- Staged files: PASS, `0`

## Decision Target

`v1_ib_a_p_a_replayed_analyzer_semantic_completeness_fix_ready_for_counterpart_qa_review`
