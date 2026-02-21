# M0 Step 13 Hotfix - Planner Clarification Loop Guard

Date: 2026-02-18  
Status: Completed

## Objective
Fix repeated clarification loop where user replies like `yes` and assistant repeats the same question without progressing.

## Root Cause
`report_qa_continue(mode="planner_clarify")` forwarded any reply text back to planner, including low-information acknowledgements (`yes`, `ok`, `I said yes`), with no deterministic validation of whether the clarification was actually answered.

## Changes Applied
1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/report_qa.py`
   - Added deterministic clarification helpers:
     - `_normalize_clarification_options(...)`
     - `_is_low_information_clarification_reply(...)`
   - Extended planner clarify pending state to carry:
     - `clarification_question`
     - `clarification_options` (when available)
   - Updated `report_qa_continue(mode="planner_clarify")`:
     - if options exist, enforce option selection
     - if no options and reply is low-information, request a specific answer
     - when valid clarification is provided, include structured context in restart prompt:
       - `Clarification question: ...`
       - `User clarification answer: ...`
   - For internal quality-gate fallback prompt (`metric/grouping`), set deterministic options so `yes` is no longer accepted as a complete answer.

2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/tests/test_planner_contract.py`
   - Added regressions:
     - `test_report_qa_continue_planner_clarify_blocks_low_information_reply`
     - `test_report_qa_continue_planner_clarify_accepts_option_choice`
     - `test_report_qa_continue_planner_clarify_yes_no_option_allows_yes`

## Verification Evidence
1. Clarify test group:
- `docker compose exec backend bash -lc "cd /home/frappe/frappe-bench && ./env/bin/python -m unittest ai_assistant_ui.tests.test_planner_contract.ReportQaClarifyTests"`
- Result: `Ran 5 tests ... OK`

2. Full regression module:
- `docker compose exec backend bash -lc "cd /home/frappe/frappe-bench && ./env/bin/python -m unittest ai_assistant_ui.tests.test_planner_contract"`
- Result: `Ran 41 tests ... OK`

3. Runtime reload:
- `docker compose restart backend queue-short queue-long scheduler websocket`
- Result: services restarted healthy.

4. Live smoke (reported pattern):
- Session flow:
  - User: `Top 5 Customers by Revenue Last Month`
  - Assistant asks clarification with options.
  - User: `yes`
  - Assistant now responds with deterministic option prompt:
    - `Please choose one option: 1) metric; 2) grouping. ...`
  - No blind repeat-loop on `yes`.

## Notes
1. This hotfix removes the unproductive `yes -> same question` loop.
2. A separate semantic quality issue remains for this business request (metric mapping/report selection quality), which needs the next hardening step.
