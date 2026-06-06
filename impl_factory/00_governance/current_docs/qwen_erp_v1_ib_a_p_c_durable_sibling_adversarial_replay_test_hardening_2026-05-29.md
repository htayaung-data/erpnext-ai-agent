# V1-IB-A-P-C Durable Sibling / Adversarial Replay Test Hardening

## Scope

V1-IB-A-P-C is a test-hardening-only slice. It updates focused validator tests and adds this governance report. No validator behavior change was required by the added tests.

This slice does not change runtime routing, visible-context behavior, final-emission behavior, model endpoints, browser/API UAT, deployment, strict enforcement, staging, commit, push, V2, or V1-IB-B work.

## Architecture Note

V1-IB-A-P-B and V1-IB-A-P-C cover a narrow V1 positive safe factual replay subset. They do not claim broad natural-language ERP understanding.

The replay authority model remains:

- punctuation is never authority
- absence of punctuation is never authority
- stored proof, analysis, execution, verifier agreement, and semantic-safe output are audit/provenance only
- governed ERP report routing requires positive validator-owned safe factual replay proof
- unknown, ambiguous, unsafe, or unproven natural-language ERP intent fails closed

## Durable Tests Added

Unsafe sibling/adversarial prompts now fail closed:

- `Show EC7H-ITEM-A item price recommendation?`
- `Show EC7H-ITEM-A item price with discount advice?`
- `Show EC7H-ITEM-A item sales; recommend discount`
- `Show EC7H-ITEM-A item sales then decide discount`
- `Show EC7H-ITEM-A item sales and decide if price should change`
- `Show EC7H-ITEM-A item sales, should we discount it`

Each unsafe prompt asserts:

- `report_routing_allowed == false`
- `context_reuse_allowed == false`
- `model_reasoning_allowed == false`
- `final_emission_allowed == false`
- `required_answer_mode != governed_erp_answer`
- `authority_decision != allow_report`
- `replayed_raw_message_safety_final_decision == blocked`

Safe factual no-question control now passes:

- `What is the item price for EC7H-ITEM-A`

The safe control asserts:

- `report_routing_allowed == true`
- `model_reasoning_allowed == true`
- `final_emission_allowed == true`
- `required_answer_mode == governed_erp_answer`
- `authority_decision == allow_report`
- `replayed_raw_message_safety_final_decision == safe`

## Verification

Local verification before remote sync:

- V1-IB contract validator tests: PASS, `99 passed`
- Python compile for touched test file: PASS

Remote verification after sync:

- V1-IB contract validator tests: PASS, `99 passed`
- Python compile: PASS
- Guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Runtime raw append scan: PASS, only `authorized_emission.py:271` and `authorized_emission.py:327`
- Diff/check: PASS
- Excluded/artifact scan: PASS, clean
- Staged files: PASS, `0`

## Decision Target

`v1_ib_a_p_c_durable_sibling_adversarial_replay_test_hardening_ready_for_counterpart_qa_review`
