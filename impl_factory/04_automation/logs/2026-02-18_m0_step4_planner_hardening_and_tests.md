# M0 Step 4 - Planner Hardening + Clarify Flow + Regression Tests

Date: 2026-02-18  
Status: Completed

## Objective
Strengthen commercial behavior for diverse user questions by hardening planner validation/fallback, honoring planner clarifications explicitly, and removing topic-specific tool routing.

## Changes Applied
1. Planner hardening in `ai_core/llm/report_planner.py`:
   - Added action-specific schema normalization/validation for:
     - `run_report`
     - `clarify`
     - `transform_last`
     - `write_draft`
   - Added safe fallback plan:
     - always returns a single-question `clarify` plan when LLM output is invalid or parsing fails.
   - Kept export handling strict (`export` normalized to boolean).

2. Few-shot library externalization:
   - Added `ai_core/llm/few_shot_examples.py`.
   - Moved planner examples into reusable list `REPORT_PLANNER_FEW_SHOTS`.
   - Expanded coverage across Finance, Sales, Stock, HR, and Operations style prompts.

3. Clarify action handling in `ai_core/tools/report_qa.py`:
   - Added explicit `action == "clarify"` path.
   - Returns exactly one clarification question and stores pending state:
     - `mode = planner_clarify`
     - `base_question`
     - `filters_so_far`
     - `export_requested`
   - Added continuation logic for `planner_clarify` in `report_qa_continue`:
     - merges user clarification with base question
     - re-enters `report_qa_start` safely.

4. Generic tooling enforcement in `ai_core/tools/registry.py`:
   - Removed topic-specific tool registration:
     - deleted `top_customers_last_month` from active tool map.
   - Active runtime tools are now generic report-QA start/continue only.

5. Added regression tests:
   - `ai_assistant_ui/tests/test_planner_contract.py`
   - Validates:
     - invalid planner outputs fallback to safe clarify plan
     - run_report plan normalization
     - report_qa honors planner clarify question
     - planner clarify pending flow re-enters start path correctly.

## Verification Evidence
1. Compile + tests in backend bench environment:
   - `./env/bin/python -m compileall -q apps/ai_assistant_ui/ai_assistant_ui`
   - `./env/bin/python -m unittest apps.ai_assistant_ui.ai_assistant_ui.tests.test_planner_contract -v`
   - Result: 4 tests passed.

2. Live API smoke:
   - Created session via `ai_assistant_ui.api.create_session`
   - Sent chat via `ai_assistant_ui.api.chat_send`
   - Retrieved debug messages via `ai_assistant_ui.api.get_messages`
   - Deleted session via `ai_assistant_ui.api.delete_session`
   - Result: `chat_send` returned `{"ok": true}` and report output was produced.

## Notes
1. This step focuses on planner safety + clarification behavior + regression coverage.
2. Dead-file cleanup (`.bak.*`) remains intentionally deferred to the next controlled cleanup step with dependency checks.
