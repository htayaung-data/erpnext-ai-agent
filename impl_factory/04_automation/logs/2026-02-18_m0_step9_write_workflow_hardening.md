# M0 Step 9 - Write Workflow Hardening

Date: 2026-02-18  
Status: Completed

## Objective
Harden write workflow behavior after Step 8 by improving:
1. negative-path robustness around write confirmation and capability gating
2. permission-safe handling at execution time
3. confirmation clarity for non-create write operations (`update/delete/submit/cancel`)

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added deterministic payload preview helpers for write confirmations:
     - `_value_preview()`
     - `_update_changes_preview()`
   - Hardened write draft normalization:
     - `update` now requires at least one field change in payload (besides `name/docname/id`), otherwise asks one clarification question.
   - Improved write confirmation text generation:
     - `update`: includes target record and field-change preview
     - `delete`: explicit permanent delete wording
     - `submit`: explicit submit action wording
     - `cancel`: explicit cancel action wording
   - Added permission-aware execution fallback:
     - `_looks_like_permission_error()`
     - permission-like execution errors now return a user-safe permission message with target context.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added Step 9 regression tests for write workflow hardening:
     - update draft with no changed fields triggers clarify (negative path)
     - confirmation execution blocked when write capability gate is disabled
     - permission-like execution failure returns safe permission message
     - non-create confirmation text includes clear operation-specific summaries

## Verification Evidence
Executed in backend bench runtime:

1. Compile check:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'`
- Result: success

2. Regression tests:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'`
- Result: `Ran 26 tests ... OK`

## Notes
1. No ERPNext core files changed.
2. Write capability remains disabled by default unless explicitly enabled via site config.
3. Step 9 focused on write safety/clarity hardening and regression coverage.
