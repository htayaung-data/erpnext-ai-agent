# M0 Step 8 - Context Window + Follow-up Memory Hardening

Date: 2026-02-18  
Status: Completed

## Objective
Improve ChatGPT-like conversation quality while preserving contract safety:
1. enforce practical 3-5 turn memory window for planner context
2. improve follow-up behavior for context references such as "same period" / "same warehouse" / "same company"
3. keep deterministic validation-first behavior and one-question discipline
4. add regression tests and verification evidence

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Context manager improvements:
     - `_get_recent_user_assistant()` now captures up to 5 turns (10 user/assistant messages)
     - assistant JSON payloads are summarized for planner context using `_assistant_context_text()` instead of passing bulky raw payload JSON
   - Added deterministic follow-up context reuse:
     - `_detect_followup_context()`
     - `_apply_followup_filter_context()`
     - supports carry-over from last result filters for same-period/company/warehouse/same-filters phrasing
   - Integrated follow-up context reuse into report execution path before constraint validation and FAC run.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/llm/report_planner.py`
   - Increased planner and pending-mode recent context payload from 5 messages to 10 messages (aligned with 3-5 turn target).

3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/llm/few_shot_examples.py`
   - Added follow-up few-shot sample for same-period phrasing.

4. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added Step 8 regression tests:
     - context window returns last five turns and summarized assistant report context
     - same-period follow-up reuses prior date range filters
     - same-warehouse follow-up reuses prior warehouse filter

## Verification Evidence
Executed in backend bench runtime:

1. Compile check:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'`
- Result: success

2. Regression tests:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'`
- Result: `Ran 22 tests ... OK`

## Notes
1. No ERPNext core files changed.
2. No dead-file cleanup performed in this step.
3. Behavior remains FAC-truth aligned; this step only hardens context handling and follow-up memory use.
