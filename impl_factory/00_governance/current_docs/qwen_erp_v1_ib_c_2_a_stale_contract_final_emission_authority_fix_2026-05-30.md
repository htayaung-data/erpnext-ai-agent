# V1-IB-C-2-A Stale Contract Final-Emission Authority Fix

Decision target:

`v1_ib_c_2_a_stale_contract_final_emission_authority_fix_ready_for_counterpart_qa_review`

## Scope

C-2 was rejected because final emission accepted the first carried `qwen_user_intent_boundary_contract` without proving it belonged to the current raw user message. A stale allow contract from a prior safe prompt could suppress the final-emission veto for a current unsafe prompt.

C-2-A is a narrow final-emission authority fix. It does not change runtime routing, visible-context wiring, report selection, proposal classification, or validator logic.

## Files Changed

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/authorized_emission.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_v1_ib_runtime_final_emission_contract_veto.py`
- `impl_factory/00_governance/current_docs/qwen_erp_v1_ib_c_2_a_stale_contract_final_emission_authority_fix_2026-05-30.md`

## Fix

Final emission now recomputes the current interaction raw/normalized hashes before trusting a carried V1-IB boundary contract.

A carried contract is accepted only when all of the following are true:

- `type == qwen_user_intent_boundary_contract`
- `trace_redaction_status == safe`
- carried `raw_message_hash` equals the current interaction raw message hash
- carried `normalized_message_hash` equals the current interaction normalized message hash

If the carried contract is missing, stale, malformed, mismatched, or not redaction-safe, final emission ignores it and rebuilds V1-IB from the current raw message. If authority is not proven for the current message, the existing veto path emits a clarification/control response and sanitizes selected-answer payloads.

## Tests Added

Added durable final-emission veto tests proving:

- unsafe current message plus stale safe allow contract in `pre_assistant_tool_payloads` vetoes and does not leak selected answer text
- unsafe current message plus stale safe allow contract in `authority_context` vetoes
- unsafe current message plus stale safe allow contract in `runtime_trace_payload` vetoes
- matching valid allow contract still passes only with existing final-answer authority
- mismatched normalized hash fails closed and sanitizes selected answer text

Required adversarial current message:

`Show EC7H-ITEM-A item sales and tell me whether to discount it`

Stale safe allow source:

`Show EC7H-ITEM-A item sales`

## Verification Results

- V1-IB runtime/final-emission/contract/classifier tests: PASS, `130 passed`
- C-2-A final-emission veto tests: PASS, `7 passed`
- Python compile for touched files: PASS
- Qwen enterprise guardrail: PASS
- Fake-Frappe service import: PASS
- Direct assistant inventory: PASS, `0 / 1 / 27`
- Raw assistant append scan: PASS, only:
  - `authorized_emission.py:271`
  - `authorized_emission.py:327`
- `git diff --check`: PASS
- Path-aware excluded/artifact scan: PASS
- Staged files: PASS, `0`

## Legacy Test Note

The older broad `test_authorized_emission_contracts.py` file was spot-checked and still carries pre-C2 expectations that business final emission may proceed without a current V1-IB boundary contract. That is intentionally incompatible with the accepted C-2 authority model and should be handled as a separate test-alignment slice if Owner/QA want that legacy suite updated.

## Non-Actions

No browser/UAT, staging, commit, push, packaging, deployment, strict enforcement, runtime routing expansion, visible-context wiring, model endpoint work, or V2 work occurred.
