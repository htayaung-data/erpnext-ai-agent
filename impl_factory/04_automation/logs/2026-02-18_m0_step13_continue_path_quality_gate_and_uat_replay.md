# M0 Step 13 - Continue-Path Quality Gate + Focused UAT Replay

Date: 2026-02-18  
Status: Completed

## Objective
Extend semantic quality enforcement to pending clarification continuation flow and replay user-reported mismatch patterns:
1. enforce deterministic quality gate in `need_filters` continuation path
2. preserve semantic context (`base_question`, `business_spec`) across pending turns
3. run focused replay tests for:
   - products vs customers dimension mismatch
   - sold qty vs received qty metric mismatch

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added `_merge_pending_state_context(...)` to persist pending semantic context.
   - Updated `_execute_run_report_plan(...)` to accept `pending_context` and carry context into pending states.
   - Added `business_spec` propagation in planner-clarify pending states from `report_qa_start`.
   - Hardened `report_qa_continue(mode="need_filters")` with full quality workflow:
     - initial deterministic quality gate
     - deterministic local repair
     - single bounded planner re-plan/re-run
     - one clarification fallback if still semantically mismatched
   - Persisted continue-path quality gate and semantic spec via audit context bridge.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/result_quality.py`
   - Tightened metric-column alignment threshold to reduce false-positive matches (for example sold vs received).
   - Added safe int coercion helper for robust `top_n` handling.

3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added metric mismatch replay test: sold qty vs received qty.
   - Added continue-path local repair replay test.
   - Added continue-path bounded retry replay test.

## Verification Evidence
Executed in backend bench runtime:

1. Compile check:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'`
- Result: success

2. Full regression module:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'`
- Result: `Ran 35 tests ... OK`

3. Focused UAT replay set (reported mismatch patterns):
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract.ResultQualityGateTests.test_quality_gate_flags_dimension_metric_mismatch apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract.ResultQualityGateTests.test_quality_gate_flags_sold_vs_received_metric_mismatch apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract.ReportQaTransformStep6Tests.test_report_qa_start_quality_gate_retries_once_with_replan apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract.ReportQaTransformStep6Tests.test_report_qa_continue_need_filters_quality_gate_retries_once_with_replan -v'`
- Result: `Ran 4 tests ... OK`

## Notes
1. No ERPNext core files changed.
2. No dead/unused file cleanup performed in this step.
3. This step specifically closes quality-gate parity between `report_qa_start` and `report_qa_continue`.
