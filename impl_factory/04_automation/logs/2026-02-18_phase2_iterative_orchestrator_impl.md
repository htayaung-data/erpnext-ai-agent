# Phase 2 Implementation Note (Iterative Read Orchestrator)

Date: 2026-02-18
Status: Implemented in custom app source
Scope: Feature-flagged iterative orchestration for READ path + deterministic quality alignment fallback

## Contract / Roadmap Alignment
1. Bounded iterative loop for read orchestration (max 5 steps).
2. Repeated identical tool-call guard in one turn.
3. Write confirmation state machine unchanged.
4. Feature-flag path with fallback to current flow when disabled.
5. Concrete clarification fallback replaces abstract planner-preference prompts.

## Code Changes
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added feature flag helpers:
     - `_read_orchestrator_v2_enabled`
     - `_read_orchestrator_max_steps`
   - Added iterative loop helpers:
     - `_run_iterative_read_orchestrator`
     - `_run_report_call_signature`
     - `_quality_clarification_payload`
     - `_planner_observation_text`
   - Wired iterative path in:
     - `report_qa_start` run_report branch.
     - `report_qa_continue` `need_filters` branch.
   - Preserved write flow (`write_confirmation`) behavior.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/result_quality.py`
   - Added deterministic metric semantic fallback for single numeric-column cases.
   - Added quantity-vs-value and directional conflict guards to avoid unsafe false matches.
   - Updated minimal-columns check to accept validated metric fallback mapping.
   - Exposed `metric_column_fallback` in gate context.

3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added quality-gate fallback test for revenue/value alignment.
   - Added iterative Phase 2 tests:
     - retry-until-pass path.
     - repeated-call guard with actionable clarification.

## Validation
1. Host syntax checks:
   - `python3 -m compileall -q .../report_qa.py .../result_quality.py`
   - `python3 -m compileall -q .../test_planner_contract.py`
   - Result: PASS

2. Container targeted checks (runtime behavior):
   - New targeted tests for quality fallback and iterative guard executed.
   - Direct mocked smoke confirmed:
     - `Top 5 customers by revenue last month` path returns `report_table` when report returns `Customer + Value` columns under iterative mode.

## Notes
1. Bench container test file path may not yet reflect workspace test edits in all environments; runtime behavior was additionally validated via direct mocked execution in-container.
2. Feature flag names supported:
   - `ai_assistant_orchestrator_v2_enabled`
   - `ai_assistant_iterative_read_enabled`
   - `ai_assistant_read_orchestrator_v2`
3. Max-step config names supported (capped at 5):
   - `ai_assistant_orchestrator_v2_max_steps`
   - `ai_assistant_iterative_read_max_steps`
   - `ai_assistant_read_orchestrator_max_steps`
