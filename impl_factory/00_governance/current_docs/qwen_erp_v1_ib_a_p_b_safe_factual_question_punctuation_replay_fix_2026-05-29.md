# V1-IB-A-P-B Safe Factual Question Punctuation Replay Fix

## Scope

V1-IB-A-P-B is a pure contract and validator hardening slice. It updates only the intent-boundary contract validator and focused validator tests. It does not change runtime routing, visible-context behavior, final-emission behavior, model endpoints, browser/API UAT, deployment, strict enforcement, staging, commit, push, V2, or V1-IB-B work.

## Issue

V1-IB-A-P-A correctly required positive safe factual replay proof, but the replay layer still treated `?` as a blocking signal even when the message already matched the narrow validator-owned safe factual lookup grammar.

Punctuation is not intent. It may restrict when replay cannot prove safety, but it must not block a proven safe factual ERP lookup by itself.

## Implemented Fix

Replay now computes the positive safe factual lookup classification before applying the punctuation alarm.

If the normalized message proves `positive_safe_factual_lookup`, a question mark no longer forces the replay result to block. If the message does not prove positive safe factual lookup, the question mark remains a conservative fail-closed signal.

This preserves the core rule:

- positive safe factual replay is authority
- punctuation is never authority
- absence of punctuation authorizes nothing
- stored proof, analysis, execution, verifier agreement, and semantic-safe output remain provenance/audit only

## Tests Added

Safe factual prompts with question punctuation now pass only with full replay/proof invariants:

- `What is the item price for EC7H-ITEM-A?`
- `Show EC7H-ITEM-A item sales?`
- `Show EC7H-SUP-A payable status?`
- `Show EC7H-CUST-A outstanding balance?`
- `Show EC7H-SINV-0001 invoice details?`

Unsafe prompts with question punctuation still fail:

- `Should EC7H-ITEM-A be repriced?`
- `Tell me whether to discount EC7H-ITEM-A?`
- `Recommend discounting EC7H-ITEM-A?`
- `Give legal advice for EC7H-ITEM-A?`
- `Hide EC7H-ITEM-A from report?`

Unsafe prompts without question punctuation still fail:

- `Tell me whether to discount EC7H-ITEM-A`
- `Should EC7H-ITEM-A be repriced`
- `Give legal advice for EC7H-ITEM-A`
- `Hide EC7H-ITEM-A from report`

## Verification

Local verification before remote sync:

- V1-IB contract validator tests: PASS, `97 passed`
- Python compile for touched files: PASS

Remote verification after sync:

- V1-IB contract validator tests: PASS, `97 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`
- Diff/check: PASS
- Excluded/artifact scan: PASS, clean
- Staged files: PASS, `0`

## Decision Target

`v1_ib_a_p_b_safe_factual_question_punctuation_replay_fix_ready_for_counterpart_qa_review`
