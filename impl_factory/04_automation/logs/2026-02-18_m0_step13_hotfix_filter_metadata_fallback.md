# M0 Step 13 Hotfix - Empty FAC Filter Metadata Fallback

Date: 2026-02-18  
Status: Completed

## Objective
Fix false clarification failures reported in live chat:
1. `Top 5 Customers by Revenue Last Month` returned "report does not support date range"
2. `Total Payable Amount as of Today` returned "report does not support date"

## Root Cause
For some FAC reports, `get_report_requirements(...).filters_definition` is empty.
The previous constraint validator treated empty metadata as "unsupported", which triggered false hard-block clarifications.

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - `_validate_hard_constraints(...)`
     - Added filter-schema guard: unsupported constraint hard-block is applied only when filter schema is known.
   - `_apply_timeframe_defaults(...)`
     - Added metadata-empty fallback behavior:
       - date range intent -> default `from_date` + `to_date`
       - as-of date intent -> default `report_date` (fallback order includes `as_on_date`, `to_date`, `posting_date`)
     - Keeps existing warning behavior only when schema exists and explicitly lacks date-range support.
   - `_execute_run_report_plan(...)`
     - Normalizes planner `date_range` object before sanitize/validation (`date_range -> from_date/to_date`).
   - `report_qa_continue(mode="need_filters")`
     - Added the same filter normalization before sanitize/coerce.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added regressions:
     - `test_report_qa_start_allows_date_range_when_filter_metadata_missing`
     - `test_report_qa_start_normalizes_date_range_object_when_filter_metadata_missing`
     - `test_report_qa_start_allows_as_of_date_when_filter_metadata_missing`

## Verification Evidence
Executed in backend bench runtime:

1. Targeted new tests:
- `docker compose exec backend bash -lc "cd /home/frappe/frappe-bench && ./env/bin/python -m unittest ai_assistant_ui.tests.test_planner_contract.ReportQaConstraintAndEntityTests.test_report_qa_start_allows_date_range_when_filter_metadata_missing ai_assistant_ui.tests.test_planner_contract.ReportQaConstraintAndEntityTests.test_report_qa_start_normalizes_date_range_object_when_filter_metadata_missing ai_assistant_ui.tests.test_planner_contract.ReportQaConstraintAndEntityTests.test_report_qa_start_allows_as_of_date_when_filter_metadata_missing"`
- Result: `Ran 3 tests ... OK`

2. Full regression module:
- `docker compose exec backend bash -lc "cd /home/frappe/frappe-bench && ./env/bin/python -m unittest ai_assistant_ui.tests.test_planner_contract"`
- Result: `Ran 38 tests ... OK`

3. Compile check:
- `docker compose exec backend bash -lc "python -m compileall -q /home/frappe/frappe-bench/apps/ai_assistant_ui/ai_assistant_ui"`
- Result: success

4. Live smoke replay (user prompts):
- Prompt: `Top 5 Customers by Revenue Last Month`
  - No longer returns "can’t apply date range constraint".
  - Flow now reaches semantic quality gate clarification (separate behavior area).
  - Pending state includes normalized date filters (`from_date`, `to_date`).
- Prompt: `Total Payable Amount as of Today`
  - No longer returns "can’t apply date constraint".
  - Flow now reaches semantic quality gate clarification (separate behavior area).

## Notes
1. This hotfix removes false "unsupported date/date-range" blocks when FAC metadata is missing.
2. Remaining clarification behavior is now driven by semantic quality checks, not constraint-support misclassification.
3. No ERPNext core files changed.
