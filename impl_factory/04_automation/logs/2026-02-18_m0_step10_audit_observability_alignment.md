# M0 Step 10 - Audit/Observability Alignment

Date: 2026-02-18  
Status: Completed

## Objective
Implement contract-aligned operational hardening for observability and safe error handling:
1. persist structured turn-level audit envelope for each actionable turn (contract section 14)
2. standardize user-safe error envelope behavior with internal trace logging
3. keep internal tool/debug messages hidden from normal user view

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/turn_audit.py` (new)
   - Added lightweight planner-output context bridge:
     - `set_last_planner_output()`
     - `pop_last_planner_output()`
     - `clear_last_planner_output()`
   - Planner payload is pruned/json-safe before storage.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added planner-output capture hook right after validated planner result:
     - `set_last_planner_output(plan, source="report_qa_start")`

3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/service.py`
   - Added deterministic turn-level audit envelope (`type: "audit_turn"`) persisted as hidden `role=tool` message per actionable turn.
   - Audit envelope includes:
     - intent classification
     - planner output (validated/pruned form when available)
     - tool invocation summary
     - response payload hash/meta
     - user-visible response snapshot
     - error envelope (if error)
   - Added standardized safe error handling:
     - `_safe_user_error_text()`
     - `_error_envelope()` persisted as hidden `role=tool` message (`type: "error_envelope"`)
   - Added internal trace logging with trace IDs on execution failures via `frappe.log_error(...)`.
   - Ensured stale planner context is cleared each turn before execution.

4. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_assistant_ui/page/ai_chat/ai_chat.js`
   - Updated renderer to support `type: "error"` assistant payloads so safe errors remain user-friendly.

5. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added Step 10 regression tests:
     - `test_handle_user_message_persists_audit_turn_with_planner_output`
     - `test_handle_user_message_failure_persists_error_envelope_and_safe_response`

## Verification Evidence
Executed in backend bench runtime:

1. Compile check:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'`
- Result: success

2. Step 10 focused tests:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract.ChatServiceAuditStep10Tests -v'`
- Result: `Ran 2 tests ... OK`

3. Full contract regression module:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'`
- Result: `Ran 28 tests ... OK`

## Notes
1. No ERPNext core files changed.
2. Internal audit/error envelopes are persisted as `role=tool` messages and remain hidden in normal user message retrieval.
3. No dead/unused file cleanup performed in this step.
