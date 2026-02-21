# M0 Step 7 - Write Draft + Confirmation State Machine

Date: 2026-02-18  
Status: Completed

## Objective
Implement safe write lifecycle behavior in active chat orchestration:
1. planner `write_draft` creates a confirmation gate (no immediate execution)
2. execution requires explicit user confirmation
3. write capability remains disabled by default behind deterministic gate
4. topic switch should cancel pending write confirmation
5. add regression tests and verification evidence

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added deterministic write capability gate:
     - `_write_capability_enabled()` (defaults to disabled unless site config enables)
   - Added write draft normalization and validation:
     - `_normalize_write_draft()`
     - one-question clarify path for missing required write fields
   - Added explicit write confirmation flow:
     - `action == write_draft` now returns confirmation prompt + pending state `mode=write_confirmation`
     - execution blocked unless user replies explicitly with confirm/cancel
   - Added deterministic write execution adapter:
     - `_execute_write_draft()` for create/update/delete/submit/cancel
     - `_cancel_document()` for cancel operation
   - Added safe user-facing success/cancel/error text and hidden write result tool message.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/service.py`
   - Added deterministic pending routing for `write_confirmation`:
     - only explicit confirm/cancel-like replies continue pending
     - otherwise message starts a new topic and clears pending flow (topic-switch safety)

3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added Step 7 regression tests for:
     - write_draft disabled behavior
     - write_draft pending confirmation behavior
     - explicit confirm requirement (non-explicit stays pending)
     - explicit cancel clears pending
     - explicit confirm executes draft path

## Verification Evidence
Executed in backend bench runtime:

1. Compile check:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'`
- Result: success

2. Regression tests:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'`
- Result: `Ran 19 tests ... OK`

## Notes
1. No ERPNext core files changed.
2. Write actions are still capability-gated and disabled by default unless explicitly enabled in site config.
3. No dead-file cleanup performed in this step.
