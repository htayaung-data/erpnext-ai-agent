# M0 Step 6 - Transform Engine Completion (`sort/filter/summary`)

Date: 2026-02-18  
Status: Completed

## Objective
Complete the next AI-behavior vertical slice by extending deterministic transform behavior:
1. add `sort`, `filter`, `summary` transform operations on last FAC result
2. support same-turn `post_transform` execution for these ops when planner requests it
3. keep one-question clarification behavior for missing transform inputs
4. add regression tests and evidence

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added deterministic transform helpers:
     - `_transform_sort()`
     - `_transform_filter()`
     - `_transform_summary()`
     - plus operator/direction normalization and row-match utilities
   - Extended `action == transform_last` handling to execute:
     - `sort`
     - `filter`
     - `summary`
   - Enforced one-question follow-up for filter when required inputs are missing:
     - asks column if unknown
     - asks filter value if missing
     - stores pending state in `transform_pending`
   - Extended one-turn `post_transform` after `run_report` to support:
     - `sort`
     - `filter` (when value provided)
     - `summary`
   - Extended `transform_pending` continuation path to support:
     - `sort`
     - `filter` (column then value, one question at a time)
     - `summary`

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/llm/report_planner.py`
   - Expanded validated planner operations for both `transform_last` and `post_transform`:
     - now includes `sort`, `filter`, `summary`
   - Updated planner instruction text to include these allowed operations.

3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/llm/few_shot_examples.py`
   - Added few-shot guidance examples for:
     - sort transform
     - filter transform
     - summary transform

4. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added Step 6 regression coverage:
     - planner accepts validated `transform_last: sort`
     - deterministic sort helper behavior
     - deterministic filter helper behavior
     - deterministic summary helper behavior
     - same-turn post-transform sort application

## Verification Evidence
Executed in backend bench runtime:

1. Compile check:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'`
- Result: success

2. Regression tests:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'`
- Result: `Ran 14 tests ... OK`

## Notes
1. No ERPNext core files changed.
2. Export behavior remains explicit-request only.
3. Step focuses on deterministic transform capability and follow-up behavior; no dead-file cleanup performed.
