# M0 Step 12 - Semantic Request Spec + Result Quality Gate

Date: 2026-02-18  
Status: Completed

## Objective
Implement generalized, industry-style answer-quality control without keyword/specific-question hardcoding:
1. normalize user request into validated semantic `business_request_spec`
2. deterministically validate FAC result quality against requested semantics
3. apply bounded repair (`local deterministic repair` -> `single re-plan/re-run`) before user response
4. persist spec + quality verdict in turn audit envelope

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/llm/report_planner.py`
   - Added `choose_business_request_spec(...)` with deterministic schema validation.
   - Added safe fallback spec generation when LLM output is invalid/unavailable.
   - Added strict normalization for:
     - intent/task/output mode
     - metric/grouping/top_n/time scope
     - clarification requirement and question

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/result_quality.py` (new)
   - Added deterministic post-FAC quality validator:
     - hard-filter/time-scope checks
     - metric/dimension alignment checks
     - top-N integrity checks
     - KPI/ranking output-shape checks
   - Added deterministic local repair helper:
     - top-N sort/limit repair
     - KPI total projection
     - minimal-column projection
   - Added machine-readable feedback formatter for bounded re-plan retry.

3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/chat/turn_audit.py`
   - Extended turn context bridge to include:
     - `business_request_spec`
     - `result_quality_gate`
     - `plan_history` (last planner decisions in-turn)
   - Added:
     - `set_last_business_request_spec(...)`
     - `set_last_result_quality_gate(...)`

4. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added semantic-spec capture in `report_qa_start`.
   - Added early single-question clarify when semantic spec is ambiguous.
   - Refactored run-report execution into `_execute_run_report_plan(...)`.
   - Added post-FAC quality-gate flow:
     - initial deterministic quality validation
     - deterministic local repair attempt
     - single planner re-plan + FAC re-run attempt
     - final one-question clarification fallback when still mismatched
   - Added audit capture of quality verdict and decision path.

5. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added semantic spec validation test.
   - Added direct quality-gate mismatch test.
   - Added local top-N repair regression test.
   - Added bounded retry regression test.
   - Extended audit test to assert persisted `business_request_spec` and `result_quality_gate`.

## Verification Evidence
Executed in backend bench runtime:

1. Compile check:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui'`
- Result: success

2. Full contract regression module:
- `docker compose exec backend bash -lc 'cd /home/frappe/frappe-bench && ./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v'`
- Result: `Ran 32 tests ... OK`

## Notes
1. No ERPNext core files changed.
2. No dead/unused file deletion performed in this step.
3. Flow remains FAC-truth-only; this step adds semantic normalization and deterministic quality control on top.
